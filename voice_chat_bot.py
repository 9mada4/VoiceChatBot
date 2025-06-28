#!/usr/bin/env python3
"""
Voice Chat Bot for macOS ChatGPT App
音声でChatGPTアプリを操作するためのAutomationツール
"""

import time
import pyautogui
import pyttsx3
import threading
import logging
from typing import Optional
import subprocess
import re

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VoiceChatBot:
    def __init__(self):
        """VoiceChatBotの初期化"""
        self.tts_engine = None
        try:
            self.tts_engine = self._init_tts()
        except Exception as e:
            logger.warning(f"TTS engine initialization failed, will use fallback: {e}")
        
        self.is_running = False
        self.voice_input_active = False
        
        # pyautoguiの設定
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        
        logger.info("VoiceChatBot initialized")
    
    def _init_tts(self) -> pyttsx3.Engine:
        """TTSエンジンの初期化"""
        try:
            # macOS用のTTSエンジンを初期化
            engine = pyttsx3.init('nsss')  # macOS用のドライバーを明示的に指定
            
            # 利用可能な音声を取得
            voices = engine.getProperty('voices')
            logger.info(f"Available voices: {len(voices) if voices else 0}")
            
            # 日本語音声の設定を試行
            if voices:
                for voice in voices:
                    voice_name = voice.name if hasattr(voice, 'name') else str(voice)
                    logger.info(f"Voice: {voice_name}")
                    if 'japan' in voice_name.lower() or 'kyoko' in voice_name.lower() or 'haruka' in voice_name.lower():
                        engine.setProperty('voice', voice.id)
                        logger.info(f"Selected Japanese voice: {voice_name}")
                        break
            
            # 読み上げ速度の設定
            engine.setProperty('rate', 180)
            
            logger.info("TTS engine initialized successfully")
            return engine
            
        except Exception as e:
            logger.error(f"TTS initialization failed: {e}")
            # フォールバック: デフォルトドライバーを試行
            try:
                engine = pyttsx3.init()
                logger.info("TTS engine initialized with default driver")
                return engine
            except Exception as e2:
                logger.error(f"Fallback TTS initialization also failed: {e2}")
                raise
    
    def check_voice_input_status(self) -> bool:
        """
        音声入力の状態をチェック
        macOSの音声入力プロセスを監視
        """
        try:
            # 音声入力関連のプロセスをチェック
            result = subprocess.run(
                ['ps', 'aux'], 
                capture_output=True, 
                text=True
            )
            
            # DictationまたはSpeechRecognitionServerが動いているかチェック
            voice_processes = [
                'DictationIM',
                'SpeechRecognitionServer',
                'Dictation'
            ]
            
            for process in voice_processes:
                if process in result.stdout:
                    self.voice_input_active = True
                    logger.info(f"Voice input detected: {process}")
                    return True
            
            self.voice_input_active = False
            return False
            
        except Exception as e:
            logger.error(f"Failed to check voice input status: {e}")
            return False
    
    def stop_voice_input(self) -> bool:
        """音声入力を停止（右コマンドキー2回）"""
        try:
            if self.check_voice_input_status():
                logger.info("Stopping voice input with right cmd double-tap...")
                
                # 右コマンドキーを2回押下（停止用）
                pyautogui.keyDown('cmd')
                time.sleep(0.05)
                pyautogui.keyUp('cmd')
                time.sleep(0.3)
                pyautogui.keyDown('cmd')
                time.sleep(0.05)
                pyautogui.keyUp('cmd')
                
                # 停止確認
                time.sleep(1)
                if not self.check_voice_input_status():
                    logger.info("Voice input stopped successfully")
                    return True
                else:
                    # もう一度試行
                    logger.info("Trying to stop voice input again...")
                    pyautogui.keyDown('cmd')
                    time.sleep(0.05)
                    pyautogui.keyUp('cmd')
                    time.sleep(0.3)
                    pyautogui.keyDown('cmd')
                    time.sleep(0.05)
                    pyautogui.keyUp('cmd')
                    
                    time.sleep(1)
                    return not self.check_voice_input_status()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop voice input: {e}")
            return False
    
    def start_voice_input(self) -> bool:
        """音声入力を開始（右コマンドキー2回）"""
        try:
            # 既に音声入力が有効な場合は停止
            if self.check_voice_input_status():
                self.stop_voice_input()
                time.sleep(1)
            
            # 右コマンドキーを2回押下（より正確な実装）
            logger.info("Starting voice input...")
            
            # 方法1: 右コマンドキー（option+cmd）を試行
            try:
                # macOSでの右コマンドキーは'cmd'または'right cmd'
                pyautogui.keyDown('cmd')
                time.sleep(0.05)
                pyautogui.keyUp('cmd')
                time.sleep(0.3)  # キー間の間隔を少し長く
                pyautogui.keyDown('cmd')
                time.sleep(0.05)
                pyautogui.keyUp('cmd')
                
                # 音声入力の起動確認
                time.sleep(1.5)  # 起動までの待機時間を延長
                if self.check_voice_input_status():
                    logger.info("Voice input started successfully")
                    return True
                
            except Exception as e:
                logger.warning(f"Method 1 failed: {e}")
            
            # 方法2: fn+fn のダブルタップを試行（代替方法）
            try:
                logger.info("Trying alternative method (fn+fn)...")
                pyautogui.keyDown('fn')
                time.sleep(0.05)
                pyautogui.keyUp('fn')
                time.sleep(0.3)
                pyautogui.keyDown('fn')
                time.sleep(0.05)
                pyautogui.keyUp('fn')
                
                time.sleep(1.5)
                if self.check_voice_input_status():
                    logger.info("Voice input started successfully (fn method)")
                    return True
                    
            except Exception as e:
                logger.warning(f"Method 2 failed: {e}")
            
            logger.warning("Voice input may not have started")
            return False
                
        except Exception as e:
            logger.error(f"Failed to start voice input: {e}")
            return False
    
    def wait_for_input_completion(self, timeout: int = 30) -> bool:
        """音声入力の完了を待機"""
        logger.info("Waiting for voice input completion...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if not self.check_voice_input_status():
                logger.info("Voice input completed")
                return True
            time.sleep(0.5)
        
        logger.warning("Voice input timeout")
        return False
    
    def speak_text(self, text: str) -> None:
        """テキストを読み上げ"""
        try:
            logger.info(f"Speaking: {text[:50]}...")
            
            # pyttsx3での読み上げを試行
            if hasattr(self, 'tts_engine') and self.tts_engine:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
                logger.info("Speech completed (pyttsx3)")
            else:
                # フォールバック: macOSのsayコマンドを使用
                logger.info("Using fallback say command")
                subprocess.run(['say', text], check=False)
                logger.info("Speech completed (say command)")
            
        except Exception as e:
            logger.error(f"Speech failed with pyttsx3: {e}")
            try:
                # フォールバック: macOSのsayコマンドを使用
                logger.info("Trying fallback say command")
                subprocess.run(['say', text], check=False)
                logger.info("Speech completed (say command)")
            except Exception as e2:
                logger.error(f"Fallback speech also failed: {e2}")
    
    def get_chatgpt_response(self) -> Optional[str]:
        """
        ChatGPTの返答を取得
        TODO: Accessibility APIまたはスクリーンスクレイピングで実装
        """
        # プレースホルダー実装
        logger.info("Getting ChatGPT response...")
        
        # 現在は手動での実装確認用
        return "この機能は現在開発中です。ChatGPTの返答取得機能を実装してください。"
    
    def main_loop(self) -> None:
        """メインの操作ループ"""
        logger.info("VoiceChatBot started. Press Ctrl+C to exit.")
        self.is_running = True
        
        try:
            while self.is_running:
                print("\n=== Voice Chat Session ===")
                print("音声入力を開始します...")
                
                # 1. 音声入力開始
                if not self.start_voice_input():
                    print("音声入力の開始に失敗しました")
                    continue
                
                # 2. 音声入力完了まで待機
                if not self.wait_for_input_completion():
                    print("音声入力がタイムアウトしました")
                    self.stop_voice_input()
                    continue
                
                print("音声入力が完了しました。ChatGPTの返答を待機中...")
                
                # 3. ChatGPTの返答を待機・取得
                # TODO: 実際の返答検出ロジックを実装
                time.sleep(3)  # 仮の待機時間
                
                response = self.get_chatgpt_response()
                if response:
                    print(f"ChatGPT: {response}")
                    
                    # 4. 返答を読み上げ
                    self.speak_text(response)
                    
                    print("返答の読み上げが完了しました")
                else:
                    print("ChatGPTの返答を取得できませんでした")
                
                # 次のサイクルまで少し待機
                time.sleep(2)
        
        except KeyboardInterrupt:
            logger.info("User interrupted")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self) -> None:
        """クリーンアップ処理"""
        self.is_running = False
        self.stop_voice_input()
        logger.info("VoiceChatBot stopped")

def main():
    """メイン関数"""
    print("VoiceChatBot for macOS ChatGPT App")
    print("===================================")
    print("使用前に以下を確認してください:")
    print("1. ChatGPTアプリが起動していること")
    print("2. チャット画面が開いていること") 
    print("3. macOSの音声入力が有効になっていること")
    print("4. アクセシビリティ権限が付与されていること")
    print("")
    
    input("準備ができたらEnterキーを押してください...")
    
    try:
        bot = VoiceChatBot()
        bot.main_loop()
    except Exception as e:
        logger.error(f"Failed to start VoiceChatBot: {e}")
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
