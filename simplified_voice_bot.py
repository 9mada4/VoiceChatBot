#!/usr/bin/env python3
"""
Simplified Advanced Voice Chat Bot for macOS ChatGPT App
Python 3.13対応版：音声認識の代わりにキーボード入力を使用
"""

import time
import pyautogui
import subprocess
import logging
import threading
from typing import Optional
from datetime import datetime

# macOS用のインポート
try:
    from AppKit import NSWorkspace, NSApplication
    from Cocoa import NSPasteboard, NSStringPboardType
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

class SimpleCommandRecognizer:
    """簡易コマンド認識（キーボード入力）"""
    
    def __init__(self):
        logger.info("SimpleCommandRecognizer initialized (keyboard input mode)")
    
    def wait_for_yes_command(self, timeout: int = 30) -> bool:
        """「はい」コマンドを待機（キーボード入力）"""
        print("「はい」なら 'y' + Enter、「いいえ」なら 'n' + Enter を押してください:")
        
        try:
            user_input = input().strip().lower()
            return user_input in ['y', 'yes', 'はい', 'hai']
        except KeyboardInterrupt:
            return False

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
            if not ACCESSIBILITY_AVAILABLE:
                # Fallback: システムのpbpasteコマンドを使用
                result = subprocess.run(['pbpaste'], capture_output=True, text=True)
                content = result.stdout.strip()
            else:
                pasteboard = NSPasteboard.generalPasteboard()
                content = pasteboard.stringForType_(NSStringPboardType)
            
            if content and content != self.last_response:
                self.last_response = content
                return content
            
            return None
            
        except Exception as e:
            logger.error(f"Clipboard access error: {e}")
            return None
    
    def wait_for_response_ready(self) -> bool:
        """回答準備完了の確認"""
        print("\nChatGPTの回答が完了したら:")
        print("1. 回答全体を選択（Cmd+A）")
        print("2. コピー（Cmd+C）")
        print("3. 'y' + Enter を押してください")
        
        return SimpleCommandRecognizer().wait_for_yes_command()

class NativeDictationController:
    """macOS純正音声入力の制御"""
    
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
        """純正音声入力を開始（コマンドキー2回）"""
        try:
            if self.check_dictation_status():
                logger.info("Dictation already active")
                return True
            
            logger.info("Starting native dictation...")
            
            # コマンドキーを2回押下
            for i in range(2):
                pyautogui.keyDown('cmd')
                time.sleep(0.05)
                pyautogui.keyUp('cmd')
                if i == 0:
                    time.sleep(0.3)
            
            # 起動確認
            time.sleep(1.5)
            return self.check_dictation_status()
            
        except Exception as e:
            logger.error(f"Failed to start dictation: {e}")
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
    
    def wait_for_dictation_completion(self, timeout: int = 60) -> bool:
        """音声入力の完了を待機"""
        logger.info("Waiting for dictation completion...")
        
        start_time = time.time()
        was_active = False
        
        # 音声入力がアクティブになるまで待機
        while time.time() - start_time < 10:
            if self.check_dictation_status():
                was_active = True
                break
            time.sleep(0.5)
        
        if not was_active:
            logger.warning("Dictation never became active")
            return False
        
        # 音声入力が停止するまで待機
        while time.time() - start_time < timeout:
            if not self.check_dictation_status():
                logger.info("Dictation completed")
                return True
            time.sleep(0.5)
        
        logger.warning("Dictation timeout")
        return False

class SimplifiedVoiceChatBot:
    """簡略化されたVoice Chat Bot"""
    
    def __init__(self):
        self.command_recognizer = SimpleCommandRecognizer()
        self.response_extractor = ChatGPTResponseExtractor()
        self.dictation_controller = NativeDictationController()
        self.is_running = False
        
        logger.info("SimplifiedVoiceChatBot initialized")
    
    def speak_text(self, text: str) -> None:
        """テキストを読み上げ"""
        try:
            logger.info(f"Speaking: {text[:50]}...")
            subprocess.run(['say', text], check=False)
            logger.info("Speech completed")
        except Exception as e:
            logger.error(f"Speech failed: {e}")
    
    def setup_phase(self) -> bool:
        """初期セットアップフェーズ"""
        print("\n" + "="*60)
        print("VoiceChatBot セットアップ")
        print("="*60)
        
        # 音声での指示
        setup_message = (
            "ChatGPTアプリのウィンドウを選択し、"
            "チャット入力欄をクリックしてください。"
        )
        
        print(f"指示: {setup_message}")
        self.speak_text(setup_message)
        
        # 準備完了の確認
        print("\n準備ができましたか？")
        return self.command_recognizer.wait_for_yes_command()
    
    def chat_cycle(self) -> bool:
        """1回のチャットサイクル"""
        try:
            print("\n" + "-"*50)
            print("新しい質問を受付中...")
            
            # 1. 音声入力①（純正）を開始
            print("🎤 音声入力を開始します...")
            if not self.dictation_controller.start_dictation():
                print("❌ 音声入力の開始に失敗しました")
                print("手動でコマンドキー2回押しで音声入力を開始してください")
            
            print("音声で質問を話してください（終了したら自動的に送信されます）")
            
            # 2. 音声入力の完了を待機
            if self.dictation_controller.wait_for_dictation_completion():
                print("✅ 質問が送信されました")
            else:
                print("⚠️ 音声入力の完了を確認できませんでした")
                print("手動でEnterキーを押して送信してください")
                input("送信したらEnterキーを押してください...")
            
            # 3. ChatGPTの回答を待機・取得
            print("🤖 ChatGPTの回答を待機中...")
            
            if self.response_extractor.wait_for_response_ready():
                response = self.response_extractor.get_response_via_clipboard()
                
                if response:
                    print(f"\nChatGPT回答:")
                    print("-" * 40)
                    print(response)
                    print("-" * 40)
                    
                    # 4. 回答を読み上げ
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
        
        return self.command_recognizer.wait_for_yes_command()
    
    def main_loop(self) -> None:
        """メインループ"""
        try:
            # セットアップフェーズ
            if not self.setup_phase():
                print("セットアップがキャンセルされました。終了します。")
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
                    print("再試行しますか？")
                    
                    if not self.command_recognizer.wait_for_yes_command():
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
        logger.info("SimplifiedVoiceChatBot stopped")

def main():
    """メイン関数"""
    print("Simplified Advanced VoiceChatBot for macOS ChatGPT")
    print("==================================================")
    print("機能:")
    print("- 音声入力①: macOS純正（ChatGPT入力用）")
    print("- 音声入力②: キーボード入力（制御用）") 
    print("- クリップボード: ChatGPT回答取得")
    print("")
    
    print("使用方法:")
    print("1. ChatGPTアプリを起動してチャット画面を開く")
    print("2. このプログラムの指示に従って操作")
    print("3. 音声で質問、手動で回答をコピー")
    print("")
    
    input("準備完了後、Enterキーを押してください...")
    
    try:
        bot = SimplifiedVoiceChatBot()
        bot.main_loop()
    except Exception as e:
        logger.error(f"Failed to start SimplifiedVoiceChatBot: {e}")
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
