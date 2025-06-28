#!/usr/bin/env python3
"""
音声入力機能の単体テスト用スクリプト
"""

import time
import pyautogui
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_voice_input_status():
    """音声入力の状態をチェック"""
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        voice_processes = ['DictationIM', 'SpeechRecognitionServer', 'Dictation']
        
        for process in voice_processes:
            if process in result.stdout:
                return True, process
        return False, None
        
    except Exception as e:
        logger.error(f"Failed to check voice input status: {e}")
        return False, None

def test_voice_input_control():
    """音声入力制御のテスト"""
    print("音声入力制御テスト")
    print("==================")
    
    # 現在の状態確認
    active, process = check_voice_input_status()
    print(f"現在の音声入力状態: {'有効' if active else '無効'}")
    if active:
        print(f"検出されたプロセス: {process}")
    
    print("\n音声入力を手動で起動してください")
    print("macOSの設定に従って：")
    print("- 右コマンドキー2回押し")
    print("- または fn キー2回押し")
    print("- または設定されたショートカット")
    
    print("音声入力を起動したら、30秒待機します...")
    time.sleep(30)  # input() の代わりに固定時間待機
    
    # 起動確認
    active, process = check_voice_input_status()
    if active:
        print(f"✅ 音声入力が検出されました: {process}")
        
        print("\n5秒後に自動停止を試行します...")
        time.sleep(5)
        
        # 停止テスト
        print("右コマンド2回押しで停止を試行...")
        # 右コマンドキーを2回押下
        pyautogui.keyDown('cmd')
        time.sleep(0.05)
        pyautogui.keyUp('cmd')
        time.sleep(0.3)
        pyautogui.keyDown('cmd')
        time.sleep(0.05)
        pyautogui.keyUp('cmd')
        
        time.sleep(1)
        
        active, process = check_voice_input_status()
        if not active:
            print("✅ 右コマンド2回押しで音声入力が正常に停止されました")
        else:
            print("❌ 右コマンド2回押しでは停止できませんでした")
            print("（macOSの設定により異なる場合があります）")
    else:
        print("❌ 音声入力が検出されませんでした")
    
    print("\nテスト完了")

def test_say_command():
    """sayコマンドのテスト"""
    print("\nmacOS sayコマンドテスト")
    print("=======================")
    
    test_text = "こんにちは。音声合成のテストです。"
    print(f"テキスト: {test_text}")
    
    try:
        subprocess.run(['say', test_text], check=True)
        print("✅ sayコマンドが正常に動作しました")
    except Exception as e:
        print(f"❌ sayコマンドでエラー: {e}")

def main():
    print("VoiceChatBot 音声機能テスト")
    print("===========================")
    
    # sayコマンドテスト
    test_say_command()
    
    # 音声入力制御テスト
    test_voice_input_control()

if __name__ == "__main__":
    main()
