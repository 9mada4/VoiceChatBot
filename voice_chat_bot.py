#!/usr/bin/env python3
"""
VoiceChatBot - Simple Voice-Controlled ChatGPT Automation for macOS
シンプル版：最小限のワークフローで音声制御
"""

import time
import subprocess
import logging
import tempfile
import os
import threading
from typing import Optional
import glob
from datetime import datetime

# 音声認識用のインポート
try:
    from faster_whisper import WhisperModel
    VOICE_RECOGNITION_AVAILABLE = True
except ImportError:
    VOICE_RECOGNITION_AVAILABLE = False
    print("Warning: Voice recognition not available")

# macOS用のインポート
try:
    from Quartz.CoreGraphics import CGEventCreateKeyboardEvent, CGEventPost, kCGHIDEventTap
    from Quartz.CoreGraphics import CGEventTapCreate, kCGHeadInsertEventTap, kCGEventTapOptionDefault
    from Quartz.CoreGraphics import CGEventMaskBit, kCGEventKeyDown, CGEventGetIntegerValueField, kCGKeyboardEventKeycode
    import Quartz
    QUARTZ_AVAILABLE = True
except ImportError:
    QUARTZ_AVAILABLE = False
    print("Warning: Quartz not available")

# Vision Framework用のインポート
try:
    import Vision
    from Foundation import NSURL, NSData, NSString
    from Cocoa import NSImage
    VISION_AVAILABLE = True
except ImportError:
    try:
        # PyObjCライブラリが不完全な場合のフォールバック
        from Cocoa import NSString
        from Foundation import NSURL, NSData
        VISION_AVAILABLE = False
        print("Warning: Vision framework not fully available, using fallback OCR")
    except ImportError:
        VISION_AVAILABLE = False
        print("Warning: Vision framework and Foundation not available")

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceBot:
    """シンプル音声ボット"""
    
    def __init__(self):
        self.whisper_model = None
        self.background_thread = None
        self.stop_monitoring = False
        self.keyboard_monitoring = False
        self.screenshot_waiting = False
        if VOICE_RECOGNITION_AVAILABLE:
            try:
                self.whisper_model = WhisperModel("tiny", device="cpu")
                logger.info("Whisper model loaded")
            except Exception as e:
                logger.error(f"Failed to load Whisper: {e}")
    
    def speak_text(self, text: str) -> None:
        """テキストを読み上げ"""
        try:
            print(f"🔊 読み上げ: {text}")
            subprocess.run(['say', text], timeout=30, check=False)
            print("✅ 読み上げ完了")
        except Exception as e:
            logger.error(f"Speech failed: {e}")
            print(f"📝 メッセージ: {text}")
    
    def record_audio_macos(self, duration: int = 4) -> Optional[str]:
        """macOSで音声録音（要件1: 4秒に変更）"""
        try:
            temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            temp_file.close()
            
            print(f"🎤 音声録音中... ({duration}秒)")
            print("「はい」または「終わり」と話してください")
            
            cmd = ['rec', temp_file.name, 'trim', '0', str(duration)]
            
            try:
                subprocess.run(cmd, check=True, capture_output=True)
                print("✅ 録音完了")
                return temp_file.name
            except subprocess.CalledProcessError:
                print("❌ 録音機能が利用できません")
                return None
                
        except Exception as e:
            logger.error(f"Recording failed: {e}")
            return None
    
    def transcribe_audio(self, audio_file: str) -> Optional[str]:
        """音声をテキストに変換"""
        try:
            if not self.whisper_model or not audio_file:
                return None
            
            segments, _ = self.whisper_model.transcribe(audio_file, language="ja")
            text = " ".join([segment.text for segment in segments])
            
            # 一時ファイル削除
            os.unlink(audio_file)
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None
    
    def get_voice_response(self, duration: int = 4) -> bool:
        """音声入力②で「はい」「いいえ」を取得"""
        audio_file = self.record_audio_macos(duration)
        if not audio_file:
            return False
        
        text = self.transcribe_audio(audio_file)
        if not text:
            print("❌ 音声認識に失敗しました")
            return False
        
        print(f"音声認識結果: '{text}'")
        
        # 「はい」系の判定
        yes_commands = ['はい', 'hai', 'yes', 'うん', 'そうです', 'オッケー', 'ok']
        
        # 終了コマンドの検出（ひらがな・漢字・カタカナ対応）
        end_commands = [
            '終わり', 'おわり', 'オワリ', 'OWARI', 'おわりー', 'オワリー',
            'しゅうりょう', 'シュウリョウ', 'SHUURYOU', 'しゅーりょー', 'シューリョー',
            'end', 'finish', 'stop', 'やめ', 'ヤメ',
            'キャンセル', 'cancel', 'ストップ', '中止', 'ちゅうし', 'チュウシ'
        ]
        
        text_lower = text.lower()
        
        # 終了判定を優先
        if any(end_word in text_lower for end_word in end_commands):
            print(f"判定結果: 終わり")
            return False
        
        result = any(yes_word in text_lower for yes_word in yes_commands)
        print(f"判定結果: {'はい' if result else '終わり'}")
        
        return result
    
    def press_key_quartz(self, keycode: int) -> bool:
        """Quartzでキーを送信"""
        if not QUARTZ_AVAILABLE:
            return False
        
        try:
            # Key down
            event = CGEventCreateKeyboardEvent(None, keycode, True)
            CGEventPost(kCGHIDEventTap, event)
            time.sleep(0.05)
            
            # Key up
            event = CGEventCreateKeyboardEvent(None, keycode, False)
            CGEventPost(kCGHIDEventTap, event)
            
            return True
        except Exception as e:
            logger.error(f"Key press failed: {e}")
            return False
    
    def start_dictation(self) -> bool:
        """要件2: 右コマンド2回で音声入力①を開始"""
        if not QUARTZ_AVAILABLE:
            print("💡 手動で音声入力を開始してください：右コマンドキーを2回押す")
            return False
        
        try:
            RIGHT_COMMAND_KEY = 54
            
            print("🎤 音声入力①を開始しています...")
            
            # 1回目
            if not self.press_key_quartz(RIGHT_COMMAND_KEY):
                return False
            time.sleep(0.1)
            
            # 2回目
            if not self.press_key_quartz(RIGHT_COMMAND_KEY):
                return False
            
            print("✅ 音声入力①が開始されました")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start dictation: {e}")
            return False
    
    def stop_dictation(self) -> bool:
        """Escapeキーで音声入力①を停止"""
        if not QUARTZ_AVAILABLE:
            print("💡 手動でEscapeキーを押して音声入力を停止してください")
            return False
        
        try:
            ESCAPE_KEY = 53
            print("🛑 音声入力①を停止しています...")
            
            if not self.press_key_quartz(ESCAPE_KEY):
                return False
            
            print("✅ 音声入力①が停止されました")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop dictation: {e}")
            return False
    
    def background_voice_monitor(self):
        """要件4: バックグラウンドで音声入力②を監視"""
        print("🎧 バックグラウンド音声監視を開始...")
        
        while not self.stop_monitoring:
            try:
                # 音声録音（短い間隔で監視）
                audio_file = self.record_audio_macos(duration=5)
                if audio_file:
                    text = self.transcribe_audio(audio_file)
                    if text:
                        print(f"🎧 監視中の音声: '{text}'")
                        
                        # 「音声入力終了」を検知
                        if '音声入力終わり' in text or '終わり' in text:
                            print("🎯 音声入力終わりを検知！")
                            self.stop_monitoring = True
                            self.stop_dictation()
                            break
                
                time.sleep(1)  # 短い間隔で再チェック
                
            except Exception as e:
                logger.error(f"Background monitoring error: {e}")
                break
        
        print("🛑 バックグラウンド音声監視を終了")
    
    def press_enter(self) -> bool:
        """Enterキーを押す（sample.py参考）"""
        if not QUARTZ_AVAILABLE:
            print("💡 手動でEnterキーを押してください")
            return False
        
        try:
            ENTER_KEY = 36  # Return / Enter（メインキー）
            
            # keyDown
            CGEventPost(
                kCGHIDEventTap,
                CGEventCreateKeyboardEvent(None, ENTER_KEY, True)
            )
            time.sleep(0.05)  # 押しっぱなし時間
            
            # keyUp
            CGEventPost(
                kCGHIDEventTap,
                CGEventCreateKeyboardEvent(None, ENTER_KEY, False)
            )
            
            print("✅ Enterキーを送信しました")
            return True
            
        except Exception as e:
            logger.error(f"Failed to press enter: {e}")
            return False
    
    def send_with_cmd_enter(self) -> bool:
        """要件7: Cmd+Enterで送信"""
        if not QUARTZ_AVAILABLE:
            print("💡 手動でCmd+Enterを押してください")
            return False
        
        try:
            CMD_KEY = 55     # Left Command
            ENTER_KEY = 36   # Enter
            
            print("📤 Cmd+Enterで送信中...")
            
            # Cmd+Enter
            event = CGEventCreateKeyboardEvent(None, CMD_KEY, True)
            CGEventPost(kCGHIDEventTap, event)
            event = CGEventCreateKeyboardEvent(None, ENTER_KEY, True)
            CGEventPost(kCGHIDEventTap, event)
            event = CGEventCreateKeyboardEvent(None, ENTER_KEY, False)
            CGEventPost(kCGHIDEventTap, event)
            event = CGEventCreateKeyboardEvent(None, CMD_KEY, False)
            CGEventPost(kCGHIDEventTap, event)
            
            print("✅ 送信完了")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send with Cmd+Enter: {e}")
            return False
    
    def handle_post_send_screenshot(self) -> bool:
        """送信後の確認処理（簡略化版）"""
        try:
            print("\n【ステップ8】ChatGPT出力確認")
            
            # 音声で確認を待機
            if self.wait_for_voice_confirmation("ChatGPTの出力が終了したら「はい」と答えてください"):
                print("✅ 「はい」を検知 - 処理完了しました")
                return True
            else:
                print("❌ 音声確認がキャンセルされました")
                return False
            
        except Exception as e:
            logger.error(f"Post-send confirmation error: {e}")
            print("❌ 確認処理中にエラーが発生しました")
            return False
    
    def run_requirements_1_to_3(self):
        """メインワークフロー（簡略化版）- 初期確認なし"""
        print("\n" + "="*50)
        print("VoiceChatBot - シンプル音声制御")
        print("="*50)
        
        # 直接音声入力を開始
        print("\n【ステップ1】音声入力開始")
        self.speak_text("お話しください")
        
        if self.start_dictation():
            print("✅ 音声入力①が正常に開始されました")
            return self.run_requirements_4_to_7()
        else:
            print("❌ 音声入力①の開始に失敗しました")
            return False
    
    def run_requirements_4_to_7(self):
        """ステップ4-7を実装（簡略化版）"""
        print("\n【ステップ4-7】音声入力処理と送信")
        
        try:
            # 要件4: バックグラウンドで音声入力②を起動
            self.stop_monitoring = False
            self.background_thread = threading.Thread(target=self.background_voice_monitor)
            self.background_thread.daemon = True
            self.background_thread.start()
            
            # 音声入力終了の検知を待機
            print("🎤 音声で話してください。「音声入力終わり」と言うと音声入力が停止されます")
            
            # バックグラウンドスレッドの終了を待機
            self.background_thread.join(timeout=60)  # 最大60秒待機
            
            if not self.stop_monitoring:
                print("⚠️ タイムアウトしました。手動で音声入力を停止します")
                self.stop_dictation()
            
            # 要件7: Cmd+Enterで送信
            print("\n【ステップ7】送信")
            if self.send_with_cmd_enter():
                print("✅ 送信完了しました")
                
                # 送信後のスクリーンショット処理
                return self.handle_post_send_screenshot()
            else:
                print("❌ 送信に失敗しました")
                return False
                
        except Exception as e:
            logger.error(f"Requirements 4-7 error: {e}")
            return False
    
    
    def wait_for_voice_confirmation(self, message: str) -> bool:
        """音声で「はい」の確認を待機"""
        self.speak_text(message)
        
        while True:
            try:
                print("🎤 「はい」と話してください...")
                
                temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                temp_file.close()
                
                cmd = ['rec', temp_file.name, 'trim', '0', '5']
                try:
                    subprocess.run(cmd, check=True, capture_output=True)
                    
                    if self.whisper_model:
                        segments, _ = self.whisper_model.transcribe(temp_file.name, language="ja")
                        text = " ".join([segment.text for segment in segments])
                        os.unlink(temp_file.name)
                        
                        if text:
                            print(f"音声認識結果: '{text}'")
                            
                            # 「はい」系の判定
                            yes_commands = ['はい', 'hai', 'yes', 'うん', 'そうです', 'オッケー', 'ok']
                            # 終わり系の判定
                            end_commands = ['終わり', 'おわり', 'オワリ', 'キャンセル', 'cancel', 'いいえ', 'no']
                            
                            text_lower = text.lower()
                            
                            if any(yes_word in text_lower for yes_word in yes_commands):
                                print("✅ 「はい」を検知")
                                return True
                            elif any(end_word in text_lower for end_word in end_commands):
                                print("❌ 終了コマンドを検知")
                                return False
                
                except:
                    # 録音失敗時はファイルを削除
                    try:
                        os.unlink(temp_file.name)
                    except:
                        pass
                
                time.sleep(1)
                
            except KeyboardInterrupt:
                print("\n🛑 キーボード割り込みで終了")
                return False
            except Exception as e:
                logger.error(f"Failed to wait for voice confirmation: {e}")
                return False
    
    def scroll_screen(self, scroll_amount: int = 5) -> bool:
        """画面全体でスクロール"""
        if not QUARTZ_AVAILABLE:
            print("💡 手動でスクロールしてください")
            return False
        
        try:
            # 画面の中央位置を計算
            from Quartz import CGDisplayBounds, CGMainDisplayID
            
            display_bounds = CGDisplayBounds(CGMainDisplayID())
            screen_width = int(display_bounds.size.width)
            screen_height = int(display_bounds.size.height)
            
            # 画面中央の座標
            center_x = int(screen_width * 0.5)
            center_y = int(screen_height * 0.5)
            
            print(f"📜 画面全体でスクロール中... (位置: {center_x}, {center_y})")
            
            # スクロールイベントを作成
            from Quartz.CoreGraphics import CGEventCreateScrollWheelEvent, CGEventPost, kCGScrollEventUnitPixel
            
            # 下方向にスクロール（負の値で下スクロール）
            scroll_event = CGEventCreateScrollWheelEvent(
                None,  # source
                kCGScrollEventUnitPixel,  # units
                1,     # wheelCount (垂直スクロールのみ)
                -scroll_amount * 10  # deltaAxis1 (負の値で下スクロール)
            )
            
            # マウス位置を設定
            from Quartz.CoreGraphics import CGEventSetLocation
            from Foundation import NSPoint
            CGEventSetLocation(scroll_event, NSPoint(center_x, center_y))
            
            # イベントを送信
            CGEventPost(kCGHIDEventTap, scroll_event)
            
            print("✅ 画面スクロール完了")
            return True
            
        except Exception as e:
            logger.error(f"Failed to scroll screen: {e}")
            return False
    
    def click_at_position(self, x: int, y: int) -> bool:
        """指定した座標をクリック"""
        if not QUARTZ_AVAILABLE:
            print(f"💡 手動で座標 ({x}, {y}) をクリックしてください")
            return False
        
        try:
            from Quartz.CoreGraphics import (
                CGEventCreateMouseEvent, CGEventPost, 
                kCGEventLeftMouseDown, kCGEventLeftMouseUp,
                kCGMouseButtonLeft
            )
            from Foundation import NSPoint
            
            print(f"🖱️ 座標 ({x}, {y}) をクリック中...")
            
            # マウスダウンイベント
            mouse_down = CGEventCreateMouseEvent(
                None,
                kCGEventLeftMouseDown,
                NSPoint(x, y),
                kCGMouseButtonLeft
            )
            
            # マウスアップイベント
            mouse_up = CGEventCreateMouseEvent(
                None,
                kCGEventLeftMouseUp,
                NSPoint(x, y),
                kCGMouseButtonLeft
            )
            
            # クリック実行
            CGEventPost(kCGHIDEventTap, mouse_down)
            time.sleep(0.1)  # 短い間隔
            CGEventPost(kCGHIDEventTap, mouse_up)
            
            print(f"✅ 座標 ({x}, {y}) のクリック完了")
            return True
            
        except Exception as e:
            logger.error(f"Failed to click at position ({x}, {y}): {e}")
            return False
    

    

    

    

    
    def capture_right_side_screen(self) -> Optional[str]:
        """画面右側をキャプチャ"""
        try:
            from Quartz import CGDisplayBounds, CGMainDisplayID
            
            display_bounds = CGDisplayBounds(CGMainDisplayID())
            screen_width = int(display_bounds.size.width)
            screen_height = int(display_bounds.size.height)
            
            # 画面右側の範囲を計算（右50%）
            right_x = screen_width // 2
            right_width = screen_width - right_x
            
            # スクリプトのディレクトリにright_side_screenshot.pngで保存
            script_dir = os.path.dirname(os.path.abspath(__file__))
            screenshot_path = os.path.join(script_dir, "right_side_screenshot.png")
            
            print(f"📸 画面右側をキャプチャ中... (範囲: {right_x}, 0, {right_width}, {screen_height})")
            
            # screencaptureで画面右側のみをキャプチャ
            cmd = [
                'screencapture', 
                '-x',  # 音なし
                '-R', f"{right_x},0,{right_width},{screen_height}",  # 範囲指定
                screenshot_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and os.path.exists(screenshot_path):
                print(f"✅ 画面右側キャプチャ完了: {screenshot_path}")
                return screenshot_path
            else:
                print(f"❌ 画面右側キャプチャ失敗: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to capture right side screen: {e}")
            return None
    

    
    def click_fallback_position(self) -> bool:
        """フォールバック: 推定位置をクリック"""
        try:
            from Quartz import CGDisplayBounds, CGMainDisplayID
            
            display_bounds = CGDisplayBounds(CGMainDisplayID())
            screen_width = int(display_bounds.size.width)
            screen_height = int(display_bounds.size.height)
            
            # 画面右側の適当な位置をクリック（画面幅の70%, 高さの40%）
            click_x = int(screen_width * 0.7)
            click_y = int(screen_height * 0.4)
            
            print(f"💡 フォールバック: 推定位置 ({click_x}, {click_y}) をクリックします")
            return self.click_at_position(click_x, click_y)
            
        except Exception as e:
            logger.error(f"Failed to click fallback position: {e}")
            return False
    
    def find_and_click_image_simple(self, button_image: str = "startVoiceBtn.png") -> bool:
        """PyAutoGUIを使用したシンプルな画像検索・クリック（複数ボタン対応・座標補正廃止）"""
        try:
            try:
                import pyautogui
            except ImportError:
                print("❌ PyAutoGUIが利用できません。pip install pyautoguiでインストールしてください")
                return False
            
            print(f"🔍 PyAutoGUIで{button_image}を全画面検索中...")
            
            # スクリプトディレクトリからボタン画像のパスを取得
            script_dir = os.path.dirname(os.path.abspath(__file__))
            button_path = os.path.join(script_dir, button_image)
            
            print(f"🔍 ボタン画像パス: {button_path}")
            print(f"🔍 ファイルが存在するか: {os.path.exists(button_path)}")
            
            if not os.path.exists(button_path):
                print(f"❌ ボタン画像 {button_image} が見つかりません")
                return False
            
            # デバッグ: スクリーンショットを取得
            screenshot = pyautogui.screenshot()
            print(f"🔍 スクリーンショットサイズ: {screenshot.size}")
            
            # 画像を画面上で検索（全て検索）
            try:
                locations = list(pyautogui.locateAllOnScreen(button_path, confidence=0.4))
                print(f"🔍 検索結果: {len(locations)}個のボタンを発見")
                for i, loc in enumerate(locations):
                    print(f"  ボタン{i+1}: {loc}")
            except pyautogui.ImageNotFoundException:
                print(f"❌ {button_image} が見つかりませんでした")
                return False
            except Exception as search_error:
                print(f"❌ 画像検索エラー: {search_error}")
                return False
            
            if locations:
                # 複数のボタンがある場合は最下部（y座標が最大）のボタンを選択
                if len(locations) > 1:
                    bottom_location = max(locations, key=lambda loc: loc.top)
                    print(f"🎯 複数ボタンあり - 最下部ボタンを選択: {bottom_location}")
                else:
                    bottom_location = locations[0]
                    print(f"🎯 ボタンを発見: {bottom_location}")
                
                # 見つかった位置の中心を取得
                center = pyautogui.center(bottom_location)
                print(f"🖱️ クリック座標: {center}")
                
                # 座標補正なしで直接クリック
                pyautogui.click(center.x, center.y)
                print(f"✅ {button_image} のクリック完了（座標補正なし）")
                return True
            else:
                print(f"❌ {button_image} が見つかりませんでした")
                return False
                
        except Exception as e:
            print(f"❌ PyAutoGUIエラーの詳細: {str(e)}")
            logger.error(f"Failed to find and click image with PyAutoGUI: {e}")
            return False

    # ...existing code...
    
def main():
    """メイン関数"""
    print("VoiceChatBot for macOS")
    print("=====================")
    print("シンプル音声制御ワークフロー:")
    print("1. 音声入力開始（確認なし）")
    print("2. 音声入力終了の検知")
    print("3. 自動送信")
    print("4. ChatGPT出力確認（音声制御）")
    print("※全て音声で操作します（ひらがな・漢字・カタカナ対応）")
    print("")
    
    bot = VoiceBot()
    success = bot.run_requirements_1_to_3()
    
    if success:
        print("\n🎉 全ての要件が正常に完了しました！")
    else:
        print("\n❌ 処理中にエラーが発生しました")

def test_voice_function():
    """音声機能のテスト用関数"""
    print("音声機能のテストを開始します...")
    
    bot = VoiceBot()
    
    # 音声確認テスト
    print("\n=== 音声確認テスト ===")
    print("音声確認機能をテストします...")
    result = bot.wait_for_voice_confirmation("テスト用メッセージです。「はい」と答えてください")
    
    if result:
        print("✅ 音声確認テスト成功")
    else:
        print("❌ 音声確認テスト失敗")

def test_scroll_click_function():
    """スクロールとクリック機能のテスト用関数"""
    print("スクロールとクリック機能のテストを開始します...")
    
    bot = VoiceBot()
    
    # スクロールテスト（全画面対応）
    print("\n=== 全画面スクロールテスト ===")
    print("画面全体でスクロールします...")
    if bot.scroll_screen():
        print("✅ 全画面スクロールテスト成功")
    else:
        print("❌ 全画面スクロールテスト失敗")
    
    time.sleep(2)  # 2秒待機
    
    # 方法選択を削除し、PyAutoGUI方式のみ使用
    print("\n=== PyAutoGUI方式テスト ===")
    if bot.find_and_click_image_simple("startVoiceBtn.png"):
        print("✅ PyAutoGUI方式テスト成功")
    else:
        print("❌ PyAutoGUI方式テスト失敗")
    
    time.sleep(2)  # 2秒待機
    
    # startVoiceBtn.png検索・クリックテスト（シンプル版）
    print("\n=== startVoiceBtn.png検索・クリックテスト（シンプル版） ===")
    print("PyAutoGUIを使用してstartVoiceBtn.pngを探してクリックします...")
    if bot.find_and_click_image_simple("startVoiceBtn.png"):
        print("✅ startVoiceBtn.pngクリックテスト成功")
    else:
        print("❌ startVoiceBtn.pngクリックテスト失敗")

if __name__ == "__main__":
    import sys
    
    # コマンドライン引数でテストモードを指定
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            test_voice_function()
        elif sys.argv[1] == "scroll":
            test_scroll_click_function()
        else:
            print("使用方法:")
            print("  python voice_chat_bot.py          # メイン機能")
            print("  python voice_chat_bot.py test     # 音声テスト")
            print("  python voice_chat_bot.py scroll   # スクロール・クリックテスト")
    else:
        main()

