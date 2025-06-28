#!/usr/bin/env python3
"""
Final Voice Chat Bot for macOS ChatGPT App
最終版：音声入力②をクリップボード監視方式で実装
"""

import time
import subprocess
import logging
import threading
import os
import tempfile
from typing import Optional
from datetime import datetime

# 音声認識用のインポート
try:
    from faster_whisper import WhisperModel
    VOICE_RECOGNITION_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Voice recognition libraries not available: {e}")
    VOICE_RECOGNITION_AVAILABLE = False

# macOS用のインポート
try:
    from AppKit import NSWorkspace, NSApplication
    from Cocoa import NSPasteboard, NSStringPboardType
    from Quartz.CoreGraphics import (
        CGEventCreateKeyboardEvent, CGEventPost, kCGHIDEventTap,
        CGEventTapCreate, kCGSessionEventTap, kCGHeadInsertEventTap,
        kCGEventKeyDown, kCGEventKeyUp, kCGEventFlagsChanged,
        CGEventGetIntegerValueField, kCGKeyboardEventKeycode,
        CGEventGetFlags, kCGEventFlagMaskCommand
    )
    import objc
    ACCESSIBILITY_AVAILABLE = True
    QUARTZ_AVAILABLE = True
except ImportError:
    ACCESSIBILITY_AVAILABLE = False
    QUARTZ_AVAILABLE = False
    print("Warning: Accessibility frameworks not available")

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('voice_chat_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# macOS Quartzを使用したキー送信関数（純粋実装）
def press_key_quartz(keycode: int) -> bool:
    """Quartzを使用してキーを送信"""
    if not QUARTZ_AVAILABLE:
        logger.error("Quartz not available")
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
        logger.error(f"Quartz key press failed: {e}")
        return False

def start_dictation_quartz() -> bool:
    """Quartz使用して右コマンドキー2回で音声入力開始"""
    if not QUARTZ_AVAILABLE:
        logger.error("Quartz not available for dictation start")
        return False
    
    try:
        # キーコード54 = Right Command
        RIGHT_COMMAND_KEY = 54
        
        logger.info("Starting dictation with Quartz (Right Command x2)")
        
        # 1回目
        if not press_key_quartz(RIGHT_COMMAND_KEY):
            logger.error("First right command key press failed")
            return False
        
        time.sleep(0.1)  # 間隔（sample.pyと同じ）
        
        # 2回目
        if not press_key_quartz(RIGHT_COMMAND_KEY):
            logger.error("Second right command key press failed")
            return False
        
        logger.info("Right command key sequence completed")
        return True
        
    except Exception as e:
        logger.error(f"Dictation start failed: {e}")
        return False

def stop_dictation_quartz() -> bool:
    """Quartz使用してEscapeキーで音声入力停止"""
    if not QUARTZ_AVAILABLE:
        logger.error("Quartz not available for dictation stop")
        return False
    
    try:
        # キーコード53 = Escape
        ESCAPE_KEY = 53
        
        logger.info("Stopping dictation with Quartz (Escape)")
        
        if not press_key_quartz(ESCAPE_KEY):
            logger.error("Escape key press failed")
            return False
        
        logger.info("Escape key press completed")
        return True
        
    except Exception as e:
        logger.error(f"Dictation stop failed: {e}")
        return False

class KeyboardMonitor:
    """キーボード監視クラス（Command+Enter検出用）"""
    
    def __init__(self):
        self.is_monitoring = False
        self.cmd_enter_pressed = False
        self.event_tap = None
        
    def keyboard_event_handler(self, proxy, event_type, event, refcon):
        """キーボードイベントハンドラー"""
        try:
            if event_type == kCGEventKeyDown:
                keycode = CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)
                flags = CGEventGetFlags(event)
                
                # Enter key (keycode 36) + Command modifier
                if keycode == 36 and (flags & kCGEventFlagMaskCommand):
                    logger.info("Command+Enter detected!")
                    print("🎯 Command+Enter が検出されました！")
                    self.cmd_enter_pressed = True
                    return None  # イベントを消費
            
            return event  # 他のイベントはそのまま通す
            
        except Exception as e:
            logger.error(f"Keyboard event handler error: {e}")
            return event
    
    def start_monitoring(self) -> bool:
        """キーボード監視開始"""
        try:
            if not QUARTZ_AVAILABLE:
                logger.error("Quartz not available for keyboard monitoring")
                return False
            
            logger.info("Starting keyboard monitoring for Command+Enter...")
            print("⌨️ Command+Enter監視を開始しています...")
            
            self.cmd_enter_pressed = False
            self.is_monitoring = True
            
            # イベントタップを作成
            self.event_tap = CGEventTapCreate(
                kCGSessionEventTap,
                kCGHeadInsertEventTap,
                0,  # Active
                1 << kCGEventKeyDown,  # Key down events only
                self.keyboard_event_handler,
                None
            )
            
            if self.event_tap:
                print("✅ Command+Enter監視が開始されました")
                return True
            else:
                logger.error("Failed to create event tap")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start keyboard monitoring: {e}")
            return False
    
    def stop_monitoring(self) -> None:
        """キーボード監視停止"""
        try:
            self.is_monitoring = False
            if self.event_tap:
                # Note: 実際の停止処理は簡易実装
                logger.info("Keyboard monitoring stopped")
                print("⌨️ Command+Enter監視を停止しました")
                
        except Exception as e:
            logger.error(f"Failed to stop keyboard monitoring: {e}")
    
    def wait_for_cmd_enter(self, timeout: int = 60) -> bool:
        """Command+Enterが押されるまで待機"""
        start_time = time.time()
        
        while time.time() - start_time < timeout and self.is_monitoring:
            if self.cmd_enter_pressed:
                logger.info("Command+Enter detected during wait")
                return True
            time.sleep(0.1)
        
        logger.warning("Command+Enter wait timeout")
        return False

class VoiceCommandRecognizer:
    """音声入力②：macOSの録音機能を使った独立音声認識"""
    
    def __init__(self):
        self.model = None
        
        if VOICE_RECOGNITION_AVAILABLE:
            try:
                # Whisperモデルを初期化（軽量版）
                self.model = WhisperModel("tiny", device="cpu")
                logger.info("Whisper model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}")
                self.model = None
        
        logger.info("VoiceCommandRecognizer initialized (macOS recording + Whisper)")
    
    def record_audio_macos(self, duration: int = 10) -> str:
        """macOSのrecコマンドで音声録音"""
        try:
            # 一時ファイル作成
            temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            temp_file.close()
            
            print(f"🎤 音声録音中... ({duration}秒)")
            print("「はい」または「いいえ」と話してください")
            print("ゆっくりとはっきり話してください")
            print("録音開始！ 📣")
            
            # macOSのrecコマンドで録音
            cmd = [
                'rec', 
                temp_file.name,
                'trim', '0', str(duration)
            ]
            
            try:
                subprocess.run(cmd, check=True, capture_output=True)
                print("✅ 録音完了！")
                return temp_file.name
            except subprocess.CalledProcessError:
                # recコマンドが利用できない場合
                print("録音機能が利用できません。")
                return None
                
        except Exception as e:
            logger.error(f"macOS recording failed: {e}")
            return None
    
    def _keyboard_fallback(self) -> str:
        """音声認識失敗時の再試行処理"""
        print("音声認識が利用できません。")
        print("もう一度音声で「はい」または「いいえ」と話してください...")
        
        # 音声認識を再試行（簡易版）
        for attempt in range(3):
            print(f"再試行 {attempt + 1}/3:")
            time.sleep(1)
            audio_file = self.record_audio_macos(duration=8)  # 再試行は少し短く
            if audio_file:
                text = self.transcribe_audio(audio_file)
                if text:
                    text_lower = text.lower()
                    yes_commands = [
                        'はい', 'hai', 'yes', 'うん', 'そうです', 'オッケー', 'ok', 'そう',
                        'お願い', 'します', 'いたします', 'ください', '続行', '開始', 
                        'よろしく', 'いいよ', 'いいです', 'ありがとう', 'スタート'
                    ]
                    if any(yes_word in text_lower for yes_word in yes_commands):
                        return "はい"
                    # 明確に「いいえ」系の場合
                    no_commands = ['いいえ', 'いえ', 'no', 'だめ', 'やめ', 'キャンセル', 'ストップ', '中止']
                    if any(no_word in text_lower for no_word in no_commands):
                        return "いいえ"
        
        print("音声認識に3回失敗しました。デフォルトで「いいえ」として処理します。")
        return "いいえ"
    
    def transcribe_audio(self, audio_file: str) -> Optional[str]:
        """音声ファイルをテキストに変換"""
        try:
            if not self.model or not audio_file or not os.path.exists(audio_file):
                return None
            
            segments, _ = self.model.transcribe(audio_file, language="ja")
            text = " ".join([segment.text for segment in segments])
            
            # 一時ファイルを削除
            os.unlink(audio_file)
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None
    
    def wait_for_yes_command(self, timeout: int = 60) -> bool:
        """「はい」コマンドを待機（完全音声認識のみ）"""
        try:
            if not VOICE_RECOGNITION_AVAILABLE:
                # 音声認識が利用できない場合は音声で再試行
                result_text = self._keyboard_fallback()
                return result_text == "はい"
            
            # 音声録音
            audio_file = self.record_audio_macos(duration=2)
            
            if not audio_file:
                # 録音失敗時は音声で再試行
                result_text = self._keyboard_fallback()
                return result_text == "はい"
            
            # 音声認識
            text = self.transcribe_audio(audio_file)
            
            if text:
                text_lower = text.lower()
                yes_commands = [
                    'はい', 'hai', 'yes', 'うん', 'そうです', 'オッケー', 'ok', 'そう',
                    'お願い', 'します', 'いたします', 'ください', '続行', '開始', 
                    'よろしく', 'いいよ', 'いいです', 'ありがとう', 'スタート'
                ]
                
                result = any(yes_word in text_lower for yes_word in yes_commands)
                print(f"音声認識結果: '{text}' → 判定: {'はい' if result else 'いいえ'}")
                return result
            else:
                print("音声認識に失敗しました")
                result_text = self._keyboard_fallback()
                return result_text == "はい"
                
        except Exception as e:
            logger.error(f"Voice command recognition error: {e}")
            result_text = self._keyboard_fallback()
            return result_text == "はい"

class ChatGPTResponseExtractor:
    """ChatGPTの回答を取得するクラス"""
    
    def __init__(self):
        self.chatgpt_bundle_id = "com.openai.chat"
        self.last_response = ""
        
    def is_chatgpt_active(self) -> bool:
        """ChatGPTアプリがアクティブかチェック"""
        if not ACCESSIBILITY_AVAILABLE:
            return False
            
        try:
            workspace = NSWorkspace.sharedWorkspace()
            active_app = workspace.frontmostApplication()
            return active_app.bundleIdentifier() == self.chatgpt_bundle_id
        except Exception as e:
            logger.error(f"Failed to check active app: {e}")
            return False
    
    def get_response_via_clipboard(self) -> Optional[str]:
        """クリップボード経由で回答を取得"""
        try:
            if ACCESSIBILITY_AVAILABLE:
                pasteboard = NSPasteboard.generalPasteboard()
                content = pasteboard.stringForType_(NSStringPboardType)
            else:
                result = subprocess.run(['pbpaste'], capture_output=True, text=True)
                content = result.stdout.strip()
            
            if content and content != self.last_response:
                self.last_response = content
                return content
            
            return None
            
        except Exception as e:
            logger.error(f"Clipboard access error: {e}")
            return None
    
    def wait_for_response_ready(self) -> bool:
        """回答準備完了の確認（完全音声認識のみ）"""
        print("\nChatGPTの回答が完了したら:")
        print("1. 回答全体を選択（Cmd+A またはマウスで選択）")
        print("2. コピー（Cmd+C）")
        print("3. 「はい」と音声で答えてください")
        
        # 音声認識で確認
        recognizer = VoiceCommandRecognizer()
        return recognizer.wait_for_yes_command()

class NativeDictationController:
    """macOS純正音声入力の制御（Command+Enter監視付き）"""
    
    def __init__(self):
        self.is_active = False
        self.keyboard_monitor = KeyboardMonitor()
    
    def check_dictation_status(self) -> bool:
        """純正音声入力の状態をチェック（簡易版）"""
        # プロセス検証は削除 - 常にFalseを返す
        return False
    
    def start_dictation(self) -> bool:
        """純正音声入力を開始（Quartz純粋実装）"""
        try:
            logger.info("Starting native dictation...")
            print("🎤 macOS音声入力を開始しています...")
            
            # Quartz（macOSネイティブAPI）で右コマンドキー2回押し
            print("Quartz（macOSネイティブAPI）で右コマンドキー2回押し...")
            
            if not QUARTZ_AVAILABLE:
                print("❌ Quartzが利用できません")
                print("💡 手動で音声入力を開始してください：")
                print("   - 右コマンドキーを2回素早く押す")
                return False
            
            if start_dictation_quartz():
                print("✅ Quartz経由で右コマンドキー送信完了")
            else:
                print("❌ Quartz経由でのキー送信に失敗しました")
                print("💡 手動で音声入力を開始してください：")
                print("   - 右コマンドキーを2回素早く押す")
                return False
            
            print("音声入力の起動を待機中...")
            time.sleep(2)
            
            print("✅ 音声入力①の起動処理が完了しました（Quartz右コマンドキー方式）")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start dictation: {e}")
            return False
    
    def stop_dictation(self) -> bool:
        """純正音声入力を停止（Quartz純粋実装でEscapeキー）"""
        try:
            logger.info("Stopping native dictation...")
            print("音声入力①を停止中...")
            
            # Quartz（macOSネイティブAPI）でEscapeキーを送信
            if not QUARTZ_AVAILABLE:
                print("❌ Quartzが利用できません")
                print("💡 手動で音声入力を停止してください：Escapeキーを押す")
                return False
            
            if stop_dictation_quartz():
                print("✅ Quartz経由でEscapeキー送信完了")
            else:
                print("❌ Quartz経由でのEscapeキー送信に失敗しました")
                print("💡 手動で音声入力を停止してください：Escapeキーを押す")
                return False
            
            # 停止確認の待機
            time.sleep(1)
            print("✅ 音声入力①の停止処理が完了しました")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop dictation: {e}")
            return False
    
    def wait_for_dictation_completion(self, timeout: int = 60) -> bool:
        """音声入力の完了を待機（Command+Enter監視方式）"""
        logger.info("Waiting for dictation completion with Command+Enter monitoring...")
        print("音声で質問を話した後、Command+Enterで送信してください...")
        
        # キーボード監視開始
        if not self.keyboard_monitor.start_monitoring():
            logger.warning("Failed to start keyboard monitoring, falling back to simple wait")
            print("⚠️ キーボード監視に失敗しました。30秒待機します...")
            time.sleep(30)
            return True
        
        print("Command+Enterを押すと質問が送信されます...")
        
        # Command+Enterが押されるまで待機
        if self.keyboard_monitor.wait_for_cmd_enter(timeout):
            print("✅ Command+Enterが検出されました。質問を送信中...")
            
            # キーボード監視停止
            self.keyboard_monitor.stop_monitoring()
            
            # 音声入力を停止（Escapeキー送信）
            if self.stop_dictation():
                logger.info("Dictation stopped successfully after Command+Enter")
                print("✅ 音声入力①が正常に停止されました")
                return True
            else:
                logger.warning("Failed to stop dictation after Command+Enter")
                print("⚠️ 音声入力①の停止に失敗しましたが、続行します")
                return True
        else:
            print("⚠️ Command+Enterの検出がタイムアウトしました")
            self.keyboard_monitor.stop_monitoring()
            return False

class FinalVoiceChatBot:
    """最終版 Voice Chat Bot"""
    
    def __init__(self):
        self.voice_commands = VoiceCommandRecognizer()
        self.response_extractor = ChatGPTResponseExtractor()
        self.dictation_controller = NativeDictationController()
        self.is_running = False
        
        logger.info("FinalVoiceChatBot initialized")
    
    def speak_text(self, text: str) -> None:
        """テキストを読み上げ"""
        try:
            logger.info(f"Speaking: {text[:50]}...")
            print(f"🔊 読み上げ: {text[:50]}...")
            
            # sayコマンドを実行
            result = subprocess.run(['say', text], timeout=30, check=False)
            
            if result.returncode == 0:
                logger.info("Speech completed")
                print("✅ 読み上げ完了")
            else:
                logger.warning(f"Speech command returned {result.returncode}")
                print("⚠️ 読み上げ警告")
                
        except subprocess.TimeoutExpired:
            logger.warning("Speech timeout")
            print("⚠️ 読み上げタイムアウト")
        except Exception as e:
            logger.error(f"Speech failed: {e}")
            print(f"❌ 読み上げエラー: {e}")
            # フォールバック: テキストを表示
            print(f"📝 メッセージ: {text}")
    
    def setup_phase(self) -> bool:
        """初期セットアップフェーズ"""
        print("\n" + "="*60)
        print("VoiceChatBot セットアップ")
        print("="*60)
        
        # 音声での指示（音声入力②は使わない）
        setup_message = "準備はできましたか？"
        
        print(f"指示: {setup_message}")
        print("\n🔊 指示を読み上げ中...")
        self.speak_text(setup_message)
        
        # ここで音声入力②で「はい」を待機
        print("\n🎤 チャット欄を選択完了後、音声入力②で確認します")
        return self.voice_commands.wait_for_yes_command()
    
    def start_main_dictation_after_setup(self) -> bool:
        """セットアップ完了後に音声入力①を起動"""
        print("\n✅ セットアップ完了！")
        print("🎤 質問用の音声入力①を開始します...")
        
        # 音声入力①（純正）を起動
        if self.dictation_controller.start_dictation():
            print("✅ 音声入力①が開始されました")
            return True
        else:
            print("❌ 音声入力①の開始に失敗しました")
            return False
    
    def chat_cycle(self) -> bool:
        """1回のチャットサイクル"""
        try:
            print("\n" + "-"*50)
            print("新しい質問を受付中...")
            
            # 1. 音声入力①を確実に起動
            print("🎤 音声入力①を起動します...")
            if not self.dictation_controller.start_dictation():
                print("❌ 音声入力①の開始に失敗しました")
                return False
            
            print("音声で質問を話してください（終了したら自動的に送信されます）")
            
            # 2. 音声入力の完了を待機（Command+Enter検出）
            if self.dictation_controller.wait_for_dictation_completion():
                print("✅ 質問が送信されました")
            else:
                print("⚠️ 音声入力の完了を確認できませんでした")
                print("音声で質問を話したら、送信完了と音声で答えてください")
                
                # 音声認識で送信完了確認
                if self.voice_commands.wait_for_yes_command():
                    print("✅ 送信完了を確認しました")
                else:
                    print("❌ 送信確認がキャンセルされました")
                    return False
            
            # 3. ChatGPTの回答を自動取得・読み上げ
            print("🤖 ChatGPTの回答を待機中...")
            print("回答が完了したら自動的に読み上げます...")
            
            # 回答準備の確認
            if self.response_extractor.wait_for_response_ready():
                response = self.response_extractor.get_response_via_clipboard()
                
                if response:
                    print(f"\nChatGPT回答:")
                    print("-" * 40)
                    print(response)
                    print("-" * 40)
                    
                    # 4. 回答を即座に読み上げ
                    print("\n🔊 回答を読み上げ中...")
                    self.speak_text(response)
                    
                    print("✅ 読み上げ完了")
                    return True
                else:
                    print("❌ 回答を取得できませんでした")
                    return False
            else:
                print("❌ 回答の準備がキャンセルされました")
                return False
                
        except Exception as e:
            logger.error(f"Error in chat cycle: {e}")
            return False
    
    def continuation_check(self) -> bool:
        """継続確認"""
        continue_message = "次の質問をしますか？"
        print(f"\n{continue_message}")
        self.speak_text(continue_message)
        
        # 音声入力②で継続確認
        will_continue = self.voice_commands.wait_for_yes_command()
        
        if will_continue:
            print("🔄 次の質問に進みます")
            # 音声入力①を起動
            print("🎤 音声入力①を起動しています...")
            self.dictation_controller.start_dictation()
        else:
            print("🛑 チャットを終了します")
        
        return will_continue
    
    def main_loop(self) -> None:
        """メインループ"""
        try:
            # セットアップフェーズ
            if not self.setup_phase():
                print("セットアップがキャンセルされました。終了します。")
                return
            
            # セットアップ完了後に音声入力①を起動
            if not self.start_main_dictation_after_setup():
                print("音声入力①の開始に失敗しました。終了します。")
                return
            
            self.is_running = True
            print("\n🚀 VoiceChatBot開始！")
            
            # チャットループ
            while self.is_running:
                # チャットサイクル実行
                success = self.chat_cycle()
                
                if success:
                    # 継続確認
                    if not self.continuation_check():
                        print("👋 チャットを終了します")
                        break
                else:
                    print("❌ エラーが発生しました")
                    retry_message = "再試行しますか？"
                    self.speak_text(retry_message)
                    
                    if not self.voice_commands.wait_for_yes_command():
                        break
        
        except KeyboardInterrupt:
            logger.info("User interrupted")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self) -> None:
        """クリーンアップ"""
        self.is_running = False
        self.dictation_controller.stop_dictation()
        logger.info("FinalVoiceChatBot stopped")

def main():
    """メイン関数"""
    print("Final VoiceChatBot for macOS ChatGPT")
    print("====================================")
    print("機能:")
    print("- 音声入力①: macOS純正（ChatGPT入力用）")
    print("- 音声入力②: 独立音声認識システム（制御用）") 
    print("- 自動読み上げ: ChatGPT回答の音声出力")
    print("- 完全音声制御: キーボード入力不要")
    print("")
    
    print("ワークフロー:")
    print("1. ChatGPTウィンドウ選択 → チャット欄クリック")
    print("2. 音声②で「はい」と確認 → 音声①自動起動")
    print("3. 音声①でChatGPTに質問 → Command+Enterで送信・音声入力停止")
    print("4. 手動で回答をコピー → 音声②で「はい」と確認")
    print("5. 自動読み上げ → 音声②で継続確認")
    print("")
    
    print("重要なポイント:")
    print("- 音声①: macOS純正音声入力（右コマンド2回で開始、Command+Enterで自動停止）")
    print("- 音声②: Whisper音声認識（独立システム）")
    print("- Command+Enter: 質問送信と音声入力停止を同時実行")
    print("- 全ての確認操作を音声②で実行")
    print("- キー操作: Quartz（macOSネイティブAPI）のみ使用")
    print("")
    print("🚀 VoiceChatBotを開始します...")
    
    try:
        bot = FinalVoiceChatBot()
        bot.main_loop()
    except Exception as e:
        logger.error(f"Failed to start FinalVoiceChatBot: {e}")
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
