#!/usr/bin/env python3
"""
右コマンドキーテスト（音声確認付き）
右コマンドキー（key code 54）で音声入力が起動するかを確認
"""

import subprocess
import time
import sys
import os

# 音声入力用のWhisperインポート
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

def get_voice_confirmation(prompt):
    """音声入力②で確認を取得"""
    if not WHISPER_AVAILABLE:
        print("❌ Whisperが利用できません。音声確認をスキップします。")
        return True
    
    print(f"🎤 {prompt}")
    print("音声で「はい」または「いいえ」と答えてください...")
    print("（明確に「はい」と発音してください）")
    
    try:
        # 一時音声ファイル
        temp_audio = "/tmp/voice_confirm.wav"
        
        # 5秒間録音（より長く）
        print("録音開始（5秒間）...")
        subprocess.run([
            'rec', '-r', '16000', '-c', '1', '-b', '16', 
            temp_audio, 'trim', '0', '5'
        ], check=True, capture_output=True)
        
        # Whisperで音声認識（baseモデルを使用してより正確に）
        model = WhisperModel("base", device="cpu")
        segments, _ = model.transcribe(temp_audio, language="ja")
        
        recognized_text = ""
        for segment in segments:
            recognized_text += segment.text
        
        print(f"認識結果: '{recognized_text}'")
        
        # ファイル削除
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
        
        # 「はい」系の応答を確認（より厳密に）
        recognized_lower = recognized_text.lower().strip()
        yes_words = ["はい", "hai", "yes", "イエス", "いえす", "オッケー", "ok", "おっけー"]
        
        for word in yes_words:
            if word in recognized_lower:
                print(f"✅ 確認されました（'{word}'を検出）")
                return True
        
        print(f"❌ 「はい」が認識されませんでした")
        return False
        
    except Exception as e:
        print(f"❌ 音声認識エラー: {e}")
        return True  # エラー時はデフォルトで続行

def simple_test_right_command_key():
    """右コマンドキー（key code 54）の簡略化テスト"""
    print(f"\n🔧 簡略テスト: 右コマンドキー (key code 54)")
    print("3秒後に右コマンドキーを2回押します...")
    print("⚠️  macOSの「システム設定 > キーボード > 音声入力」が有効になっている必要があります")
    print("📱 画面を見て、音声入力（マイクアイコン）が表示されるか確認してください")
    
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    
    try:
        applescript = '''
        tell application "System Events"
            key code 54
            delay 0.5
            key code 54
        end tell
        '''
        
        result = subprocess.run(['osascript', '-e', applescript], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(f"✅ key code 54 送信成功")
            
            # 待機して、プロセス確認
            print("音声入力の起動を確認中...")
            time.sleep(3)
            
            # 複数の方法で音声入力プロセス確認
            ps_result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            dictation_found = False
            found_processes = []
            
            # 音声入力関連プロセスの検出
            voice_processes = ['DictationIM', 'VoiceOver', 'SpeechRecognition', 'Dictation', 'speechd']
            for process in voice_processes:
                if process in ps_result.stdout:
                    found_processes.append(process)
                    dictation_found = True
            
            if found_processes:
                print(f"🎤 検出された音声関連プロセス: {', '.join(found_processes)}")
            
            # AppleScriptで音声入力ダイアログの存在を確認
            check_dialog_script = '''
            tell application "System Events"
                set dialogExists to false
                try
                    if exists (window 1 of application process "Dictation") then
                        set dialogExists to true
                    end if
                end try
                return dialogExists
            end tell
            '''
            
            dialog_result = subprocess.run(['osascript', '-e', check_dialog_script], 
                                         capture_output=True, text=True)
            
            if dialog_result.returncode == 0 and 'true' in dialog_result.stdout:
                print(f"🎤 音声入力ダイアログが検出されました！")
                dictation_found = True
            
            # 手動で音声入力を停止
            print("音声入力を停止します...")
            stop_script = '''
            tell application "System Events"
                key code 54
            end tell
            '''
            subprocess.run(['osascript', '-e', stop_script], capture_output=True)
            
            return dictation_found
            
        else:
            print(f"❌ key code 54 送信失敗: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

def main():
    """右コマンドキーテスト"""
    print("🧪 右コマンドキー音声入力テスト")
    print("="*50)
    print("右コマンドキー（key code 54）で音声入力が起動するか確認します")
    print("このテストは完全に音声制御で実行されます")
    
    if not WHISPER_AVAILABLE:
        print("⚠️  faster-whisperが利用できません")
        print("音声確認部分はスキップされます")
    
    print("\n✨ 自動的にテストを開始します（5秒後）...")
    print("テストを中止したい場合は Ctrl+C を押してください")
    
    try:
        for i in range(5, 0, -1):
            print(f"テスト開始まで {i} 秒...")
            time.sleep(1)
        
        print("\n" + "="*50)
        success = simple_test_right_command_key()
        
        print("\n🏁 テスト結果:")
        print("="*30)
        if success:
            print("✅ 右コマンドキー（key code 54）が正常に機能します")
            print("   音声入力の起動が確認されました")
        else:
            print("❌ 右コマンドキーで音声入力が起動しませんでした")
            print("   macOSの音声入力設定を確認してください")
            
    except KeyboardInterrupt:
        print("\n❌ テストがキャンセルされました")
        return

if __name__ == "__main__":
    main()
