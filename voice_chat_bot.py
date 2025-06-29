#!/usr/bin/env python3
"""
VoiceChatBot - Simple Voice-Controlled ChatGPT Automation for macOS
シンプル版：最小限のワークフローで音声制御
"""

import time
import subprocess
import logging
import tempfile
import os
import threading
from typing import Optional
import glob
from datetime import datetime

# 音声認識用のインポート
try:
    from faster_whisper import WhisperModel
    VOICE_RECOGNITION_AVAILABLE = True
except ImportError:
    VOICE_RECOGNITION_AVAILABLE = False
    print("Warning: Voice recognition not available")

# macOS用のインポート
try:
    from Quartz.CoreGraphics import CGEventCreateKeyboardEvent, CGEventPost, kCGHIDEventTap
    from Quartz.CoreGraphics import CGEventTapCreate, kCGHeadInsertEventTap, kCGEventTapOptionDefault
    from Quartz.CoreGraphics import CGEventMaskBit, kCGEventKeyDown, CGEventGetIntegerValueField, kCGKeyboardEventKeycode
    import Quartz
    QUARTZ_AVAILABLE = True
except ImportError:
    QUARTZ_AVAILABLE = False
    print("Warning: Quartz not available")

# Vision Framework用のインポート
try:
    import Vision
    from Foundation import NSURL, NSData, NSString
    from Cocoa import NSImage
    VISION_AVAILABLE = True
except ImportError:
    try:
        # PyObjCライブラリが不完全な場合のフォールバック
        from Cocoa import NSString
        from Foundation import NSURL, NSData
        VISION_AVAILABLE = False
        print("Warning: Vision framework not fully available, using fallback OCR")
    except ImportError:
        VISION_AVAILABLE = False
        print("Warning: Vision framework and Foundation not available")

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceBot:
    """シンプル音声ボット"""
    
    def __init__(self):
        self.whisper_model = None
        self.background_thread = None
        self.stop_monitoring = False
        self.keyboard_monitoring = False
        self.screenshot_waiting = False
        if VOICE_RECOGNITION_AVAILABLE:
            try:
                self.whisper_model = WhisperModel("tiny", device="cpu")
                logger.info("Whisper model loaded")
            except Exception as e:
                logger.error(f"Failed to load Whisper: {e}")
    
    def speak_text(self, text: str) -> None:
        """テキストを読み上げ"""
        try:
            print(f"🔊 読み上げ: {text}")
            subprocess.run(['say', text], timeout=30, check=False)
            print("✅ 読み上げ完了")
        except Exception as e:
            logger.error(f"Speech failed: {e}")
            print(f"📝 メッセージ: {text}")
    
    def record_audio_macos(self, duration: int = 4) -> Optional[str]:
        """macOSで音声録音（要件1: 4秒に変更）"""
        try:
            temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            temp_file.close()
            
            print(f"🎤 音声録音中... ({duration}秒)")
            print("「はい」または「終わり」と話してください")
            
            cmd = ['rec', temp_file.name, 'trim', '0', str(duration)]
            
            try:
                subprocess.run(cmd, check=True, capture_output=True)
                print("✅ 録音完了")
                return temp_file.name
            except subprocess.CalledProcessError:
                print("❌ 録音機能が利用できません")
                return None
                
        except Exception as e:
            logger.error(f"Recording failed: {e}")
            return None
    
    def transcribe_audio(self, audio_file: str) -> Optional[str]:
        """音声をテキストに変換"""
        try:
            if not self.whisper_model or not audio_file:
                return None
            
            segments, _ = self.whisper_model.transcribe(audio_file, language="ja")
            text = " ".join([segment.text for segment in segments])
            
            # 一時ファイル削除
            os.unlink(audio_file)
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None
    
    def get_voice_response(self, duration: int = 4) -> bool:
        """音声入力②で「はい」「いいえ」を取得"""
        audio_file = self.record_audio_macos(duration)
        if not audio_file:
            return False
        
        text = self.transcribe_audio(audio_file)
        if not text:
            print("❌ 音声認識に失敗しました")
            return False
        
        print(f"音声認識結果: '{text}'")
        
        # 「はい」系の判定
        yes_commands = ['はい', 'hai', 'yes', 'うん', 'そうです', 'オッケー', 'ok']
        
        # 終了コマンドの検出（ひらがな・漢字・カタカナ対応）
        end_commands = [
            '終わり', 'おわり', 'オワリ', 'OWARI', 'おわりー', 'オワリー',
            'しゅうりょう', 'シュウリョウ', 'SHUURYOU', 'しゅーりょー', 'シューリョー',
            'end', 'finish', 'stop', 'やめ', 'ヤメ',
            'キャンセル', 'cancel', 'ストップ', '中止', 'ちゅうし', 'チュウシ'
        ]
        
        text_lower = text.lower()
        
        # 終了判定を優先
        if any(end_word in text_lower for end_word in end_commands):
            print(f"判定結果: 終わり")
            return False
        
        result = any(yes_word in text_lower for yes_word in yes_commands)
        print(f"判定結果: {'はい' if result else '終わり'}")
        
        return result
    
    def press_key_quartz(self, keycode: int) -> bool:
        """Quartzでキーを送信"""
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
            logger.error(f"Key press failed: {e}")
            return False
    
    def start_dictation(self) -> bool:
        """要件2: 右コマンド2回で音声入力①を開始"""
        if not QUARTZ_AVAILABLE:
            print("💡 手動で音声入力を開始してください：右コマンドキーを2回押す")
            return False
        
        try:
            RIGHT_COMMAND_KEY = 54
            
            print("🎤 音声入力①を開始しています...")
            
            # 1回目
            if not self.press_key_quartz(RIGHT_COMMAND_KEY):
                return False
            time.sleep(0.1)
            
            # 2回目
            if not self.press_key_quartz(RIGHT_COMMAND_KEY):
                return False
            
            print("✅ 音声入力①が開始されました")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start dictation: {e}")
            return False
    
    def stop_dictation(self) -> bool:
        """Escapeキーで音声入力①を停止"""
        if not QUARTZ_AVAILABLE:
            print("💡 手動でEscapeキーを押して音声入力を停止してください")
            return False
        
        try:
            ESCAPE_KEY = 53
            print("🛑 音声入力①を停止しています...")
            
            if not self.press_key_quartz(ESCAPE_KEY):
                return False
            
            print("✅ 音声入力①が停止されました")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop dictation: {e}")
            return False
    
    def background_voice_monitor(self):
        """要件4: バックグラウンドで音声入力②を監視"""
        print("🎧 バックグラウンド音声監視を開始...")
        
        while not self.stop_monitoring:
            try:
                # 音声録音（短い間隔で監視）
                audio_file = self.record_audio_macos(duration=5)
                if audio_file:
                    text = self.transcribe_audio(audio_file)
                    if text:
                        print(f"🎧 監視中の音声: '{text}'")
                        
                        # 「音声入力終了」を検知
                        if '音声入力終わり' in text or '終わり' in text:
                            print("🎯 音声入力終わりを検知！")
                            self.stop_monitoring = True
                            self.stop_dictation()
                            break
                
                time.sleep(1)  # 短い間隔で再チェック
                
            except Exception as e:
                logger.error(f"Background monitoring error: {e}")
                break
        
        print("🛑 バックグラウンド音声監視を終了")
    
    def press_enter(self) -> bool:
        """Enterキーを押す（sample.py参考）"""
        if not QUARTZ_AVAILABLE:
            print("💡 手動でEnterキーを押してください")
            return False
        
        try:
            ENTER_KEY = 36  # Return / Enter（メインキー）
            
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
            
            print("✅ Enterキーを送信しました")
            return True
            
        except Exception as e:
            logger.error(f"Failed to press enter: {e}")
            return False
    
    def send_with_cmd_enter(self) -> bool:
        """要件7: Cmd+Enterで送信"""
        if not QUARTZ_AVAILABLE:
            print("💡 手動でCmd+Enterを押してください")
            return False
        
        try:
            CMD_KEY = 55     # Left Command
            ENTER_KEY = 36   # Enter
            
            print("📤 Cmd+Enterで送信中...")
            
            # Cmd+Enter
            event = CGEventCreateKeyboardEvent(None, CMD_KEY, True)
            CGEventPost(kCGHIDEventTap, event)
            event = CGEventCreateKeyboardEvent(None, ENTER_KEY, True)
            CGEventPost(kCGHIDEventTap, event)
            event = CGEventCreateKeyboardEvent(None, ENTER_KEY, False)
            CGEventPost(kCGHIDEventTap, event)
            event = CGEventCreateKeyboardEvent(None, CMD_KEY, False)
            CGEventPost(kCGHIDEventTap, event)
            
            print("✅ 送信完了")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send with Cmd+Enter: {e}")
            return False
    
    def handle_post_send_screenshot(self) -> bool:
        """送信後の確認処理（簡略化版）"""
        try:
            print("\n【ステップ8】ChatGPT出力確認")
            
            # 音声で確認を待機
            if self.wait_for_voice_confirmation("ChatGPTの出力が終了したら「はい」と答えてください"):
                print("✅ 「はい」を検知 - 処理完了しました")
                return True
            else:
                print("❌ 音声確認がキャンセルされました")
                return False
            
        except Exception as e:
            logger.error(f"Post-send confirmation error: {e}")
            print("❌ 確認処理中にエラーが発生しました")
            return False
    
    def run_requirements_1_to_3(self):
        """メインワークフロー（簡略化版）- 初期確認なし"""
        print("\n" + "="*50)
        print("VoiceChatBot - シンプル音声制御")
        print("="*50)
        
        # 直接音声入力を開始
        print("\n【ステップ1】音声入力開始")
        self.speak_text("お話しください")
        
        if self.start_dictation():
            print("✅ 音声入力①が正常に開始されました")
            return self.run_requirements_4_to_7()
        else:
            print("❌ 音声入力①の開始に失敗しました")
            return False
    
    def run_requirements_4_to_7(self):
        """ステップ4-7を実装（簡略化版）"""
        print("\n【ステップ4-7】音声入力処理と送信")
        
        try:
            # 要件4: バックグラウンドで音声入力②を起動
            self.stop_monitoring = False
            self.background_thread = threading.Thread(target=self.background_voice_monitor)
            self.background_thread.daemon = True
            self.background_thread.start()
            
            # 音声入力終了の検知を待機
            print("🎤 音声で話してください。「音声入力終わり」と言うと音声入力が停止されます")
            
            # バックグラウンドスレッドの終了を待機
            self.background_thread.join(timeout=60)  # 最大60秒待機
            
            if not self.stop_monitoring:
                print("⚠️ タイムアウトしました。手動で音声入力を停止します")
                self.stop_dictation()
            
            # 要件7: Cmd+Enterで送信
            print("\n【ステップ7】送信")
            if self.send_with_cmd_enter():
                print("✅ 送信完了しました")
                
                # 送信後のスクリーンショット処理
                return self.handle_post_send_screenshot()
            else:
                print("❌ 送信に失敗しました")
                return False
                
        except Exception as e:
            logger.error(f"Requirements 4-7 error: {e}")
            return False
    
    
    def wait_for_voice_confirmation(self, message: str) -> bool:
        """音声で「はい」の確認を待機"""
        self.speak_text(message)
        
        while True:
            try:
                print("🎤 「はい」と話してください...")
                
                temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                temp_file.close()
                
                cmd = ['rec', temp_file.name, 'trim', '0', '5']
                try:
                    subprocess.run(cmd, check=True, capture_output=True)
                    
                    if self.whisper_model:
                        segments, _ = self.whisper_model.transcribe(temp_file.name, language="ja")
                        text = " ".join([segment.text for segment in segments])
                        os.unlink(temp_file.name)
                        
                        if text:
                            print(f"音声認識結果: '{text}'")
                            
                            # 「はい」系の判定
                            yes_commands = ['はい', 'hai', 'yes', 'うん', 'そうです', 'オッケー', 'ok']
                            # 終わり系の判定
                            end_commands = ['終わり', 'おわり', 'オワリ', 'キャンセル', 'cancel', 'いいえ', 'no']
                            
                            text_lower = text.lower()
                            
                            if any(yes_word in text_lower for yes_word in yes_commands):
                                print("✅ 「はい」を検知")
                                return True
                            elif any(end_word in text_lower for end_word in end_commands):
                                print("❌ 終了コマンドを検知")
                                return False
                
                except:
                    # 録音失敗時はファイルを削除
                    try:
                        os.unlink(temp_file.name)
                    except:
                        pass
                
                time.sleep(1)
                
            except KeyboardInterrupt:
                print("\n🛑 キーボード割り込みで終了")
                return False
            except Exception as e:
                logger.error(f"Failed to wait for voice confirmation: {e}")
                return False
    
    def scroll_right_side(self, scroll_amount: int = 5) -> bool:
        """画面右側でスクロール"""
        if not QUARTZ_AVAILABLE:
            print("💡 手動でスクロールしてください")
            return False
        
        try:
            # 画面の右側の位置を計算（画面幅の75%あたり）
            from Quartz import CGDisplayBounds, CGMainDisplayID
            
            display_bounds = CGDisplayBounds(CGMainDisplayID())
            screen_width = int(display_bounds.size.width)
            screen_height = int(display_bounds.size.height)
            
            # 画面右側の座標（画面幅の75%、高さの50%）
            right_x = int(screen_width * 0.75)
            center_y = int(screen_height * 0.5)
            
            print(f"📜 画面右側でスクロール中... (位置: {right_x}, {center_y})")
            
            # スクロールイベントを作成
            from Quartz.CoreGraphics import CGEventCreateScrollWheelEvent, CGEventPost, kCGScrollEventUnitPixel
            
            # 下方向にスクロール（負の値で下スクロール）
            scroll_event = CGEventCreateScrollWheelEvent(
                None,  # source
                kCGScrollEventUnitPixel,  # units
                1,     # wheelCount (垂直スクロールのみ)
                -scroll_amount * 10  # deltaAxis1 (負の値で下スクロール)
            )
            
            # マウス位置を設定
            from Quartz.CoreGraphics import CGEventSetLocation
            from Foundation import NSPoint
            CGEventSetLocation(scroll_event, NSPoint(right_x, center_y))
            
            # イベントを送信
            CGEventPost(kCGHIDEventTap, scroll_event)
            
            print("✅ 右側スクロール完了")
            return True
            
        except Exception as e:
            logger.error(f"Failed to scroll on right side: {e}")
            return False
    
    def click_at_position(self, x: int, y: int) -> bool:
        """指定した座標をクリック"""
        if not QUARTZ_AVAILABLE:
            print(f"💡 手動で座標 ({x}, {y}) をクリックしてください")
            return False
        
        try:
            from Quartz.CoreGraphics import (
                CGEventCreateMouseEvent, CGEventPost, 
                kCGEventLeftMouseDown, kCGEventLeftMouseUp,
                kCGMouseButtonLeft
            )
            from Foundation import NSPoint
            
            print(f"🖱️ 座標 ({x}, {y}) をクリック中...")
            
            # マウスダウンイベント
            mouse_down = CGEventCreateMouseEvent(
                None,
                kCGEventLeftMouseDown,
                NSPoint(x, y),
                kCGMouseButtonLeft
            )
            
            # マウスアップイベント
            mouse_up = CGEventCreateMouseEvent(
                None,
                kCGEventLeftMouseUp,
                NSPoint(x, y),
                kCGMouseButtonLeft
            )
            
            # クリック実行
            CGEventPost(kCGHIDEventTap, mouse_down)
            time.sleep(0.1)  # 短い間隔
            CGEventPost(kCGHIDEventTap, mouse_up)
            
            print(f"✅ 座標 ({x}, {y}) のクリック完了")
            return True
            
        except Exception as e:
            logger.error(f"Failed to click at position ({x}, {y}): {e}")
            return False
    
    def find_and_click_image(self, target_description: str = "指定された画像") -> bool:
        """画像を探してクリック（改良版：図形認識→画像解析）"""
        try:
            print(f"🔍 {target_description}を探してクリックします...")
            
            # ステップ1: 画面右側をキャプチャ
            right_screenshot = self.capture_right_side_screen()
            if not right_screenshot:
                print("❌ 画面右側のキャプチャに失敗しました")
                return False
            
            # ステップ2: 図形を個別で認識して座標を保存
            shapes = self.detect_shapes_and_coordinates(right_screenshot)
            if not shapes:
                print("❌ 図形が見つかりませんでした")
                return self.click_fallback_position()
            
            # ステップ3: 各図形がボタンと一致するか画像解析
            button_position = self.match_shapes_with_button(right_screenshot, shapes, "startVoiceBtn.png")
            if button_position:
                click_x, click_y = button_position
                print(f"🎯 ボタンを発見: ({click_x}, {click_y})")
                return self.click_at_position(click_x, click_y)
            else:
                print("❌ startVoiceBtn.pngと一致する図形が見つかりませんでした")
                return self.click_fallback_position()
            
        except Exception as e:
            logger.error(f"Failed to find and click image: {e}")
            return self.click_fallback_position()
    
    def detect_shapes_and_coordinates(self, screenshot_path: str) -> list:
        """図形を個別で認識して座標を保存"""
        try:
            try:
                import cv2
                import numpy as np
            except ImportError:
                print("❌ OpenCVが利用できません。pip install opencv-pythonでインストールしてください")
                return []
            
            # 画像を読み込み
            img = cv2.imread(screenshot_path)
            if img is None:
                print("❌ スクリーンショットの読み込みに失敗しました")
                return []
            
            print("🔍 図形認識を開始...")
            
            # グレースケール変換
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # エッジ検出
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
            # 輪郭検出
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            shapes = []
            
            for i, contour in enumerate(contours):
                # 小さすぎる輪郭は無視
                area = cv2.contourArea(contour)
                if area < 100:  # 最小面積閾値
                    continue
                
                # 輪郭の近似
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # バウンディングボックスを取得
                x, y, w, h = cv2.boundingRect(contour)
                
                # 中心座標を計算
                center_x = x + w // 2
                center_y = y + h // 2
                
                # 図形の種類を判定
                shape_type = self.classify_shape(approx, area, w, h)
                
                shape_info = {
                    'id': i,
                    'type': shape_type,
                    'center': (center_x, center_y),
                    'bbox': (x, y, w, h),
                    'area': area,
                    'contour': contour,
                    'approx': approx
                }
                
                shapes.append(shape_info)
                print(f"  図形{i}: {shape_type}, 中心({center_x}, {center_y}), 面積{area}")
            
            print(f"✅ {len(shapes)}個の図形を認識しました")
            return shapes
            
        except Exception as e:
            logger.error(f"Failed to detect shapes: {e}")
            return []
    
    def classify_shape(self, approx, area: float, width: int, height: int) -> str:
        """図形の種類を分類"""
        try:
            vertices = len(approx)
            aspect_ratio = width / height if height > 0 else 0
            
            # 円形判定
            if vertices > 8 and 0.7 <= aspect_ratio <= 1.3:
                return "circle"
            
            # 矩形判定
            elif vertices == 4:
                if 0.9 <= aspect_ratio <= 1.1:
                    return "square"
                else:
                    return "rectangle"
            
            # 三角形判定
            elif vertices == 3:
                return "triangle"
            
            # その他の多角形
            elif vertices > 4:
                return f"polygon_{vertices}"
            
            else:
                return "unknown"
                
        except Exception as e:
            logger.error(f"Failed to classify shape: {e}")
            return "unknown"
    
    def match_shapes_with_button(self, screenshot_path: str, shapes: list, button_image: str) -> Optional[tuple]:
        """各図形がボタンと一致するか画像解析"""
        try:
            try:
                import cv2
                import numpy as np
            except ImportError:
                print("❌ OpenCVが利用できません")
                return None
            
            # ボタン画像を読み込み
            script_dir = os.path.dirname(os.path.abspath(__file__))
            button_path = os.path.join(script_dir, button_image)
            
            if not os.path.exists(button_path):
                print(f"❌ ボタン画像 {button_image} が見つかりません")
                return None
            
            button_img = cv2.imread(button_path)
            if button_img is None:
                print("❌ ボタン画像の読み込みに失敗しました")
                return None
            
            screenshot_img = cv2.imread(screenshot_path)
            if screenshot_img is None:
                print("❌ スクリーンショットの読み込みに失敗しました")
                return None
            
            button_height, button_width = button_img.shape[:2]
            print(f"🔍 ボタン画像解析: サイズ({button_width}x{button_height})")
            
            best_match = None
            best_confidence = 0.0
            
            # 各図形領域でボタンマッチングを実行
            for shape in shapes:
                try:
                    x, y, w, h = shape['bbox']
                    
                    # 図形領域を少し拡張（ボタンの境界を含むため）
                    margin = 10
                    x1 = max(0, x - margin)
                    y1 = max(0, y - margin)
                    x2 = min(screenshot_img.shape[1], x + w + margin)
                    y2 = min(screenshot_img.shape[0], y + h + margin)
                    
                    # 図形領域を切り出し
                    roi = screenshot_img[y1:y2, x1:x2]
                    
                    if roi.size == 0:
                        continue
                    
                    # テンプレートマッチング
                    if roi.shape[0] >= button_height and roi.shape[1] >= button_width:
                        result = cv2.matchTemplate(roi, button_img, cv2.TM_CCOEFF_NORMED)
                        _, max_val, _, max_loc = cv2.minMaxLoc(result)
                        
                        print(f"  図形{shape['id']} ({shape['type']}): マッチング信頼度 {max_val:.3f}")
                        
                        if max_val > best_confidence and max_val > 0.7:  # 閾値
                            # グローバル座標を計算
                            local_center_x = max_loc[0] + button_width // 2
                            local_center_y = max_loc[1] + button_height // 2
                            
                            global_center_x = x1 + local_center_x
                            global_center_y = y1 + local_center_y
                            
                            best_match = (global_center_x, global_center_y)
                            best_confidence = max_val
                            
                            print(f"    ✅ 新しい最良マッチ: 信頼度 {max_val:.3f}, 位置 ({global_center_x}, {global_center_y})")
                
                except Exception as e:
                    logger.error(f"Error processing shape {shape['id']}: {e}")
                    continue
            
            if best_match:
                # 画面全体の座標に変換（右側キャプチャのオフセットを追加）
                from Quartz import CGDisplayBounds, CGMainDisplayID
                display_bounds = CGDisplayBounds(CGMainDisplayID())
                screen_width = int(display_bounds.size.width)
                right_offset = screen_width // 2
                
                final_x = right_offset + best_match[0]
                final_y = best_match[1]
                
                print(f"🎯 最終的なボタン位置: ({final_x}, {final_y}), 信頼度: {best_confidence:.3f}")
                return (final_x, final_y)
            else:
                print("❌ 閾値を超える一致が見つかりませんでした")
                return None
                
        except Exception as e:
            logger.error(f"Failed to match shapes with button: {e}")
            return None
    
    def capture_right_side_screen(self) -> Optional[str]:
        """画面右側をキャプチャ"""
        try:
            from Quartz import CGDisplayBounds, CGMainDisplayID
            
            display_bounds = CGDisplayBounds(CGMainDisplayID())
            screen_width = int(display_bounds.size.width)
            screen_height = int(display_bounds.size.height)
            
            # 画面右側の範囲を計算（右50%）
            right_x = screen_width // 2
            right_width = screen_width - right_x
            
            # スクリプトのディレクトリにright_side_screenshot.pngで保存
            script_dir = os.path.dirname(os.path.abspath(__file__))
            screenshot_path = os.path.join(script_dir, "right_side_screenshot.png")
            
            print(f"📸 画面右側をキャプチャ中... (範囲: {right_x}, 0, {right_width}, {screen_height})")
            
            # screencaptureで画面右側のみをキャプチャ
            cmd = [
                'screencapture', 
                '-x',  # 音なし
                '-R', f"{right_x},0,{right_width},{screen_height}",  # 範囲指定
                screenshot_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and os.path.exists(screenshot_path):
                print(f"✅ 画面右側キャプチャ完了: {screenshot_path}")
                return screenshot_path
            else:
                print(f"❌ 画面右側キャプチャ失敗: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to capture right side screen: {e}")
            return None
    
    def find_button_in_image(self, screenshot_path: str, button_image: str) -> Optional[tuple]:
        """スクリーンショット内でボタン画像を検索"""
        try:
            # OpenCVを使用した画像認識
            try:
                import cv2
                import numpy as np
            except ImportError:
                print("❌ OpenCVが利用できません。pip install opencv-pythonでインストールしてください")
                return None
            
            # スクリプトディレクトリからボタン画像を読み込み
            script_dir = os.path.dirname(os.path.abspath(__file__))
            button_path = os.path.join(script_dir, button_image)
            
            if not os.path.exists(button_path):
                print(f"❌ ボタン画像 {button_image} が見つかりません")
                return None
            
            # 画像を読み込み
            screenshot_img = cv2.imread(screenshot_path)
            button_img = cv2.imread(button_path)
            
            if screenshot_img is None or button_img is None:
                print("❌ 画像の読み込みに失敗しました")
                return None
            
            print(f"🔍 {button_image} を検索中...")
            
            # テンプレートマッチング
            result = cv2.matchTemplate(screenshot_img, button_img, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            # マッチング閾値
            threshold = 0.7
            
            if max_val >= threshold:
                # ボタンの中心位置を計算
                button_height, button_width = button_img.shape[:2]
                center_x = max_loc[0] + button_width // 2
                center_y = max_loc[1] + button_height // 2
                
                # 画面全体の座標に変換（右側キャプチャの座標オフセットを追加）
                from Quartz import CGDisplayBounds, CGMainDisplayID
                display_bounds = CGDisplayBounds(CGMainDisplayID())
                screen_width = int(display_bounds.size.width)
                right_offset = screen_width // 2
                
                global_x = right_offset + center_x
                global_y = center_y
                
                print(f"✅ ボタンを発見: 信頼度 {max_val:.2f}, 位置 ({global_x}, {global_y})")
                return (global_x, global_y)
            else:
                print(f"❌ ボタンが見つかりません: 最高信頼度 {max_val:.2f} < 閾値 {threshold}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to find button in image: {e}")
            return None
    
    def click_fallback_position(self) -> bool:
        """フォールバック: 推定位置をクリック"""
        try:
            from Quartz import CGDisplayBounds, CGMainDisplayID
            
            display_bounds = CGDisplayBounds(CGMainDisplayID())
            screen_width = int(display_bounds.size.width)
            screen_height = int(display_bounds.size.height)
            
            # 画面右側の適当な位置をクリック（画面幅の70%, 高さの40%）
            click_x = int(screen_width * 0.7)
            click_y = int(screen_height * 0.4)
            
            print(f"💡 フォールバック: 推定位置 ({click_x}, {click_y}) をクリックします")
            return self.click_at_position(click_x, click_y)
            
        except Exception as e:
            logger.error(f"Failed to click fallback position: {e}")
            return False
    
    def find_and_click_image_simple(self, button_image: str = "startVoiceBtn.png") -> bool:
        """PyAutoGUIを使用したシンプルな画像検索・クリック"""
        try:
            try:
                import pyautogui
            except ImportError:
                print("❌ PyAutoGUIが利用できません。pip install pyautoguiでインストールしてください")
                return False
            
            print(f"🔍 PyAutoGUIで{button_image}を検索中...")
            
            # スクリプトディレクトリからボタン画像のパスを取得
            script_dir = os.path.dirname(os.path.abspath(__file__))
            button_path = os.path.join(script_dir, button_image)
            
            if not os.path.exists(button_path):
                print(f"❌ ボタン画像 {button_image} が見つかりません")
                return False
            
            # 画像を画面上で検索
            location = pyautogui.locateOnScreen(button_path, confidence=0.8)
            
            if location:
                # 見つかった位置の中心をクリック
                center = pyautogui.center(location)
                print(f"🎯 ボタンを発見: {location}, 中心: {center}")
                
                pyautogui.click(center)
                print(f"✅ {button_image} のクリック完了")
                return True
            else:
                print(f"❌ {button_image} が見つかりませんでした")
                return False
                
        except Exception as e:
            logger.error(f"Failed to find and click image with PyAutoGUI: {e}")
            return False

    # ...existing code...
    
def main():
    """メイン関数"""
    print("VoiceChatBot for macOS")
    print("=====================")
    print("シンプル音声制御ワークフロー:")
    print("1. 音声入力開始（確認なし）")
    print("2. 音声入力終了の検知")
    print("3. 自動送信")
    print("4. ChatGPT出力確認（音声制御）")
    print("※全て音声で操作します（ひらがな・漢字・カタカナ対応）")
    print("")
    
    bot = VoiceBot()
    success = bot.run_requirements_1_to_3()
    
    if success:
        print("\n🎉 全ての要件が正常に完了しました！")
    else:
        print("\n❌ 処理中にエラーが発生しました")

def test_voice_function():
    """音声機能のテスト用関数"""
    print("音声機能のテストを開始します...")
    
    bot = VoiceBot()
    
    # 音声確認テスト
    print("\n=== 音声確認テスト ===")
    print("音声確認機能をテストします...")
    result = bot.wait_for_voice_confirmation("テスト用メッセージです。「はい」と答えてください")
    
    if result:
        print("✅ 音声確認テスト成功")
    else:
        print("❌ 音声確認テスト失敗")

def test_scroll_click_function():
    """スクロールとクリック機能のテスト用関数"""
    print("スクロールとクリック機能のテストを開始します...")
    
    bot = VoiceBot()
    
    # スクロールテスト
    print("\n=== 右側スクロールテスト ===")
    print("画面右側でスクロールします...")
    if bot.scroll_right_side():
        print("✅ 右側スクロールテスト成功")
    else:
        print("❌ 右側スクロールテスト失敗")
    
    time.sleep(2)  # 2秒待機
    
    # 方法選択
    print("\n=== 画像検索方法選択 ===")
    print("1. PyAutoGUI（シンプル）")
    print("2. OpenCV図形認識（高度）")
    
    try:
        choice = input("選択してください (1 or 2): ").strip()
    except:
        choice = "2"  # デフォルト
    
    if choice == "1":
        # PyAutoGUI方式
        print("\n=== PyAutoGUI方式テスト ===")
        if bot.find_and_click_image_simple("startVoiceBtn.png"):
            print("✅ PyAutoGUI方式テスト成功")
        else:
            print("❌ PyAutoGUI方式テスト失敗")
    else:
        # OpenCV図形認識方式（既存）
        print("\n=== 画面右側キャプチャテスト ===")
        screenshot_path = bot.capture_right_side_screen()
        if screenshot_path:
            print(f"✅ 画面右側キャプチャ成功: {screenshot_path}")
            
            print("\n=== 図形認識テスト ===")
            shapes = bot.detect_shapes_and_coordinates(screenshot_path)
            if shapes:
                print(f"✅ 図形認識成功: {len(shapes)}個の図形を検出")
                for shape in shapes[:5]:  # 最初の5個のみ表示
                    print(f"  - 図形{shape['id']}: {shape['type']}, 中心{shape['center']}, 面積{shape['area']}")
            else:
                print("❌ 図形認識失敗")
        else:
            print("❌ 画面右側キャプチャ失敗")
            return
        
        time.sleep(1)
        
        print("\n=== OpenCV図形認識方式テスト ===")
        if bot.find_and_click_image("startVoiceBtn.png"):
            print("✅ OpenCV図形認識方式テスト成功")
        else:
            print("❌ OpenCV図形認識方式テスト失敗")
    
    time.sleep(2)  # 2秒待機
    
    # startVoiceBtn.png検索・クリックテスト（シンプル版）
    print("\n=== startVoiceBtn.png検索・クリックテスト（シンプル版） ===")
    print("PyAutoGUIを使用してstartVoiceBtn.pngを探してクリックします...")
    if bot.find_and_click_image_simple("startVoiceBtn.png"):
        print("✅ startVoiceBtn.pngクリックテスト成功")
    else:
        print("❌ startVoiceBtn.pngクリックテスト失敗")

if __name__ == "__main__":
    import sys
    
    # コマンドライン引数でテストモードを指定
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            test_voice_function()
        elif sys.argv[1] == "scroll":
            test_scroll_click_function()
        else:
            print("使用方法:")
            print("  python voice_chat_bot.py          # メイン機能")
            print("  python voice_chat_bot.py test     # 音声テスト")
            print("  python voice_chat_bot.py scroll   # スクロール・クリックテスト")
    else:
        main()

