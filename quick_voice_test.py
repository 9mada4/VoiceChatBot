#!/usr/bin/env python3
"""
音声認識クイックテスト
音声入力が正しく動作するかを確認
"""

import subprocess
import tempfile
import os
from faster_whisper import WhisperModel

def test_voice_input():
    """音声認識をテスト"""
    print("🎤 音声認識テスト開始")
    print("="*50)
    
    # Whisperモデル初期化
    print("🤖 Whisperモデル初期化中...")
    try:
        model = WhisperModel("tiny", device="cpu")
        print("✅ Whisperモデル初期化成功")
    except Exception as e:
        print(f"❌ Whisperモデル初期化失敗: {e}")
        return
    
    # 録音テスト
    print("\n📣 5秒間録音します")
    print("マイクに向かって「テストです」と話してください")
    print("3秒後に録音開始...")
    
    import time
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    
    # 一時ファイル作成
    temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    temp_file.close()
    
    try:
        print("🔴 録音開始！「テストです」と話してください")
        
        # 録音実行
        result = subprocess.run([
            'rec', temp_file.name,
            'trim', '0', '5'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ 録音失敗: {result.stderr}")
            return
        
        print("✅ 録音完了")
        
        # ファイルサイズ確認
        file_size = os.path.getsize(temp_file.name)
        print(f"📊 音声ファイルサイズ: {file_size} bytes")
        
        if file_size < 1000:
            print("⚠️ ファイルサイズが小さすぎます。マイクが正しく動作していない可能性があります")
            return
        
        # 音声認識実行
        print("🤖 音声認識実行中...")
        segments, _ = model.transcribe(temp_file.name, language="ja")
        text = " ".join([segment.text for segment in segments])
        
        print(f"🗣️ 認識結果: '{text}'")
        
        if not text.strip():
            print("❌ 音声認識結果が空です")
        else:
            print("✅ 音声認識成功！")
            
            # 「はい」判定テスト
            text_lower = text.lower()
            yes_commands = [
                'はい', 'hai', 'yes', 'うん', 'そうです', 'オッケー', 'ok', 'そう', 'テスト',
                'お願い', 'します', 'いたします', 'ください', '続行', '開始', 
                'よろしく', 'いいよ', 'いいです', 'ありがとう', 'スタート'
            ]
            is_positive = any(word in text_lower for word in yes_commands)
            
            print(f"📝 判定結果: {'✅ ポジティブ' if is_positive else '❌ ネガティブ'}")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
    finally:
        # 一時ファイル削除
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
    
    print("\n🏁 テスト完了")

if __name__ == "__main__":
    test_voice_input()
