import time, Quartz

CMD   = 55   # ⌘
CTRL  = 59   # ^
SHIFT = 56   # ⇧
KEY_5 = 23   # 5

FLAGS = (
    Quartz.kCGEventFlagMaskCommand |
    Quartz.kCGEventFlagMaskShift   |
    Quartz.kCGEventFlagMaskControl
)

def post(key, down, flags=0):
    evt = Quartz.CGEventCreateKeyboardEvent(None, key, down)
    if flags:
        Quartz.CGEventSetFlags(evt, flags)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, evt)

time.sleep(2)                       # 画面切り替え猶予
# 1) 修飾キーを押しっぱなし
for k in (CTRL, SHIFT, CMD):
    post(k, True)

time.sleep(0.05)                    # ほんの僅か待機でも可
# 2) 5 keyDown 〈修飾フラグ付き〉
post(KEY_5, True,  FLAGS)
# 3) 5 keyUp   〈修飾フラグ付き〉
post(KEY_5, False, FLAGS)

# 4) 修飾キーを離す
for k in (CMD, SHIFT, CTRL):
    post(k, False)