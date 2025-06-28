#!/usr/bin/env python3
"""
macOS音声入力設定確認ツール
"""

import subprocess
import sys

def check_dictation_settings():
    """macOSの音声入力設定を確認"""
    print("🔍 macOS音声入力設定確認")
    print("="*50)
    
    # 音声入力の有効状態を確認
    try:
        print("📋 システム音声入力設定確認中...")
        result = subprocess.run([
            'defaults', 'read', 'com.apple.HIToolbox', 'AppleDictationAutoEnable'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            setting = result.stdout.strip()
            if setting == "1":
                print("✅ 音声入力が有効になっています")
            else:
                print("❌ 音声入力が無効になっています")
                print("   システム環境設定 > キーボード > 音声入力 で有効にしてください")
        else:
            print("⚠️ 音声入力設定を読み取れませんでした")
            
    except Exception as e:
        print(f"❌ 設定確認エラー: {e}")
    
    # ショートカットキー設定を確認
    print("\n📋 音声入力ショートカット設定確認中...")
    try:
        result = subprocess.run([
            'defaults', 'read', 'com.apple.HIToolbox'
        ], capture_output=True, text=True)
        
        if "DictationHotKey" in result.stdout:
            print("✅ 音声入力ショートカットが設定されています")
        else:
            print("⚠️ 音声入力ショートカットが設定されていない可能性があります")
            
    except Exception as e:
        print(f"❌ ショートカット確認エラー: {e}")
    
    # 現在実行中の音声入力関連プロセスを確認
    print("\n📋 音声入力関連プロセス確認中...")
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        dictation_processes = [
            'DictationIM', 'SpeechRecognitionServer', 'AppleSpell', 
            'TextInputMenuAgent', 'com.apple.inputmethod'
        ]
        
        found_processes = []
        for process in dictation_processes:
            if process in result.stdout:
                found_processes.append(process)
        
        if found_processes:
            print(f"✅ 検出されたプロセス: {', '.join(found_processes)}")
        else:
            print("❌ 音声入力関連プロセスが見つかりません")
            
    except Exception as e:
        print(f"❌ プロセス確認エラー: {e}")
    
    print("\n📋 修正提案:")
    print("1. システム環境設定 > キーボード > 音声入力")
    print("2. 「音声入力」を「オン」に設定")
    print("3. ショートカットを「コマンドキーを2回押す」に設定")
    print("4. 「拡張音声入力」も有効にすることを推奨")
    print("5. 言語は「日本語」を選択")

def check_keyboard_layout():
    """キーボード配列を確認"""
    print("\n🔍 キーボード配列確認")
    print("="*30)
    
    try:
        result = subprocess.run([
            'defaults', 'read', 'com.apple.HIToolbox', 'AppleCurrentKeyboardLayoutInputSourceID'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            layout = result.stdout.strip()
            print(f"📋 現在のキーボード配列: {layout}")
            
            if "Japanese" in layout or "JIS" in layout:
                print("✅ JIS配列が検出されました")
                print("   右コマンドキー: key code 54")
                print("   左コマンドキー: key code 55")
            elif "US" in layout or "ABC" in layout:
                print("✅ US配列が検出されました")
                print("   右コマンドキー: key code 55")
                print("   左コマンドキー: key code 54")
            else:
                print(f"⚠️ 未知のキーボード配列: {layout}")
                
        else:
            print("❌ キーボード配列を取得できませんでした")
            
    except Exception as e:
        print(f"❌ キーボード配列確認エラー: {e}")

if __name__ == "__main__":
    check_dictation_settings()
    check_keyboard_layout()
