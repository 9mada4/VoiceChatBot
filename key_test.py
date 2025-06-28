#!/usr/bin/env python3
"""
統合キー操作テスト
メインファイルのキー操作関数とPyAutoGUI直接テストの両方を実行
"""

import subprocess
import time
import sys
import os
import pyautogui

# Quartzインポート
try:
    from Quartz.CoreGraphics import CGEventCreateKeyboardEvent, CGEventPost, kCGHIDEventTap
    QUARTZ_AVAILABLE = True
except ImportError:
    QUARTZ_AVAILABLE = False

def press_key_quartz(keycode: int) -> bool:
    """Quartzを使用してキーを送信"""
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
        print(f"Quartz key press failed: {e}")
        return False

def quartz_test():
    """Quartz（macOSネイティブAPI）テスト"""
    print("\n🔧 Quartz（macOSネイティブAPI）テスト")
    print("-" * 30)
    
    if not QUARTZ_AVAILABLE:
        print("❌ Quartzが利用できません")
        return False, False
    
    # 右コマンドキーテスト
    print("Quartz右コマンドキー2回押しテスト（3秒後）...")
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    
    try:
        RIGHT_COMMAND_KEY = 54
        
        # 1回目
        if not press_key_quartz(RIGHT_COMMAND_KEY):
            print("❌ 1回目の右コマンドキー送信失敗")
            return False, False
        
        time.sleep(0.3)
        
        # 2回目
        if not press_key_quartz(RIGHT_COMMAND_KEY):
            print("❌ 2回目の右コマンドキー送信失敗")
            return False, False
        
        print("✅ Quartz右コマンドキー送信完了")
        right_cmd_ok = True
    except Exception as e:
        print(f"❌ Quartz右コマンドキーエラー: {e}")
        right_cmd_ok = False
    
    # 5秒待機
    print("5秒待機...")
    time.sleep(5)
    
    # Escapeキーテスト
    print("QuartzEscapeキーテスト（3秒後）...")
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    
    try:
        ESCAPE_KEY = 53  # macOSでのEscapeキーのキーコード
        
        if press_key_quartz(ESCAPE_KEY):
            print("✅ QuartzEscapeキー送信完了")
            escape_ok = True
        else:
            print("❌ QuartzEscapeキー送信失敗")
            escape_ok = False
    except Exception as e:
        print(f"❌ QuartzEscapeキーエラー: {e}")
        escape_ok = False
    
    return right_cmd_ok, escape_ok

# メインファイルからインポート
try:
    from voice_chat_bot import NativeDictationController
    MAIN_MODULE_AVAILABLE = True
except ImportError:
    MAIN_MODULE_AVAILABLE = False

# 音声入力用のWhisperインポート
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

def simple_pyautogui_test():
    """PyAutoGUI直接テスト（超シンプル）"""
    print("🔧 PyAutoGUI直接テスト")
    print("-" * 30)
    
    # 右コマンドキーテスト
    print("右コマンドキー2回押しテスト（3秒後）...")
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    
    try:
        # 右コマンドキー2回押し
        for i in range(2):
            pyautogui.keyDown('right_cmd')
            time.sleep(0.05)
            pyautogui.keyUp('right_cmd')
            if i == 0:
                time.sleep(0.3)
        print("✅ 右コマンドキー送信完了")
        right_cmd_ok = True
    except Exception as e:
        print(f"❌ 右コマンドキーエラー: {e}")
        right_cmd_ok = False
    
    # 5秒待機
    print("5秒待機...")
    time.sleep(5)
    
    # Escapeキーテスト
    print("Escapeキーテスト（3秒後）...")
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    
    try:
        pyautogui.press('escape')
        print("✅ Escapeキー送信完了")
        escape_ok = True
    except Exception as e:
        print(f"❌ Escapeキーエラー: {e}")
        escape_ok = False
    
    return right_cmd_ok, escape_ok

def main_module_test():
    """メインファイルのキー操作関数テスト"""
    if not MAIN_MODULE_AVAILABLE:
        print("❌ voice_chat_bot.pyが利用できません")
        return False, False
    
    print("\n🔧 メインファイルキー操作テスト")
    print("-" * 30)
    
    controller = NativeDictationController()
    
    # 現在状態確認
    print("現在の音声入力状態をチェック...")
    is_active = controller.check_dictation_status()
    print(f"現在: {'アクティブ' if is_active else '非アクティブ'}")
    
    # 開始テスト
    print("\n音声入力開始テスト（3秒後）...")
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    
    start_result = controller.start_dictation()
    print(f"開始結果: {'✅ 成功' if start_result else '❌ 失敗'}")
    
    # 停止テスト
    print("\n音声入力停止テスト（3秒後）...")
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    
    stop_result = controller.stop_dictation()
    print(f"停止結果: {'✅ 成功' if stop_result else '❌ 失敗'}")
    
    return start_result, stop_result

def main():
    """統合キー操作テスト"""
    print("🧪 統合キー操作テスト")
    print("=" * 50)
    print("PyAutoGUI直接テストとメインファイル関数テストを実行します")
    
    print("\n⚠️  注意:")
    print("- macOSの「システム設定 > キーボード > 音声入力」が有効である必要があります")
    print("- アクセシビリティ権限が必要です")
    print("- 画面を見て音声入力（マイクアイコン）の表示を確認してください")
    
    print("\n✨ 5秒後にテストを開始します...")
    print("中止する場合は Ctrl+C を押してください")
    
    try:
        for i in range(5, 0, -1):
            print(f"開始まで {i} 秒...")
            time.sleep(1)
        
        print("\n" + "=" * 50)
        
        # 1. Quartzテスト
        quartz_right_cmd_ok, quartz_escape_ok = quartz_test()
        
        # 2. PyAutoGUI直接テスト
        right_cmd_ok, escape_ok = simple_pyautogui_test()
        
        # 3. メインファイル関数テスト
        start_ok, stop_ok = main_module_test()
        
        # 結果サマリー
        print("\n🏁 テスト結果サマリー")
        print("=" * 50)
        print("Quartz（macOSネイティブAPI）テスト:")
        if QUARTZ_AVAILABLE:
            print(f"  右コマンドキー: {'✅ OK' if quartz_right_cmd_ok else '❌ NG'}")
            print(f"  Escapeキー: {'✅ OK' if quartz_escape_ok else '❌ NG'}")
        else:
            print("  ❌ Quartzが利用できません")
        
        print("PyAutoGUI直接テスト:")
        print(f"  右コマンドキー: {'✅ OK' if right_cmd_ok else '❌ NG'}")
        print(f"  Escapeキー: {'✅ OK' if escape_ok else '❌ NG'}")
        
        print("メインファイル関数テスト:")
        if MAIN_MODULE_AVAILABLE:
            print(f"  音声入力開始: {'✅ OK' if start_ok else '❌ NG'}")
            print(f"  音声入力停止: {'✅ OK' if stop_ok else '❌ NG'}")
        else:
            print("  ❌ メインファイルが利用できません")
        
        # 総合判定
        all_ok = (
            (quartz_right_cmd_ok and quartz_escape_ok if QUARTZ_AVAILABLE else True) and
            right_cmd_ok and escape_ok and 
            (start_ok if MAIN_MODULE_AVAILABLE else True)
        )
        print(f"\n総合結果: {'🎉 全テスト成功!' if all_ok else '⚠️ 一部テストで問題あり'}")
        
        if not all_ok:
            print("macOSの音声入力設定やアクセシビリティ権限を確認してください")
        
        # 推奨使用方法の表示
        print(f"\n💡 推奨キー送信方法:")
        if QUARTZ_AVAILABLE:
            print("✅ Quartz（macOSネイティブAPI）が利用可能 - 最も確実")
        if right_cmd_ok:
            print("✅ PyAutoGUIフォールバック利用可能")
        if not QUARTZ_AVAILABLE and not right_cmd_ok:
            print("❌ どちらのキー送信方法も利用できません")
            
    except KeyboardInterrupt:
        print("\n❌ テストがキャンセルされました")
        return

if __name__ == "__main__":
    main()
