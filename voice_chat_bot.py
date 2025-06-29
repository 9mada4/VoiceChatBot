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
    
    def take_screenshot_shortcut(self) -> bool:
        """Cmd+Shift+Ctrl+5でスクリーンショット撮影（修飾フラグ使用版）"""
        if not QUARTZ_AVAILABLE:
            print("💡 手動でCmd+Shift+Ctrl+5を押してください")
            return False

        try:
            CMD_KEY = 55      # Command
            SHIFT_KEY = 56    # Shift
            CTRL_KEY = 59     # Control
            KEY_5 = 23        # 5

            # 修飾フラグを定義
            FLAGS = (
                Quartz.kCGEventFlagMaskCommand |
                Quartz.kCGEventFlagMaskShift   |
                Quartz.kCGEventFlagMaskControl
            )

            print("📸 スクリーンショットショートカット実行中...")

            # 1) 修飾キーを押しっぱなし
            modifier_keys = [CTRL_KEY, SHIFT_KEY, CMD_KEY]
            for key in modifier_keys:
                event = CGEventCreateKeyboardEvent(None, key, True)
                CGEventPost(kCGHIDEventTap, event)

            time.sleep(0.05)  # 僅かに待機

            # 2) 5キーDown（修飾フラグ付き）
            event = CGEventCreateKeyboardEvent(None, KEY_5, True)
            Quartz.CGEventSetFlags(event, FLAGS)
            CGEventPost(kCGHIDEventTap, event)

            # 3) 5キーUp（修飾フラグ付き）
            event = CGEventCreateKeyboardEvent(None, KEY_5, False)
            Quartz.CGEventSetFlags(event, FLAGS)
            CGEventPost(kCGHIDEventTap, event)

            # 4) 修飾キーを離す
            for key in reversed(modifier_keys):
                event = CGEventCreateKeyboardEvent(None, key, False)
                CGEventPost(kCGHIDEventTap, event)

            print("✅ スクリーンショットショートカット実行完了")
            return True

        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return False
    
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
    
    def get_latest_screenshot(self) -> Optional[str]:
        """~/Pictures/Screenshotから最新のファイルを取得（フィルタリングなし）"""
        try:
            screenshot_dir = os.path.expanduser("~/Pictures/Screenshot")
            
            if not os.path.exists(screenshot_dir):
                print(f"❌ スクリーンショットディレクトリが見つかりません: {screenshot_dir}")
                return None
            
            # 全てのファイルを取得（フィルタリングなし）
            all_files = []
            for item in os.listdir(screenshot_dir):
                item_path = os.path.join(screenshot_dir, item)
                # ディレクトリは除外、ファイルのみ
                if os.path.isfile(item_path):
                    all_files.append(item_path)
            
            if not all_files:
                print(f"❌ {screenshot_dir} にファイルが見つかりません")
                return None
            
            # 最新のファイルを取得（作成時間順）
            latest_file = max(all_files, key=os.path.getctime)
            print(f"📸 最新のファイル: {os.path.basename(latest_file)}")
            return latest_file
            
        except Exception as e:
            logger.error(f"Failed to get latest file: {e}")
            return None
    
    def read_screenshot_with_vision(self, screenshot_path: str) -> str:
        """スクリーンショットをmacOS Vision frameworkでOCR読み取り"""
        try:
            if not os.path.exists(screenshot_path):
                return f"スクリーンショットファイル {os.path.basename(screenshot_path)} が見つかりません。"
            
            if VISION_AVAILABLE:
                return self._read_with_vision_framework(screenshot_path)
            else:
                return self._read_with_fallback_ocr(screenshot_path)
                
        except Exception as e:
            logger.error(f"Failed to read screenshot: {e}")
            return f"スクリーンショット {os.path.basename(screenshot_path)} の読み取り中にエラーが発生しました: {str(e)}"
    
    def _read_with_vision_framework(self, screenshot_path: str) -> str:
        """Vision frameworkを使用したOCR処理"""
        try:
            from objc import nil
            
            # 画像ファイルを読み込み
            image_url = NSURL.fileURLWithPath_(screenshot_path)
            image_data = NSData.dataWithContentsOfURL_(image_url)
            
            if not image_data:
                return f"画像ファイル {os.path.basename(screenshot_path)} の読み込みに失敗しました。"
            
            # VNImageRequestHandlerを作成
            request_handler = Vision.VNImageRequestHandler.alloc().initWithData_options_(image_data, nil)
            
            # テキスト認識リクエストを作成
            text_request = Vision.VNRecognizeTextRequest.alloc().init()
            text_request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
            text_request.setRecognitionLanguages_(["en-US", "ja-JP"])
            text_request.setUsesLanguageCorrection_(True)
            
            # リクエストを実行
            error = None
            success = request_handler.performRequests_error_([text_request], None)
            
            if not success:
                return f"Vision framework でのテキスト認識に失敗しました。"
            
            # 結果を取得
            results = text_request.results()
            if not results or len(results) == 0:
                return f"スクリーンショット {os.path.basename(screenshot_path)} からテキストが見つかりませんでした。"
            
            # 認識されたテキストを結合
            recognized_texts = []
            for observation in results:
                if hasattr(observation, 'topCandidates_'):
                    candidates = observation.topCandidates_(1)
                    if candidates and len(candidates) > 0:
                        text = candidates[0].string()
                        if text and len(text.strip()) > 0:
                            recognized_texts.append(text.strip())
            
            if not recognized_texts:
                return f"スクリーンショット {os.path.basename(screenshot_path)} からテキストが認識できませんでした。"
            
            full_text = "\n".join(recognized_texts)
            logger.info(f"Vision OCR結果: {len(full_text)} 文字認識")
            
            return f"スクリーンショット {os.path.basename(screenshot_path)} から以下のテキストを認識しました:\n\n{full_text}"
            
        except Exception as e:
            logger.error(f"Vision framework OCR error: {e}")
            return self._read_with_fallback_ocr(screenshot_path)
    
    def _read_with_fallback_ocr(self, screenshot_path: str) -> str:
        """フォールバック用の簡易OCR"""
        try:
            # textutilを使用したフォールバック
            result = subprocess.run([
                'textutil', '-convert', 'txt', '-stdout', screenshot_path
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                content = result.stdout.strip()
                return f"スクリーンショット {os.path.basename(screenshot_path)} から以下のテキストを認識しました（フォールバック）:\n\n{content}"
            
            # textutilが失敗した場合、ファイル存在確認メッセージ
            file_size = os.path.getsize(screenshot_path)
            return f"スクリーンショット {os.path.basename(screenshot_path)} （{file_size} bytes）を確認しました。テキスト認識機能は現在制限されています。"
            
        except subprocess.TimeoutExpired:
            return f"スクリーンショット {os.path.basename(screenshot_path)} の処理がタイムアウトしました。"
        except Exception as e:
            logger.error(f"Fallback OCR error: {e}")
            return f"スクリーンショット {os.path.basename(screenshot_path)} を確認しました。"
    
    def wait_for_enter_or_escape(self) -> str:
        """スクリーンショット画面で音声による「はい」「いいえ」を監視"""
        print("⌨️  スクリーンショット画面が表示されています")
        print("   「はい」: スクリーンショット撮影を実行")
        print("   「いいえ」または「終わり」: スクリーンショット画面を閉じる")
        
        self.speak_text("スクリーンショット画面が表示されています。はいと言うとスクリーンショット撮影、いいえと言うと画面を閉じます。")
        
        # 音声入力を無限に待機
        while True:
            try:
                print("🎤 「はい」または「いいえ」と話してください...")
                
                # 直接音声録音
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
                            # 「いいえ」系の判定
                            no_commands = ['いいえ', 'no', 'だめ', 'ダメ', 'やめ', 'ヤメ']
                            # 終わり系の判定
                            end_commands = ['終わり', 'おわり', 'オワリ', 'キャンセル', 'cancel']
                            
                            text_lower = text.lower()
                            
                            if any(yes_word in text_lower for yes_word in yes_commands):
                                print("✅ 「はい」を検知 - スクリーンショット撮影")
                                return "enter"
                            elif any(no_word in text_lower for no_word in no_commands) or any(end_word in text_lower for end_word in end_commands):
                                print("❌ 「いいえ」または「終わり」を検知 - 画面を閉じる")
                                return "escape"
                
                except:
                    # 録音失敗時はファイルを削除
                    try:
                        os.unlink(temp_file.name)
                    except:
                        pass
                
                time.sleep(1)
                
            except KeyboardInterrupt:
                print("\n🛑 キーボード割り込みで終了")
                return "escape"
            except Exception as e:
                logger.error(f"Failed to wait for voice input: {e}")
                return "enter"
    
    def monitor_keyboard_shortcut(self):
        """音声監視モード（簡略化版）"""
        print("⌨️  音声監視モード開始")
        
        self.speak_text("音声監視モードです。準備ができたら「はい」と言ってください。")
        
        print("� 準備ができたら「はい」と言ってください...")
        
        while True:
            try:
                # 直接音声録音
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
                            print(f"監視中の音声: '{text}'")
                            
                            ready_words = ['はい', 'ready', 'オッケー', 'ok']
                            if any(word in text.lower() for word in ready_words):
                                print("🎯 「はい」を検知！")
                                break
                            
                            # 終わりコマンド
                            end_words = ['終わり', 'やめ', 'キャンセル', 'end']
                            if any(word in text.lower() for word in end_words):
                                print("� 監視を終了します")
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
                logger.error(f"Voice monitoring error: {e}")
                break
        
        # Enterキーを押す
        print("📸 スクリーンショット撮影を実行")
        self.press_enter()
        return True
    
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
        """送信後のスクリーンショット処理"""
        try:
            print("\n【ステップ8】スクリーンショット処理")
            
            # Cmd+Shift+Ctrl+5を実行
            print("📸 スクリーンショットツールを起動中...")
            if not self.take_screenshot_shortcut():
                print("❌ スクリーンショット起動に失敗")
                return False
            
            time.sleep(2)  # ツール起動待機
            
            # ユーザーが実際にキーを押すまで待機
            user_choice = self.wait_for_enter_or_escape()
            
            if user_choice == "enter":
                print("\n【選択1】「はい」選択 -> Enterキーを押してスクリーンショット撮影")
                
                # 「はい」と言われたので、Enterキーを押してスクリーンショット撮影
                if self.press_enter():
                    print("📸 スクリーンショット撮影を実行しました")
                    time.sleep(10)  # スクリーンショット保存待機
                    
                    # 最新のスクリーンショットを取得
                    screenshot_path = self.get_latest_screenshot()
                    if screenshot_path:
                        # スクリーンショットを読み上げ
                        screenshot_text = self.read_screenshot_with_vision(screenshot_path)
                        self.speak_text(f"スクリーンショットの内容: {screenshot_text}")
                        return True
                    else:
                        print("❌ スクリーンショットが見つかりませんでした")
                        return False
                else:
                    print("❌ Enterキーの送信に失敗しました")
                    return False
                
            elif user_choice == "escape":
                print("\n【選択2】「いいえ」選択 -> スクリーンショット画面終了")
                
                # ユーザーが「いいえ」と言ってスクリーンショット画面を閉じている
                time.sleep(1)
                
                # 音声監視開始
                print("📸 再度スクリーンショットツールを起動します...")
                if self.take_screenshot_shortcut():
                    time.sleep(2)
                    
                    if self.monitor_keyboard_shortcut():
                        time.sleep(10)  # スクリーンショット保存待機
                        
                        # 最新のスクリーンショットを取得
                        screenshot_path = self.get_latest_screenshot()
                        if screenshot_path:
                            # スクリーンショットを読み上げ
                            screenshot_text = self.read_screenshot_with_vision(screenshot_path)
                            self.speak_text(f"スクリーンショットの内容: {screenshot_text}")
                            return True
                        else:
                            print("❌ スクリーンショットが見つかりませんでした")
                            return False
                    else:
                        print("❌ 音声監視がキャンセルされました")
                        return False
                else:
                    print("❌ スクリーンショット再起動に失敗")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Post-send screenshot error: {e}")
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

def main():
    """メイン関数"""
    print("VoiceChatBot for macOS")
    print("=====================")
    print("シンプル音声制御ワークフロー:")
    print("1. 音声入力開始（確認なし）")
    print("2. 音声入力終了の検知")
    print("3. 自動送信")
    print("4. スクリーンショット（音声制御）")
    print("※全て音声で操作します（ひらがな・漢字・カタカナ対応）")
    print("")
    
    bot = VoiceBot()
    success = bot.run_requirements_1_to_3()
    
    if success:
        print("\n🎉 全ての要件が正常に完了しました！")
    else:
        print("\n❌ 処理中にエラーが発生しました")

def test_screenshot_function():
    """スクリーンショット機能のテスト用関数"""
    print("スクリーンショット機能のテストを開始します...")
    
    bot = VoiceBot()
    
    # 既存のスクリーンショット確認
    print("\n=== ~/Pictures/Screenshot 確認 ===")
    existing_screenshot = bot.get_latest_screenshot()
    if existing_screenshot:
        print(f"✅ 既存のスクリーンショットが見つかりました: {existing_screenshot}")
    else:
        print("❌ 既存のスクリーンショットが見つかりませんでした")
    
    # スクリーンショット機能のテスト
    print("\n=== スクリーンショット撮影テスト ===")
    print("Cmd+Shift+Ctrl+5を実行します...")
    result = bot.take_screenshot_shortcut()
    
    if result:
        print("✅ スクリーンショットショートカット実行成功")
        print("スクリーンショット画面が表示されましたか？ (y/n)")
        
        # 簡単な確認
        response = input().lower()
        if response in ['y', 'yes', 'はい']:
            print("✅ スクリーンショット画面の表示確認")
        else:
            print("❌ スクリーンショット画面が表示されていません")
            print("手動でCmd+Shift+Ctrl+5を試してみてください")
    else:
        print("❌ スクリーンショットショートカット実行失敗")

if __name__ == "__main__":
    import sys
    
    # コマンドライン引数でテストモードを指定
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_screenshot_function()
    else:
        main()

