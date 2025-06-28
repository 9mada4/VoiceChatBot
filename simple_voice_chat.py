#!/usr/bin/env python3
"""
Simple Voice Chat Bot for macOS
新しいウィンドウで音声入力を行うシンプル版
"""

import time
import subprocess
import logging
import os
from typing import Optional

# macOS用のインポート
try:
    from Quartz.CoreGraphics import CGEventCreateKeyboardEvent, CGEventPost, kCGHIDEventTap
    QUARTZ_AVAILABLE = True
except ImportError:
    QUARTZ_AVAILABLE = False
    print("Warning: Quartz not available")

# 音声認識用のインポート
try:
    from faster_whisper import WhisperModel
    VOICE_RECOGNITION_AVAILABLE = True
except ImportError:
    VOICE_RECOGNITION_AVAILABLE = False
    print("Warning: Voice recognition not available")

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleVoiceChatBot:
    """シンプルな音声チャットボット"""
    
    def __init__(self):
        self.whisper_model = None
        if VOICE_RECOGNITION_AVAILABLE:
            try:
                self.whisper_model = WhisperModel("tiny", device="cpu")
                logger.info("Whisper model loaded")
            except Exception as e:
                logger.error(f"Failed to load Whisper: {e}")
    
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
        """macOS純正音声入力を開始"""
        if not QUARTZ_AVAILABLE:
            print("💡 手動で音声入力を開始してください：右コマンドキーを2回押す")
            return False
        
        try:
            # 右コマンドキー（keycode 54）を2回押す
            RIGHT_COMMAND_KEY = 54
            
            print("🎤 音声入力を開始しています...")
            
            # 1回目
            if not self.press_key_quartz(RIGHT_COMMAND_KEY):
                return False
            time.sleep(0.1)
            
            # 2回目
            if not self.press_key_quartz(RIGHT_COMMAND_KEY):
                return False
            
            print("✅ 音声入力が開始されました")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start dictation: {e}")
            return False
    
    def open_text_editor(self) -> bool:
        """新しいテキストエディタウィンドウを開く"""
        try:
            # TextEditを開く
            subprocess.run(['open', '-a', 'TextEdit'], check=True)
            time.sleep(2)  # ウィンドウが開くまで待機
            print("✅ TextEditが開かれました")
            return True
        except Exception as e:
            logger.error(f"Failed to open TextEdit: {e}")
            return False
    
    def get_clipboard_content(self) -> Optional[str]:
        """クリップボードの内容を取得"""
        try:
            result = subprocess.run(['pbpaste'], capture_output=True, text=True)
            content = result.stdout.strip()
            return content if content else None
        except Exception as e:
            logger.error(f"Failed to get clipboard: {e}")
            return None
    
    def speak_text(self, text: str) -> None:
        """テキストを読み上げ"""
        try:
            print(f"🔊 読み上げ中: {text[:50]}...")
            subprocess.run(['say', text], timeout=30, check=False)
            print("✅ 読み上げ完了")
        except Exception as e:
            logger.error(f"Speech failed: {e}")
            print(f"📝 メッセージ: {text}")
    
    def wait_for_voice_input(self) -> Optional[str]:
        """音声入力の完了を待機"""
        print("\n" + "="*50)
        print("音声入力手順:")
        print("1. TextEditウィンドウがアクティブであることを確認")
        print("2. 音声で質問を話してください")
        print("3. 音声入力が終了したら、テキストを全選択（Cmd+A）")
        print("4. コピー（Cmd+C）")
        print("5. Enterキーを押して次に進んでください")
        print("="*50)
        
        input("準備ができたらEnterキーを押してください...")
        
        # クリップボードから質問を取得
        question = self.get_clipboard_content()
        if question:
            print(f"📝 質問を取得しました: {question}")
            return question
        else:
            print("❌ 質問を取得できませんでした")
            return None
    
    def wait_for_chatgpt_response(self) -> Optional[str]:
        """ChatGPTの回答を待機"""
        print("\n" + "="*50)
        print("ChatGPT回答取得手順:")
        print("1. 上記の質問をChatGPTに貼り付けて送信")
        print("2. ChatGPTの回答が完了するまで待機")
        print("3. 回答を全選択（Cmd+A）してコピー（Cmd+C）")
        print("4. Enterキーを押して読み上げを開始")
        print("="*50)
        
        input("ChatGPTの回答をコピーしたらEnterキーを押してください...")
        
        # クリップボードから回答を取得
        response = self.get_clipboard_content()
        if response:
            print(f"📝 回答を取得しました: {response[:100]}...")
            return response
        else:
            print("❌ 回答を取得できませんでした")
            return None
    
    def run_chat_cycle(self) -> bool:
        """1回のチャットサイクルを実行"""
        try:
            # 1. テキストエディタを開く
            if not self.open_text_editor():
                return False
            
            # 2. 音声入力を開始
            if not self.start_dictation():
                return False
            
            # 3. 音声入力の完了を待機
            question = self.wait_for_voice_input()
            if not question:
                return False
            
            # 4. ChatGPTの回答を待機
            response = self.wait_for_chatgpt_response()
            if not response:
                return False
            
            # 5. 回答を読み上げ
            self.speak_text(response)
            
            return True
            
        except Exception as e:
            logger.error(f"Chat cycle error: {e}")
            return False
    
    def main_loop(self):
        """メインループ"""
        print("Simple Voice Chat Bot for macOS")
        print("================================")
        print("機能:")
        print("- 新しいTextEditウィンドウで音声入力")
        print("- 質問をクリップボード経由でChatGPTに転送")
        print("- ChatGPTの回答を自動読み上げ")
        print("")
        
        try:
            while True:
                print("\n🚀 新しいチャットサイクルを開始します...")
                
                # チャットサイクル実行
                success = self.run_chat_cycle()
                
                if success:
                    # 継続確認
                    continue_chat = input("\n次の質問をしますか？ (y/n): ").lower().strip()
                    if continue_chat not in ['y', 'yes', 'はい']:
                        print("👋 チャットを終了します")
                        break
                else:
                    print("❌ エラーが発生しました")
                    retry = input("再試行しますか？ (y/n): ").lower().strip()
                    if retry not in ['y', 'yes', 'はい']:
                        break
        
        except KeyboardInterrupt:
            print("\n👋 ユーザーによって終了されました")
        except Exception as e:
            logger.error(f"Main loop error: {e}")

def main():
    """メイン関数"""
    bot = SimpleVoiceChatBot()
    bot.main_loop()

if __name__ == "__main__":
    main()
