import time
from Quartz.CoreGraphics import (
    CGEventCreateKeyboardEvent,
    CGEventPost,
    kCGHIDEventTap
)

# ── キーコード定義 ──────────────────────────
ENTER_KEY = 36   # Return / Enter（メインキー）
# ENTER_KEY = 76   # ← テンキー Enter を使いたい場合はこちら

def press_enter():
    """Return / Enter キーを 1 回押下"""
    # keyDown
    CGEventPost(
        kCGHIDEventTap,
        CGEventCreateKeyboardEvent(None, ENTER_KEY, True)
    )
    time.sleep(0.05)  # 押しっぱなし時間
    # keyUp
    CGEventPost(
        kCGHIDEventTap,
        CGEventCreateKeyboardEvent(None, ENTER_KEY, False)
    )

# 実行（アクセシビリティ許可を付与しておくこと）
time.sleep(4)   # アプリ切り替え猶予
press_enter()
print("Enter キーを送信しました")