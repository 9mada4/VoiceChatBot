#!/usr/bin/env python3
"""
音声認識機能の単体テスト用スクリプト
録音時間とWhisper認識精度のテスト
"""

import time
import tempfile
import subprocess
import os
from typing import Optional

# faster-whisperをインポート
try:
    from faster_whisper import WhisperModel
    VOICE_RECOGNITION_AVAILABLE = True
    print("✅ faster-whisper が利用可能です")
except ImportError as e:
    print(f"❌ faster-whisperが利用できません: {e}")
    VOICE_RECOGNITION_AVAILABLE = False

def test_recording_durations():
    """異なる録音時間での音声認識テスト"""
    if not VOICE_RECOGNITION_AVAILABLE:
        print("音声認識ライブラリが利用できないため、テストをスキップします")
        return
    
    # Whisperモデルを初期化
    try:
        model = WhisperModel("tiny", device="cpu")
        print("✅ Whisperモデルを読み込みました")
    except Exception as e:
        print(f"❌ Whisperモデルの読み込みに失敗: {e}")
        return
    
    durations = [3, 5, 7]  # テストする録音時間（秒）
    
    for duration in durations:
        print(f"\n{'='*50}")
        print(f"録音時間 {duration}秒 のテスト")
        print(f"{'='*50}")
        
        # 録音
        audio_file = record_audio_test(duration)
        if not audio_file:
            print(f"❌ {duration}秒の録音に失敗")
            continue
        
        # 音声認識
        text = transcribe_audio_test(model, audio_file)
        if text:
            print(f"✅ 認識結果: '{text}'")
            
            # 「はい/いいえ」判定
            text_lower = text.lower()
            yes_commands = ['はい', 'hai', 'yes', 'うん', 'そうです', 'オッケー', 'ok', 'そう']
            no_commands = ['いいえ', 'いえ', 'no', 'だめ', 'やめ', 'キャンセル']
            
            if any(yes_word in text_lower for yes_word in yes_commands):
                print("🟢 判定: はい")
            elif any(no_word in text_lower for no_word in no_commands):
                print("🔴 判定: いいえ")
            else:
                print("🟡 判定: 不明")
        else:
            print(f"❌ {duration}秒の音声認識に失敗")
        
        # ファイルクリーンアップ
        try:
            os.unlink(audio_file)
        except:
            pass

def record_audio_test(duration: int) -> Optional[str]:
    """テスト用音声録音"""
    try:
        # 一時ファイル作成
        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_file.close()
        
        print(f"🎤 録音開始 ({duration}秒)")
        print("「はい」または「いいえ」と話してください")
        print("カウントダウン: 3...2...1...開始！")
        
        # macOSのrecコマンドで録音
        cmd = ['rec', temp_file.name, 'trim', '0', str(duration)]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print("✅ 録音完了")
            return temp_file.name
        except subprocess.CalledProcessError as e:
            print(f"❌ 録音コマンドエラー: {e}")
            return None
            
    except Exception as e:
        print(f"❌ 録音エラー: {e}")
        return None

def transcribe_audio_test(model, audio_file: str) -> Optional[str]:
    """テスト用音声認識"""
    try:
        if not audio_file or not os.path.exists(audio_file):
            return None
        
        print("🔄 音声認識中...")
        segments, _ = model.transcribe(audio_file, language="ja")
        text = " ".join([segment.text for segment in segments])
        
        return text.strip()
        
    except Exception as e:
        print(f"❌ 音声認識エラー: {e}")
        return None

def test_whisper_models():
    """異なるWhisperモデルでの認識精度テスト"""
    if not VOICE_RECOGNITION_AVAILABLE:
        print("音声認識ライブラリが利用できないため、テストをスキップします")
        return
    
    models = ["tiny", "base", "small"]
    
    print(f"\n{'='*50}")
    print("Whisperモデル比較テスト")
    print(f"{'='*50}")
    
    # 1回だけ録音
    print("5秒間の音声を録音します...")
    audio_file = record_audio_test(5)
    if not audio_file:
        print("録音に失敗したため、テストを中止します")
        return
    
    for model_name in models:
        try:
            print(f"\n--- {model_name} モデル ---")
            model = WhisperModel(model_name, device="cpu")
            text = transcribe_audio_test(model, audio_file)
            if text:
                print(f"結果: '{text}'")
            else:
                print("認識失敗")
        except Exception as e:
            print(f"❌ {model_name}モデルエラー: {e}")
    
    # ファイルクリーンアップ
    try:
        os.unlink(audio_file)
    except:
        pass

def main():
    """メイン関数"""
    print("🎤 音声認識テストスクリプト")
    print("============================")
    
    # SOXの確認
    try:
        result = subprocess.run(['rec', '--version'], capture_output=True, text=True)
        print(f"✅ SOX録音機能: 利用可能")
    except FileNotFoundError:
        print("❌ SOXが見つかりません: brew install sox")
        return
    
    print("\nテストメニュー:")
    print("1. 録音時間別テスト（3秒、5秒、7秒）")
    print("2. Whisperモデル比較テスト")
    print("3. 両方実行")
    
    choice = input("選択してください (1/2/3): ").strip()
    
    if choice in ['1', '3']:
        test_recording_durations()
    
    if choice in ['2', '3']:
        test_whisper_models()
    
    print("\n🎉 テスト完了！")

if __name__ == "__main__":
    main()
