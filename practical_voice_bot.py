#!/usr/bin/env python3
"""
実用的なVoice Chat Bot - 改良版
音声入力の自然な完了を待つ方式
"""

import time
import pyautogui
import subprocess
import logging
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PracticalVoiceChatBot:
    def __init__(self):
        """改良版VoiceChatBotの初期化"""
        self.is_running = False
        self.voice_input_active = False
        
        # pyautoguiの設定
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        
        logger.info("PracticalVoiceChatBot initialized")
    
    def check_voice_input_status(self) -> bool:
        """音声入力の状態をチェック"""
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            voice_processes = ['DictationIM', 'SpeechRecognitionServer', 'Dictation']
            
            for process in voice_processes:
                if process in result.stdout:
                    self.voice_input_active = True
                    return True
            
            self.voice_input_active = False
            return False
            
        except Exception as e:
            logger.error(f"Failed to check voice input status: {e}")
            return False
    
    def trigger_voice_input(self) -> bool:
        """音声入力をトリガー（複数の方法を試行）"""
        try:
            logger.info("Triggering voice input...")
            
            # 現在音声入力が有効かチェック
            if self.check_voice_input_status():
                logger.info("Voice input already active")
                return True
            
            # 方法1: 右コマンドキー2回
            try:
                for i in range(2):
                    pyautogui.keyDown('cmd')
                    time.sleep(0.05)
                    pyautogui.keyUp('cmd')
                    if i == 0:
                        time.sleep(0.3)
                
                time.sleep(1.5)
                if self.check_voice_input_status():
                    logger.info("Voice input triggered successfully (cmd method)")
                    return True
            except Exception as e:
                logger.warning(f"cmd method failed: {e}")
            
            # 方法2: fnキー2回
            try:
                for i in range(2):
                    pyautogui.keyDown('fn')
                    time.sleep(0.05)
                    pyautogui.keyUp('fn')
                    if i == 0:
                        time.sleep(0.3)
                
                time.sleep(1.5)
                if self.check_voice_input_status():
                    logger.info("Voice input triggered successfully (fn method)")
                    return True
            except Exception as e:
                logger.warning(f"fn method failed: {e}")
            
            logger.warning("Failed to trigger voice input")
            return False
                
        except Exception as e:
            logger.error(f"Error triggering voice input: {e}")
            return False
    
    def stop_voice_input(self) -> bool:
        """音声入力を停止（右コマンドキー2回）"""
        try:
            if self.check_voice_input_status():
                logger.info("Stopping voice input with right cmd double-tap...")
                
                # 右コマンドキーを2回押下（停止用）
                for i in range(2):
                    pyautogui.keyDown('cmd')
                    time.sleep(0.05)
                    pyautogui.keyUp('cmd')
                    if i == 0:
                        time.sleep(0.3)
                
                # 停止確認
                time.sleep(1)
                if not self.check_voice_input_status():
                    logger.info("Voice input stopped successfully")
                    return True
                else:
                    logger.warning("Voice input still active after stop attempt")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop voice input: {e}")
            return False
    
    def wait_for_voice_input_natural_completion(self, timeout: int = 60) -> bool:
        """音声入力の自然な完了を待機"""
        logger.info("Waiting for voice input to complete naturally...")
        start_time = time.time()
        
        # 音声入力が有効になるまで少し待機
        for _ in range(10):
            if self.check_voice_input_status():
                break
            time.sleep(0.5)
        
        if not self.check_voice_input_status():
            logger.warning("Voice input not detected")
            return False
        
        logger.info("Voice input detected, waiting for completion...")
        
        # 音声入力が停止するまで待機
        while time.time() - start_time < timeout:
            if not self.check_voice_input_status():
                logger.info("Voice input completed naturally")
                return True
            time.sleep(0.5)
        
        logger.warning("Voice input timeout - still active")
        return False
    
    def speak_text(self, text: str) -> None:
        """テキストを読み上げ（sayコマンド使用）"""
        try:
            logger.info(f"Speaking: {text[:50]}...")
            subprocess.run(['say', text], check=False)
            logger.info("Speech completed")
            
        except Exception as e:
            logger.error(f"Speech failed: {e}")
    
    def get_chatgpt_response(self) -> Optional[str]:
        """
        ChatGPTの返答を取得（プレースホルダー）
        実際の実装では、Accessibility APIやスクリーンスクレイピングを使用
        """
        logger.info("Getting ChatGPT response...")
        time.sleep(2)  # ChatGPTの応答を模擬
        return "これはテスト応答です。実際の実装ではChatGPTの返答を取得します。"
    
    def interactive_session(self) -> None:
        """対話型セッション"""
        logger.info("Interactive voice chat session started")
        self.is_running = True
        
        try:
            while self.is_running:
                print("\n" + "="*50)
                print("Voice Chat Session")
                print("="*50)
                print("準備ができたらEnterキーを押してください（q=終了）")
                
                user_input = input().strip()
                if user_input.lower() == 'q':
                    break
                
                # 1. 音声入力をトリガー
                print("音声入力を開始します...")
                if not self.trigger_voice_input():
                    print("❌ 音声入力の開始に失敗しました")
                    print("手動でmacOSの音声入力を起動してください")
                    input("音声入力を開始したらEnterキーを押してください...")
                
                # 2. 音声入力の完了を待機
                print("🎤 音声入力中...")
                print("話し終わったら自然に停止するか、別のターミナルで手動停止してください")
                
                if self.wait_for_voice_input_natural_completion():
                    print("✅ 音声入力が完了しました")
                else:
                    print("⚠️ 音声入力がまだアクティブです")
                    print("手動で音声入力を停止しますか？ (y/n)")
                    if input().lower() == 'y':
                        if self.stop_voice_input():
                            print("✅ 音声入力を手動停止しました")
                        else:
                            print("❌ 音声入力の停止に失敗しました")
                
                # 3. ChatGPTの返答を待機・取得
                print("🤖 ChatGPTの返答を取得中...")
                response = self.get_chatgpt_response()
                
                if response:
                    print(f"ChatGPT: {response}")
                    
                    # 4. 返答を読み上げ
                    print("🔊 返答を読み上げ中...")
                    self.speak_text(response)
                    print("✅ 読み上げ完了")
                else:
                    print("❌ ChatGPTの返答を取得できませんでした")
        
        except KeyboardInterrupt:
            logger.info("User interrupted")
        except Exception as e:
            logger.error(f"Error in interactive session: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self) -> None:
        """クリーンアップ処理"""
        self.is_running = False
        logger.info("PracticalVoiceChatBot stopped")

def main():
    """メイン関数"""
    print("Practical VoiceChatBot for macOS ChatGPT")
    print("========================================")
    print("改良版: 音声入力の自然な完了を待つ方式")
    print("")
    print("事前準備:")
    print("1. ChatGPTアプリを起動してチャット画面を開く")
    print("2. macOSの音声入力設定を確認")
    print("3. アクセシビリティ権限を付与")
    print("")
    
    try:
        bot = PracticalVoiceChatBot()
        bot.interactive_session()
    except Exception as e:
        logger.error(f"Failed to start PracticalVoiceChatBot: {e}")
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
