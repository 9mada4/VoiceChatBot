"""
ChatGPT返答取得のためのAccessibility APIテスト
"""

import time
from typing import Optional
import subprocess
import logging

try:
    from AppKit import NSWorkspace, NSApplication
    from Cocoa import NSPasteboard, NSStringPboardType
    import pyobjc
    APPKIT_AVAILABLE = True
except ImportError:
    APPKIT_AVAILABLE = False
    print("Warning: AppKit not available. Install with: pip install pyobjc-framework-Cocoa")

logger = logging.getLogger(__name__)

class ChatGPTResponseExtractor:
    """ChatGPTアプリから返答を取得するクラス"""
    
    def __init__(self):
        self.chatgpt_bundle_id = "com.openai.chat"  # ChatGPTアプリのBundle ID
        
    def is_chatgpt_active(self) -> bool:
        """ChatGPTアプリがアクティブかチェック"""
        if not APPKIT_AVAILABLE:
            return False
            
        try:
            workspace = NSWorkspace.sharedWorkspace()
            active_app = workspace.frontmostApplication()
            return active_app.bundleIdentifier() == self.chatgpt_bundle_id
        except Exception as e:
            logger.error(f"Failed to check active app: {e}")
            return False
    
    def get_clipboard_content(self) -> Optional[str]:
        """クリップボードの内容を取得"""
        if not APPKIT_AVAILABLE:
            return None
            
        try:
            pasteboard = NSPasteboard.generalPasteboard()
            content = pasteboard.stringForType_(NSStringPboardType)
            return content
        except Exception as e:
            logger.error(f"Failed to get clipboard content: {e}")
            return None
    
    def copy_chatgpt_response(self) -> Optional[str]:
        """
        ChatGPTの最新返答をクリップボードにコピーして取得
        注意: 手動でテキスト選択→コピーが必要
        """
        logger.info("Attempting to copy ChatGPT response...")
        
        # 現在のクリップボード内容を保存
        original_clipboard = self.get_clipboard_content()
        
        try:
            # Cmd+A で全選択、Cmd+C でコピーを試行
            # 注意: これは危険な操作なので、より安全な方法が必要
            print("ChatGPTの返答をコピーしてください（Cmd+C）")
            print("5秒待機します...")
            time.sleep(5)
            
            # クリップボードの変更をチェック
            new_content = self.get_clipboard_content()
            if new_content and new_content != original_clipboard:
                logger.info("New content detected in clipboard")
                return new_content
            else:
                logger.warning("No new content in clipboard")
                return None
                
        except Exception as e:
            logger.error(f"Failed to copy response: {e}")
            return None
    
    def get_response_via_accessibility(self) -> Optional[str]:
        """
        Accessibility APIを使用してChatGPTの返答を取得
        TODO: 実装が必要
        """
        logger.info("Attempting to get response via Accessibility API...")
        
        # プレースホルダー実装
        # 実際にはmacOSのAccessibility APIを使用してテキストを直接取得
        return None
    
    def get_latest_response(self) -> Optional[str]:
        """最新の返答を取得（複数の方法を試行）"""
        
        # 方法1: Accessibility API（将来実装）
        response = self.get_response_via_accessibility()
        if response:
            return response
        
        # 方法2: クリップボード経由（手動コピー必要）
        response = self.copy_chatgpt_response()
        if response:
            return response
        
        logger.warning("Failed to get ChatGPT response")
        return None

def test_response_extraction():
    """返答取得機能のテスト"""
    print("ChatGPT Response Extraction Test")
    print("================================")
    
    extractor = ChatGPTResponseExtractor()
    
    if not APPKIT_AVAILABLE:
        print("Error: AppKit not available")
        return
    
    print("1. ChatGPTアプリがアクティブか確認...")
    if extractor.is_chatgpt_active():
        print("✅ ChatGPTアプリがアクティブです")
    else:
        print("❌ ChatGPTアプリがアクティブではありません")
        print("ChatGPTアプリを開いてアクティブにしてください")
    
    print("\n2. クリップボード機能テスト...")
    current_clipboard = extractor.get_clipboard_content()
    print(f"現在のクリップボード: {current_clipboard[:50] if current_clipboard else 'Empty'}...")
    
    print("\n3. 返答取得テスト...")
    response = extractor.get_latest_response()
    if response:
        print(f"取得した返答: {response[:100]}...")
    else:
        print("返答を取得できませんでした")

if __name__ == "__main__":
    test_response_extraction()
