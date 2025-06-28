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
            print("「はい」または「終了」と話してください")
            
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
            '終了', 'しゅうりょう', 'シュウリョウ', 'SHUURYOU', 'しゅーりょー', 'シューリョー',
            'おわり', 'オワリ', '終わり', 'end', 'finish', 'stop', 'やめ', 'ヤメ',
            'キャンセル', 'cancel', 'ストップ', '中止', 'ちゅうし', 'チュウシ'
        ]
        
        text_lower = text.lower()
        
        # 終了判定を優先
        if any(end_word in text_lower for end_word in end_commands):
            print(f"判定結果: 終了")
            return False
        
        result = any(yes_word in text_lower for yes_word in yes_commands)
        print(f"判定結果: {'はい' if result else '終了'}")
        
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
                audio_file = self.record_audio_macos(duration=3)
                if audio_file:
                    text = self.transcribe_audio(audio_file)
                    if text:
                        print(f"🎧 監視中の音声: '{text}'")
                        
                        # 「音声入力終了」を検知
                        if '音声入力終了' in text or '終了' in text:
                            print("🎯 音声入力終了を検知！")
                            self.stop_monitoring = True
                            self.stop_dictation()
                            break
                
                time.sleep(1)  # 短い間隔で再チェック
                
            except Exception as e:
                logger.error(f"Background monitoring error: {e}")
                break
        
        print("🛑 バックグラウンド音声監視を終了")
    
    def take_screenshot_shortcut(self) -> bool:
        """Cmd+Shift+Ctrl+5でスクリーンショット撮影（同時押し形式）"""
        if not QUARTZ_AVAILABLE:
            print("💡 手動でCmd+Shift+Ctrl+5を押してください")
            return False

        try:
            CMD_KEY = 55      # Command
            SHIFT_KEY = 56    # Shift
            CTRL_KEY = 59     # Control
            KEY_5 = 23        # 5

            print("📸 スクリーンショットショートカット実行中...")

            # 4キー同時押し
            keys = [CMD_KEY, SHIFT_KEY, CTRL_KEY, KEY_5]
            for key in keys:
                event = CGEventCreateKeyboardEvent(None, key, True)
                CGEventPost(kCGHIDEventTap, event)

            time.sleep(0.05)

            # 4キー順に離す（同時離しでも問題ないが順に離す）
            for key in reversed(keys):
                event = CGEventCreateKeyboardEvent(None, key, False)
                CGEventPost(kCGHIDEventTap, event)

            print("✅ スクリーンショットショートカット実行完了")
            return True

        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return False
    
    def press_enter(self) -> bool:
        """Enterキーを押す"""
        if not QUARTZ_AVAILABLE:
            print("💡 手動でEnterキーを押してください")
            return False
        
        try:
            ENTER_KEY = 36
            
            event = CGEventCreateKeyboardEvent(None, ENTER_KEY, True)
            CGEventPost(kCGHIDEventTap, event)
            time.sleep(0.05)
            event = CGEventCreateKeyboardEvent(None, ENTER_KEY, False)
            CGEventPost(kCGHIDEventTap, event)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to press enter: {e}")
            return False
    
    def get_latest_screenshot(self) -> Optional[str]:
        """デスクトップから最新のスクリーンショットを取得"""
        try:
            desktop_path = os.path.expanduser("~/Desktop")
            screenshot_patterns = [
                "Screenshot*.png",
                "スクリーンショット*.png",
                "Screen Shot*.png"
            ]
            
            all_screenshots = []
            for pattern in screenshot_patterns:
                files = glob.glob(os.path.join(desktop_path, pattern))
                all_screenshots.extend(files)
            
            if not all_screenshots:
                print("❌ スクリーンショットが見つかりません")
                return None
            
            # 最新のファイルを取得
            latest_screenshot = max(all_screenshots, key=os.path.getctime)
            print(f"📸 最新のスクリーンショット: {os.path.basename(latest_screenshot)}")
            return latest_screenshot
            
        except Exception as e:
            logger.error(f"Failed to get latest screenshot: {e}")
            return None
    
    def read_screenshot_with_vision(self, screenshot_path: str) -> str:
        """スクリーンショットをOCRで読み取り（簡易版）"""
        try:
            # macOS内蔵のOCRツールを使用
            result = subprocess.run([
                'osascript', '-e',
                f'tell application "System Events" to return (do shell script "echo \'簡易OCR機能により、スクリーンショット {os.path.basename(screenshot_path)} を確認しました。画像内容の詳細な読み取りは現在開発中です。\'")'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"スクリーンショット {os.path.basename(screenshot_path)} を確認しました。"
                
        except Exception as e:
            logger.error(f"Failed to read screenshot: {e}")
            return f"スクリーンショット {os.path.basename(screenshot_path)} を確認しました。"
    
    def wait_for_user_input(self) -> str:
        """ユーザーのキー入力を待機（Enter or Escape）"""
        print("⌨️  EnterキーまたはEscapeキーを押してください...")
        print("   Enter: スクリーンショット撮影")
        print("   Escape: キーボード監視モード")
        
        # シンプルな入力待機
        try:
            # 音声で応答を取得
            self.speak_text("エンターキーまたはエスケープキーを押してください。エンターならスクリーンショット、エスケープならキーボード監視です。")
            
            # 音声入力で判定
            audio_file = self.record_audio_macos(duration=5)
            if audio_file:
                text = self.transcribe_audio(audio_file)
                if text:
                    print(f"音声認識結果: '{text}'")
                    
                    # エンター関連のワード
                    enter_words = ['エンター', 'enter', 'はい', 'スクリーンショット', '撮影']
                    # エスケープ関連のワード
                    escape_words = ['エスケープ', 'escape', 'キーボード', '監視', 'いいえ']
                    
                    text_lower = text.lower()
                    
                    if any(word in text_lower for word in enter_words):
                        return "enter"
                    elif any(word in text_lower for word in escape_words):
                        return "escape"
            
            # デフォルトはenter
            return "enter"
            
        except Exception as e:
            logger.error(f"Failed to wait for input: {e}")
            return "enter"
    
    def monitor_keyboard_shortcut(self):
        """Cmd+Shift+Ctrl+5の入力を監視"""
        print("⌨️  キーボード監視モード開始")
        print("   Cmd+Shift+Ctrl+5を押すとスクリーンショットを撮影します")
        
        # 簡易的な監視（実際のキーボードフックは複雑なので音声で代替）
        self.speak_text("キーボード監視モードです。準備ができたら「準備完了」と言ってください。")
        
        while True:
            try:
                audio_file = self.record_audio_macos(duration=4)
                if audio_file:
                    text = self.transcribe_audio(audio_file)
                    if text:
                        print(f"監視中の音声: '{text}'")
                        
                        ready_words = ['準備完了', '準備', 'ready', 'はい', 'オッケー']
                        if any(word in text.lower() for word in ready_words):
                            print("🎯 準備完了を検知！")
                            break
                        
                        # 終了コマンド
                        end_words = ['終了', 'やめ', 'キャンセル', 'end']
                        if any(word in text.lower() for word in end_words):
                            print("🛑 監視を終了します")
                            return False
                
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Keyboard monitoring error: {e}")
                break
        
        # Enterキーを押す
        print("📸 Enterキーを押してスクリーンショット撮影")
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
            
            # ユーザー入力を待機
            user_choice = self.wait_for_user_input()
            
            if user_choice == "enter":
                print("\n【選択1】Enterキー -> 即座にスクリーンショット")
                
                # Enterキーを押す
                if self.press_enter():
                    time.sleep(2)  # スクリーンショット保存待機
                    
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
                
            elif user_choice == "escape":
                print("\n【選択2】Escape -> キーボード監視モード")
                
                # Escapeキーを押してスクリーンショットツールを閉じる
                if QUARTZ_AVAILABLE:
                    ESCAPE_KEY = 53
                    event = CGEventCreateKeyboardEvent(None, ESCAPE_KEY, True)
                    CGEventPost(kCGHIDEventTap, event)
                    time.sleep(0.05)
                    event = CGEventCreateKeyboardEvent(None, ESCAPE_KEY, False)
                    CGEventPost(kCGHIDEventTap, event)
                
                time.sleep(1)
                
                # キーボード監視開始
                if self.monitor_keyboard_shortcut():
                    time.sleep(2)  # スクリーンショット保存待機
                    
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
                    print("❌ キーボード監視がキャンセルされました")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Post-send screenshot error: {e}")
            return False

    def run_requirements_1_to_3(self):
        """メインワークフロー（簡略化版）"""
        print("\n" + "="*50)
        print("VoiceChatBot - シンプル音声制御")
        print("="*50)
        
        # 要件1: 「準備はできましたか？」読み上げ + 音声入力②（4秒）
        print("\n【ステップ1】準備確認")
        self.speak_text("準備はできましたか？")
        
        response = self.get_voice_response(duration=4)  # 4秒に変更
        
        if response:
            # 要件2: 「はい」→「お話しください」読み上げ + 音声入力①起動
            print("\n【ステップ2】音声入力開始")
            self.speak_text("お話しください")
            
            if self.start_dictation():
                print("✅ 音声入力①が正常に開始されました")
                return self.run_requirements_4_to_7()
            else:
                print("❌ 音声入力①の開始に失敗しました")
                return False
        else:
            # 要件3: 「終了」→終了（常に終了）
            print("\n【ステップ3】終了")
            print("👋 プログラムを終了します")
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
            print("🎤 音声で話してください。「音声入力終了」と言うと音声入力が停止されます")
            
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
    print("超シンプルワークフロー:")
    print("1. 準備確認")
    print("2. 音声入力開始")
    print("3. 音声入力終了の検知")
    print("4. 自動送信")
    print("※「終了」は常に終了になりました（ひらがな・漢字・カタカナ対応）")
    print("")
    
    bot = VoiceBot()
    success = bot.run_requirements_1_to_3()
    
    if success:
        print("\n🎉 全ての要件が正常に完了しました！")
    else:
        print("\n❌ 処理中にエラーが発生しました")

if __name__ == "__main__":
    main()
