#!/usr/bin/env python3
"""
VoiceChatBot テストスイート
各機能を個別にテストするためのスクリプト
"""

import sys
import time
import subprocess
import tempfile
import os
from typing import Optional

def print_header(title: str):
    """テストセクションのヘッダー表示"""
    print("\n" + "="*50)
    print(f"🧪 {title}")
    print("="*50)

def print_test(test_name: str):
    """個別テストの開始表示"""
    print(f"\n🔍 {test_name}")
    print("-" * 30)

def print_result(success: bool, message: str):
    """テスト結果の表示"""
    status = "✅" if success else "❌"
    print(f"{status} {message}")

def test_dependencies():
    """依存関係のテスト"""
    print_header("依存関係チェック")
    
    dependencies = [
        ("pyautogui", "PyAutoGUI"),
        ("faster_whisper", "faster-whisper"),
        ("AppKit", "macOS AppKit"),
        ("Cocoa", "macOS Cocoa"),
        ("subprocess", "subprocess"),
        ("tempfile", "tempfile"),
        ("logging", "logging")
    ]
    
    all_ok = True
    for module, name in dependencies:
        print_test(f"{name} インポートテスト")
        try:
            __import__(module)
            print_result(True, f"{name} - インポート成功")
        except ImportError as e:
            print_result(False, f"{name} - インポートエラー: {e}")
            all_ok = False
    
    return all_ok

def test_sox_recording():
    """SOX録音機能のテスト"""
    print_header("SOX録音機能テスト")
    
    print_test("rec コマンド存在確認")
    try:
        result = subprocess.run(['which', 'rec'], capture_output=True, text=True)
        if result.returncode == 0:
            print_result(True, f"rec コマンド発見: {result.stdout.strip()}")
        else:
            print_result(False, "rec コマンドが見つかりません")
            return False
    except Exception as e:
        print_result(False, f"rec コマンドチェックエラー: {e}")
        return False
    
    print_test("rec バージョン確認")
    try:
        result = subprocess.run(['rec', '--version'], capture_output=True, text=True)
        version_info = result.stderr.split('\n')[0] if result.stderr else "不明"
        print_result(True, f"SOXバージョン: {version_info}")
    except Exception as e:
        print_result(False, f"バージョン確認エラー: {e}")
    
    print_test("短時間録音テスト (3秒)")
    temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    temp_file.close()
    
    try:
        print("📣 3秒間録音します。何か話してください...")
        result = subprocess.run([
            'rec', temp_file.name, 
            'trim', '0', '3'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and os.path.exists(temp_file.name):
            file_size = os.path.getsize(temp_file.name)
            print_result(True, f"録音成功 - ファイルサイズ: {file_size} bytes")
            os.unlink(temp_file.name)
            return True
        else:
            print_result(False, f"録音失敗: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print_result(False, "録音タイムアウト")
        return False
    except Exception as e:
        print_result(False, f"録音エラー: {e}")
        return False
    finally:
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

def test_whisper_model():
    """Whisperモデルのテスト"""
    print_header("Whisper音声認識テスト")
    
    print_test("faster-whisperモデル初期化")
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("tiny", device="cpu")
        print_result(True, "Whisperモデル初期化成功")
        return model
    except Exception as e:
        print_result(False, f"Whisperモデル初期化エラー: {e}")
        return None

def test_voice_recognition_integration():
    """音声認識統合テスト"""
    print_header("音声認識統合テスト")
    
    # SOXテスト
    if not test_sox_recording():
        print_result(False, "SOX録音機能が利用できないため、音声認識テストをスキップ")
        return False
    
    # Whisperモデルテスト
    model = test_whisper_model()
    if not model:
        print_result(False, "Whisperモデルが利用できないため、音声認識テストをスキップ")
        return False
    
    print_test("音声認識統合テスト (5秒間)")
    temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    temp_file.close()
    
    try:
        print("📣 5秒間で「はい」または「テスト」と話してください...")
        
        # 録音
        result = subprocess.run([
            'rec', temp_file.name,
            'trim', '0', '5'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            print_result(False, "録音に失敗しました")
            return False
        
        print("🤖 音声認識中...")
        
        # 音声認識
        segments, _ = model.transcribe(temp_file.name, language="ja")
        text = " ".join([segment.text for segment in segments])
        
        if text.strip():
            print_result(True, f"音声認識成功: '{text}'")
            
            # 「はい」判定テスト
            text_lower = text.lower()
            yes_commands = ['はい', 'hai', 'yes', 'うん', 'そうです', 'オッケー', 'ok', 'そう', 'テスト']
            is_yes = any(yes_word in text_lower for yes_word in yes_commands)
            
            print(f"📝 「はい」系判定: {'✅ はい' if is_yes else '❌ いいえ'}")
            return True
        else:
            print_result(False, "音声認識結果が空です")
            return False
            
    except Exception as e:
        print_result(False, f"音声認識統合テストエラー: {e}")
        return False
    finally:
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

def test_pyautogui():
    """PyAutoGUI動作テスト"""
    print_header("PyAutoGUI動作テスト")
    
    print_test("PyAutoGUI基本機能")
    try:
        import pyautogui
        
        # 基本情報取得
        position = pyautogui.position()
        screen_size = pyautogui.size()
        
        print_result(True, f"マウス位置: {position}")
        print_result(True, f"画面サイズ: {screen_size}")
        
        return True
    except Exception as e:
        print_result(False, f"PyAutoGUIエラー: {e}")
        return False

def test_right_cmd_key():
    """右コマンドキー2回押しテスト（AppleScript使用、JIS/US配列対応）"""
    print_header("右コマンドキー2回押しテスト")
    
    print_test("AppleScript経由の右コマンドキー動作テスト（JIS/US配列対応）")
    try:
        print("⚠️  3秒後に右コマンドキー2回押しを実行します")
        print("音声入力が起動するか確認してください...")
        time.sleep(3)
        
        # まずJIS配列（key code 54）で試行
        applescript_jis = '''
        tell application "System Events"
            key code 54
            delay 0.3
            key code 54
        end tell
        '''
        
        result = subprocess.run(['osascript', '-e', applescript_jis], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print_result(True, "AppleScript経由の右コマンドキー2回押し実行完了（JIS配列）")
        else:
            print(f"JIS配列（key code 54）で失敗、US配列を試行: {result.stderr}")
            
            # US配列（key code 55）で試行
            applescript_us = '''
            tell application "System Events"
                key code 55
                delay 0.3
                key code 55
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', applescript_us], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print_result(True, "AppleScript経由の右コマンドキー2回押し実行完了（US配列）")
            else:
                print_result(False, f"US配列でも実行エラー: {result.stderr}")
                return False
        
        # プロセス確認
        print_test("音声入力プロセス確認")
        time.sleep(2)  # 音声入力起動を待機
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        dictation_processes = ['DictationIM', 'SpeechRecognitionServer']
        
        found = []
        for process in dictation_processes:
            if process in result.stdout:
                found.append(process)
        
        if found:
            print_result(True, f"音声入力プロセス検出: {', '.join(found)}")
        else:
            print_result(False, "音声入力プロセスが検出されませんでした")
        
        return True
    except Exception as e:
        print_result(False, f"右コマンドキーテストエラー: {e}")
        return False

def test_macos_say():
    """macOS say コマンドテスト"""
    print_header("macOS say（読み上げ）テスト")
    
    print_test("say コマンド存在確認")
    try:
        result = subprocess.run(['which', 'say'], capture_output=True, text=True)
        if result.returncode == 0:
            print_result(True, f"say コマンド発見: {result.stdout.strip()}")
        else:
            print_result(False, "say コマンドが見つかりません")
            return False
    except Exception as e:
        print_result(False, f"say コマンドチェックエラー: {e}")
        return False
    
    print_test("音声出力テスト")
    try:
        print("🔊 テスト音声を再生します...")
        result = subprocess.run([
            'say', 'VoiceChatBot音声テストです。聞こえていますか？'
        ], timeout=10)
        
        if result.returncode == 0:
            print_result(True, "音声出力テスト成功")
            return True
        else:
            print_result(False, f"音声出力エラー (終了コード: {result.returncode})")
            return False
    except subprocess.TimeoutExpired:
        print_result(False, "音声出力タイムアウト")
        return False
    except Exception as e:
        print_result(False, f"音声出力テストエラー: {e}")
        return False

def test_clipboard():
    """クリップボード機能テスト"""
    print_header("クリップボード機能テスト")
    
    print_test("pbcopy/pbpaste テスト")
    test_data = "VoiceChatBot クリップボードテストデータ"
    
    try:
        # データをクリップボードに送信
        subprocess.run(['pbcopy'], input=test_data, text=True, check=True)
        print_result(True, "pbcopy でデータ送信成功")
        
        # クリップボードからデータを取得
        result = subprocess.run(['pbpaste'], capture_output=True, text=True, check=True)
        retrieved_data = result.stdout.strip()
        
        if retrieved_data == test_data:
            print_result(True, f"pbpaste でデータ取得成功: '{retrieved_data}'")
            return True
        else:
            print_result(False, f"データ不一致: 期待値'{test_data}' 取得値'{retrieved_data}'")
            return False
            
    except Exception as e:
        print_result(False, f"クリップボードテストエラー: {e}")
        return False

def test_voice_chat_bot_import():
    """VoiceChatBotメインモジュールのインポートテスト"""
    print_header("VoiceChatBotモジュールテスト")
    
    print_test("voice_chat_bot.py インポートテスト")
    try:
        # メインモジュールからクラスをインポート
        sys.path.insert(0, '/Users/kumamotoseita/GitHub/VoiceChatBot')
        
        from voice_chat_bot import (
            VoiceCommandRecognizer,
            ChatGPTResponseExtractor,
            NativeDictationController,
            FinalVoiceChatBot
        )
        
        print_result(True, "VoiceCommandRecognizer インポート成功")
        print_result(True, "ChatGPTResponseExtractor インポート成功")
        print_result(True, "NativeDictationController インポート成功")
        print_result(True, "FinalVoiceChatBot インポート成功")
        
        # 基本的なインスタンス化テスト
        print_test("クラスインスタンス化テスト")
        
        recognizer = VoiceCommandRecognizer()
        print_result(True, "VoiceCommandRecognizer インスタンス化成功")
        
        extractor = ChatGPTResponseExtractor()
        print_result(True, "ChatGPTResponseExtractor インスタンス化成功")
        
        controller = NativeDictationController()
        print_result(True, "NativeDictationController インスタンス化成功")
        
        return True
        
    except Exception as e:
        print_result(False, f"VoiceChatBotモジュールテストエラー: {e}")
        return False

def run_all_tests():
    """全テストの実行"""
    print("🎤 VoiceChatBot テストスイート")
    print("=" * 60)
    print("各機能を順次テストします。")
    print("音声テストでは実際に話してください。")
    print("=" * 60)
    
    tests = [
        ("依存関係", test_dependencies),
        ("PyAutoGUI", test_pyautogui),
        ("クリップボード", test_clipboard),
        ("macOS say", test_macos_say),
        ("SOX録音", test_sox_recording),
        ("Whisper", test_whisper_model),
        ("右コマンドキー", test_right_cmd_key),
        ("VoiceChatBotモジュール", test_voice_chat_bot_import),
        ("音声認識統合", test_voice_recognition_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except KeyboardInterrupt:
            print("\n\n⚠️ ユーザーによりテストが中断されました")
            break
        except Exception as e:
            print_result(False, f"{test_name}テストで予期しないエラー: {e}")
            results.append((test_name, False))
    
    # 結果サマリー
    print("\n" + "="*60)
    print("🏁 テスト結果サマリー")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n📊 結果: {passed}/{total} テスト合格")
    
    if passed == total:
        print("🎉 全てのテストが合格しました！VoiceChatBotは正常に動作する準備ができています。")
    else:
        print("⚠️ 一部のテストが失敗しました。失敗したテストの修正を検討してください。")
    
    return passed == total

def interactive_menu():
    """インタラクティブメニュー"""
    while True:
        print("\n🧪 VoiceChatBot テストメニュー")
        print("="*40)
        print("1. 全テスト実行")
        print("2. 依存関係チェック")
        print("3. SOX録音テスト")
        print("4. Whisper音声認識テスト")
        print("5. 右コマンドキー2回押しテスト")
        print("6. macOS say（読み上げ）テスト")
        print("7. クリップボードテスト")
        print("8. VoiceChatBotモジュールテスト")
        print("9. 音声認識統合テスト")
        print("0. 終了")
        print("="*40)
        
        try:
            choice = input("テストを選択してください (0-9): ").strip()
            
            if choice == '0':
                print("👋 テスト終了")
                break
            elif choice == '1':
                run_all_tests()
            elif choice == '2':
                test_dependencies()
            elif choice == '3':
                test_sox_recording()
            elif choice == '4':
                test_whisper_model()
            elif choice == '5':
                test_right_cmd_key()
            elif choice == '6':
                test_macos_say()
            elif choice == '7':
                test_clipboard()
            elif choice == '8':
                test_voice_chat_bot_import()
            elif choice == '9':
                test_voice_recognition_integration()
            else:
                print("❌ 無効な選択です。0-9の数字を入力してください。")
                
        except KeyboardInterrupt:
            print("\n👋 テスト終了")
            break
        except Exception as e:
            print(f"❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        # 全テスト自動実行
        run_all_tests()
    else:
        # インタラクティブメニュー
        interactive_menu()
