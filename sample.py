import pytesseract
from PIL import Image
import subprocess

# OCRの言語を日本語に指定
def extract_japanese_text(image_path):
    return pytesseract.image_to_string(Image.open(image_path), lang='jpn')

# macOSのsayコマンドで読み上げ
def speak_japanese(text):
    subprocess.run(['say', '-v', 'Kyoko', text])

# メイン処理
image_path = 'example.png'  # ← 日本語が写った画像
text = extract_japanese_text(image_path)

print("抽出されたテキスト：")
print(text)

if text.strip():
    speak_japanese(text)
else:
    print("❌ テキストが検出されませんでした")