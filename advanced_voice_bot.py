#!/usr/bin/env python3
"""
Advanced Voice Chat Bot for macOS ChatGPT App
音声入力①（純正）と音声入力②（制御用）を分離した実装
"""

import time
import pyautogui
import subprocess
import logging
import threading
import speech_recognition as sr
from typing import Optional, List
import json
from datetime import datetime

# macOS用のインポート
try:
    from AppKit import NSWorkspace, NSApplication
    from Cocoa import NSPasteboard, NSStringPboardType
    from ApplicationServices import AXUIElementCreateApplication, AXUIElementCopyElementAtPosition
    import objc
    ACCESSIBILITY_AVAILABLE = True
except ImportError:
    ACCESSIBILITY_AVAILABLE = False
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

class VoiceCommandRecognizer:
    """音声入力②：システム制御用の音声認識"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.is_listening = False
        
        # 音声認識の設定調整
        with self.microphone as source:
            logger.info("Adjusting microphone for ambient noise...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        
        logger.info("VoiceCommandRecognizer initialized")
    
    def listen_for_command(self, timeout: int = 10) -> Optional[str]:
        """音声コマンドを聞き取り"""
        try:
            logger.info("Listening for voice command...")
            
            with self.microphone as source:
                # タイムアウト付きで音声を聞き取り（録音時間を延長）
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=5)
            
            try:
                # Google Speech Recognitionを使用（日本語対応）
                text = self.recognizer.recognize_google(audio, language='ja-JP')
                logger.info(f"Recognized command: {text}")
                return text.lower()
                
            except sr.UnknownValueError:
                logger.warning("Could not understand audio")
                return None
            except sr.RequestError as e:
                logger.error(f"Speech recognition service error: {e}")
                return None
                
        except sr.WaitTimeoutError:
            logger.warning("Listening timeout")
            return None
        except Exception as e:
            logger.error(f"Error in voice command recognition: {e}")
            return None
    
    def wait_for_yes_command(self, timeout: int = 30) -> bool:
        """「はい」コマンドを待機"""
        logger.info("Waiting for 'はい' command...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            command = self.listen_for_command(timeout=10)
            if command:
                # 「はい」の様々なバリエーションに対応
                yes_commands = ['はい', 'hai', 'yes', 'うん', 'そうです', 'オッケー', 'ok']
                if any(yes_word in command for yes_word in yes_commands):
                    logger.info("Yes command detected")
                    return True
                else:
                    logger.info(f"Command '{command}' is not a yes command")
        
        logger.warning("Yes command timeout")
        return False

class ChatGPTResponseExtractor:
    """ChatGPTの回答を取得するクラス（Accessibility API使用）"""
    
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
    
    def get_chatgpt_response_accessibility(self) -> Optional[str]:
        """Accessibility APIでChatGPTの回答を取得"""
        if not ACCESSIBILITY_AVAILABLE:
            logger.warning("Accessibility API not available")
            return None
        
        try:
            # ChatGPTアプリの要素にアクセス
            # 注意: 実際の実装では、ChatGPTアプリのUI構造を調査する必要があります
            logger.info("Attempting to get response via Accessibility API...")
            
            # プレースホルダー実装
            # 実際にはChatGPTアプリのUIツリーを辿って最新の回答を取得
            return "Accessibility API経由での回答取得は現在開発中です。"
            
        except Exception as e:
            logger.error(f"Accessibility API error: {e}")
            return None
    
    def get_response_via_clipboard(self) -> Optional[str]:
        """クリップボード経由で回答を取得（フォールバック）"""
        try:
            if not ACCESSIBILITY_AVAILABLE:
                return None
                
            pasteboard = NSPasteboard.generalPasteboard()
            content = pasteboard.stringForType_(NSStringPboardType)
            
            if content and content != self.last_response:
                self.last_response = content
                return content
            
            return None
            
        except Exception as e:
            logger.error(f"Clipboard access error: {e}")
            return None
    
    def wait_for_new_response(self, timeout: int = 60) -> Optional[str]:
        """新しい回答を待機"""
        logger.info("Waiting for ChatGPT response...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            # まずAccessibility APIを試行
            response = self.get_chatgpt_response_accessibility()
            if response and "開発中" not in response:
                return response
            
            # フォールバック: クリップボード監視
            # ユーザーに手動コピーを依頼
            time.sleep(2)
        
        logger.warning("Response timeout")
        return None

class NativeDictationController:
    """音声入力①：macOS純正音声入力の制御"""
    
    def __init__(self):
        self.is_active = False
    
    def check_dictation_status(self) -> bool:
        """純正音声入力の状態をチェック"""
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            dictation_processes = ['DictationIM', 'SpeechRecognitionServer']
            
            for process in dictation_processes:
                if process in result.stdout:
                    self.is_active = True
                    return True
            
            self.is_active = False
            return False
            
        except Exception as e:
            logger.error(f"Failed to check dictation status: {e}")
            return False
    
    def start_dictation(self) -> bool:
        """純正音声入力を開始（複数の方法を試行）"""
        try:
            if self.check_dictation_status():
                logger.info("Dictation already active")
                print("✅ 音声入力①は既にアクティブです")
                return True
            
            logger.info("Starting native dictation...")
            print("🎤 macOS音声入力を開始しています...")
            
            # 方法1: 右コマンドキー2回押し
            print("方法1: コマンドキー2回押しを試行中...")
            for i in range(2):
                print(f"コマンドキー押下 {i+1}/2")
                pyautogui.keyDown('cmd')
                time.sleep(0.05)
                pyautogui.keyUp('cmd')
                if i == 0:
                    time.sleep(0.3)
            
            print("音声入力の起動を待機中...")
            time.sleep(2)
            
            if self.check_dictation_status():
                print("✅ 音声入力①が起動しました（コマンドキー方式）")
                return True
            
            # 方法2: fnキー2回押し（代替方法）
            print("方法2: fnキー2回押しを試行中...")
            for i in range(2):
                print(f"fnキー押下 {i+1}/2")
                pyautogui.keyDown('fn')
                time.sleep(0.05)
                pyautogui.keyUp('fn')
                if i == 0:
                    time.sleep(0.3)
            
            time.sleep(2)
            
            if self.check_dictation_status():
                print("✅ 音声入力①が起動しました（fnキー方式）")
                return True
            
            # 方法3: 手動起動を案内
            print("\n❌ 自動起動に失敗しました")
            print("📝 手動で音声入力を起動してください:")
            print("   - システム環境設定 > キーボード > 音声入力")
            print("   - 設定されたショートカットを確認")
            print("   - 手動でショートカットを実行")
            print("\n⏳ 手動起動後、30秒間確認を続けます...")
            
            # 手動起動を30秒間待機
            for attempt in range(30):
                time.sleep(1)
                if self.check_dictation_status():
                    print(f"✅ 音声入力①が起動しました（手動起動、{attempt+1}秒後）")
                    return True
                if attempt % 5 == 0:
                    print(f"確認中... {attempt+1}/30秒")
            
            print("❌ 音声入力①の起動を確認できませんでした")
            return False
            
        except Exception as e:
            logger.error(f"Failed to start dictation: {e}")
            print(f"❌ 音声入力①開始エラー: {e}")
            return False
    
    def stop_dictation(self) -> bool:
        """純正音声入力を停止（コマンドキー2回）"""
        try:
            if not self.check_dictation_status():
                logger.info("Dictation not active")
                return True
            
            logger.info("Stopping native dictation...")
            
            # コマンドキーを2回押下
            for i in range(2):
                pyautogui.keyDown('cmd')
                time.sleep(0.05)
                pyautogui.keyUp('cmd')
                if i == 0:
                    time.sleep(0.3)
            
            # 停止確認
            time.sleep(1)
            return not self.check_dictation_status()
            
        except Exception as e:
            logger.error(f"Failed to stop dictation: {e}")
            return False

class EnterKeyMonitor:
    """Enterキー押下の監視"""
    
    def __init__(self):
        self.enter_pressed = False
        self.monitoring = False
    
    def start_monitoring(self):
        """Enterキー監視を開始"""
        self.enter_pressed = False
        self.monitoring = True
        logger.info("Started monitoring Enter key")
    
    def stop_monitoring(self):
        """Enterキー監視を停止"""
        self.monitoring = False
        logger.info("Stopped monitoring Enter key")
    
    def check_enter_pressed(self) -> bool:
        """Enterキーが押されたかチェック（簡易実装）"""
        # 注意: より正確な実装には低レベルキーフックが必要
        # 現在は時間ベースの推定を使用
        return self.enter_pressed
    
    def wait_for_enter(self, timeout: int = 60) -> bool:
        """Enterキー押下を待機"""
        logger.info("Waiting for Enter key press...")
        
        self.start_monitoring()
        start_time = time.time()
        
        while time.time() - start_time < timeout and self.monitoring:
            # 実際の実装では、キーボードフックやシステムイベント監視を使用
            # ここでは音声入力の停止を検出してEnter押下と推定
            if not NativeDictationController().check_dictation_status():
                logger.info("Dictation stopped - assuming Enter was pressed")
                self.stop_monitoring()
                return True
            
            time.sleep(0.5)
        
        self.stop_monitoring()
        logger.warning("Enter key timeout")
        return False

class AdvancedVoiceChatBot:
    """高度なVoice Chat Bot"""
    
    def __init__(self):
        self.voice_commands = VoiceCommandRecognizer()
        self.response_extractor = ChatGPTResponseExtractor()
        self.dictation_controller = NativeDictationController()
        self.enter_monitor = EnterKeyMonitor()
        self.is_running = False
        
        logger.info("AdvancedVoiceChatBot initialized")
    
    def speak_text(self, text: str) -> None:
        """テキストを読み上げ"""
        try:
            logger.info(f"Speaking: {text[:50]}...")
            print(f"🔊 読み上げ: {text[:50]}...")
            
            # sayコマンドを非同期で実行
            process = subprocess.Popen(['say', text])
            
            # 読み上げ完了を待機（最大30秒）
            try:
                process.wait(timeout=30)
                logger.info("Speech completed")
                print("✅ 読み上げ完了")
            except subprocess.TimeoutExpired:
                logger.warning("Speech timeout")
                process.kill()
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
        
        # 音声での指示
        setup_message = (
            "ChatGPTアプリのウィンドウを選択し、"
            "チャット入力欄をクリックしてください。"
            "準備ができたら「はい」と言ってください。"
        )
        
        print(f"指示: {setup_message}")
        print("\n🔊 指示を読み上げ中...")
        
        # 読み上げを先に実行
        self.speak_text(setup_message)
        
        print("🎤 準備完了の確認を待機中...")
        # 「はい」の待機
        if self.voice_commands.wait_for_yes_command(timeout=60):
            print("✅ セットアップ完了")
            return True
        else:
            print("❌ セットアップがタイムアウトしました")
            return False
    
    def chat_cycle(self) -> bool:
        """1回のチャットサイクル"""
        try:
            print("\n" + "-"*50)
            print("新しい質問を受付中...")
            
            # 1. 音声入力①（純正）を開始
            if not self.dictation_controller.start_dictation():
                print("❌ 音声入力の開始に失敗しました")
                return False
            
            print("🎤 音声入力中... 質問を話してください")
            
            # 2. Enterキー押下を監視
            if not self.enter_monitor.wait_for_enter(timeout=60):
                print("❌ Enterキーの押下を検出できませんでした")
                self.dictation_controller.stop_dictation()
                return False
            
            print("✅ 質問が送信されました")
            
            # 3. ChatGPTの回答を待機・取得
            print("🤖 ChatGPTの回答を待機中...")
            
            # 回答取得のための一時的な指示
            temp_message = (
                "ChatGPTの回答が完了したら、"
                "回答をコピーして「はい」と言ってください。"
            )
            self.speak_text(temp_message)
            
            if self.voice_commands.wait_for_yes_command(timeout=120):
                response = self.response_extractor.get_response_via_clipboard()
                
                if response:
                    print(f"ChatGPT: {response[:100]}...")
                    
                    # 4. 回答を読み上げ
                    print("🔊 回答を読み上げ中...")
                    self.speak_text(response)
                    
                    print("✅ 読み上げ完了")
                    return True
                else:
                    print("❌ 回答を取得できませんでした")
                    return False
            else:
                print("❌ 回答待機がタイムアウトしました")
                return False
                
        except Exception as e:
            logger.error(f"Error in chat cycle: {e}")
            return False
    
    def continuation_check(self) -> bool:
        """継続確認"""
        continue_message = "次の質問をしますか？はいかいいえで答えてください。"
        print(f"\n{continue_message}")
        self.speak_text(continue_message)
        
        return self.voice_commands.wait_for_yes_command(timeout=30)
    
    def main_loop(self) -> None:
        """メインループ"""
        try:
            # セットアップフェーズ
            if not self.setup_phase():
                print("セットアップに失敗しました。終了します。")
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
                    
                    if not self.voice_commands.wait_for_yes_command(timeout=20):
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
        logger.info("AdvancedVoiceChatBot stopped")

def check_system_requirements():
    """システム要件とmacOS設定の確認"""
    print("\n🔍 システム要件チェック")
    print("="*40)
    
    # 1. アクセシビリティ権限の確認
    if ACCESSIBILITY_AVAILABLE:
        print("✅ macOS Accessibility フレームワーク: 利用可能")
    else:
        print("❌ macOS Accessibility フレームワーク: 利用不可")
    
    # 2. 音声関連プロセスの確認
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        dictation_processes = ['DictationIM', 'SpeechRecognitionServer']
        found_processes = []
        
        for process in dictation_processes:
            if process in result.stdout:
                found_processes.append(process)
        
        if found_processes:
            print(f"✅ 音声入力プロセス: {', '.join(found_processes)}")
        else:
            print("⚠️ 音声入力プロセス: 検出されませんでした")
            
    except Exception as e:
        print(f"❌ プロセス確認エラー: {e}")
    
    # 3. sayコマンドの確認
    try:
        result = subprocess.run(['say', '--version'], capture_output=True, text=True, timeout=5)
        print("✅ macOS音声合成: 利用可能")
    except Exception as e:
        print(f"❌ macOS音声合成: {e}")
    
    # 4. PyAutoGUIの確認
    try:
        import pyautogui
        print("✅ PyAutoGUI: 利用可能")
    except Exception as e:
        print(f"❌ PyAutoGUI: {e}")
    
    print("\n📋 必要な設定:")
    print("1. システム環境設定 > キーボード > 音声入力 = オン")
    print("2. ショートカット = 右コマンドキーを2回押す")
    print("3. システム環境設定 > アクセシビリティ権限 = 付与")
    print("4. ChatGPTアプリを起動してチャット画面を開く")
    print("")

def main():
    """メイン関数"""
    print("Advanced VoiceChatBot for macOS ChatGPT")
    print("======================================")
    print("機能:")
    print("- 音声入力①: macOS純正（ChatGPT入力用）")
    print("- 音声入力②: Python音声認識（制御用）") 
    print("- Accessibility API: ChatGPT回答取得")
    print("")
    
    # システム要件チェック
    check_system_requirements()
    
    print("事前準備:")
    print("1. ChatGPTアプリを起動")
    print("2. マイクの使用許可")
    print("3. アクセシビリティ権限の付与")
    print("")
    
    input("準備完了後、Enterキーを押してください...")
    
    try:
        bot = AdvancedVoiceChatBot()
        bot.main_loop()
    except Exception as e:
        logger.error(f"Failed to start AdvancedVoiceChatBot: {e}")
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
