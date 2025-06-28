#!/usr/bin/env python3
"""VoiceChatBot テストスイート"""

import sys
import subprocess
import time

def test_dependencies():
    """依存関係テスト"""
    print("\n🧪 依存関係チェック")
    print("="*50)
    
    deps = [
        ("pyautogui", "PyAutoGUI"),
        ("faster_whisper", "faster-whisper"),
        ("AppKit", "macOS AppKit"),
        ("Cocoa", "macOS Cocoa")
    ]
    
    for module, name in deps:
        try:
            __import__(module)
            print(f"✅ {name} - OK")
        except ImportError as e:
            print(f"❌ {name} - エラー: {e}")

def test_commands():
    """コマンドテスト"""
    print("\n🧪 コマンドチェック")
    print("="*50)
    
    for cmd in ["say", "rec", "pbcopy", "pbpaste"]:
        try:
            result = subprocess.run(['which', cmd], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {cmd} - {result.stdout.strip()}")
            else:
                print(f"❌ {cmd} - 見つかりません")
        except Exception as e:
            print(f"❌ {cmd} - エラー: {e}")

def test_right_cmd():
    """右コマンドキーテスト"""
    print("\n🧪 右コマンドキー2回押しテスト")
    print("="*50)
    
    try:
        import pyautogui
        print("3秒後に右コマンドキー2回押し...")
        time.sleep(3)
        
        for i in range(2):
            pyautogui.keyDown('right_cmd')
            time.sleep(0.05)
            pyautogui.keyUp('right_cmd')
            if i == 0:
                time.sleep(0.3)
        
        print("✅ 右コマンドキー実行完了")
        
        # プロセス確認
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        found = []
        for proc in ['DictationIM', 'SpeechRecognitionServer']:
            if proc in result.stdout:
                found.append(proc)
        
        if found:
            print(f"✅ 音声入力プロセス: {', '.join(found)}")
        else:
            print("❌ 音声入力プロセスなし")
            
    except Exception as e:
        print(f"❌ エラー: {e}")

def test_voice_module():
    """VoiceChatBotモジュールテスト"""
    print("\n🧪 VoiceChatBotモジュールテスト")
    print("="*50)
    
    try:
        from voice_chat_bot import VoiceCommandRecognizer, ChatGPTResponseExtractor, NativeDictationController
        print("✅ 全クラスインポート成功")
        
        recognizer = VoiceCommandRecognizer()
        extractor = ChatGPTResponseExtractor()
        controller = NativeDictationController()
        print("✅ 全クラスインスタンス化成功")
        
    except Exception as e:
        print(f"❌ エラー: {e}")

def main():
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        print("1. 依存関係 2. コマンド 3. 右コマンドキー 4. VoiceChatBot")
        choice = input("選択: ")
    
    if choice == "1":
        test_dependencies()
    elif choice == "2":
        test_commands()
    elif choice == "3":
        test_right_cmd()
    elif choice == "4":
        test_voice_module()
    else:
        test_dependencies()
        test_commands()
        test_voice_module()

if __name__ == "__main__":
    main()
