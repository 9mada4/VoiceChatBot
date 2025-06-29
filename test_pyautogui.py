#!/usr/bin/env python3
"""
PyAutoGUI動作テスト
"""

import pyautogui
import os

def test_pyautogui():
    print("PyAutoGUI動作テスト開始...")
    
    # スクリーンショット取得テスト
    try:
        screenshot = pyautogui.screenshot()
        print(f"✅ スクリーンショット成功: サイズ {screenshot.size}")
    except Exception as e:
        print(f"❌ スクリーンショット失敗: {e}")
        return
    
    # 画像ファイル確認
    button_path = "./startVoiceBtn.png"
    if os.path.exists(button_path):
        print(f"✅ ボタン画像存在: {button_path}")
    else:
        print(f"❌ ボタン画像なし: {button_path}")
        return
    
    # 画像検索テスト（信頼度を段階的に下げる）
    try:
        print("🔍 画像検索実行中...")
        
        # 複数の信頼度でテスト
        confidences = [0.8, 0.6, 0.4, 0.3]
        location = None
        
        for conf in confidences:
            try:
                print(f"  信頼度 {conf} でテスト中...")
                location = pyautogui.locateOnScreen(button_path, confidence=conf)
                if location:
                    print(f"✅ 発見! 信頼度 {conf} で発見: {location}")
                    break
            except pyautogui.ImageNotFoundException:
                print(f"  信頼度 {conf} では見つからず")
                continue
        
        if location:
            center = pyautogui.center(location)
            print(f"🎯 ボタン発見: 位置 {location}, 中心 {center}")
        else:
            print("❌ すべての信頼度で見つかりませんでした")
            
    except Exception as e:
        print(f"❌ 画像検索エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pyautogui()
