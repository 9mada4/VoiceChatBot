#!/bin/bash

echo "🎤 VoiceChatBot Setup Script"
echo "============================"
echo "音声だけでChatGPT完全操作ツール"
echo ""

# Python環境の確認
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python3 is not installed"
    echo "Homebrewでインストール: brew install python"
    exit 1
fi

echo "✅ Python3 detected: $(python3 --version)"

# Homebrewの確認
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrewが必要です"
    echo "インストール: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

echo "✅ Homebrew detected"

# SOXの確認・インストール（録音機能用）
if ! command -v rec &> /dev/null; then
    echo "📦 SOX (録音機能) をインストール中..."
    brew install sox
fi

echo "✅ SOX録音機能: $(rec --version | head -1)"

# FFmpegの確認・インストール（音声処理用）
if ! command -v ffmpeg &> /dev/null; then
    echo "📦 FFmpeg (音声処理) をインストール中..."
    brew install ffmpeg
fi

echo "✅ FFmpeg音声処理: $(ffmpeg -version | head -1)"

echo ""
echo "📦 Pythonパッケージをインストール中..."

# 必要なパッケージをインストール
pip3 install -r requirements.txt

echo ""
echo "🎉 セットアップ完了!"
echo ""
echo "📋 使用前の設定確認チェックリスト:"
echo ""
echo "1. ✅ システム環境設定 > キーボード > 音声入力"
echo "   → 音声入力を「オン」に設定"
echo "   → ショートカット「右コマンドキーを2回押す」を確認"
echo "   → 「拡張音声入力」をオンに設定（推奨）"
echo ""
echo "2. ✅ システム環境設定 > セキュリティとプライバシー > プライバシー"
echo "   → アクセシビリティ: ターミナル/VS Codeに権限付与"
echo "   → 画面録画: Python/ターミナルに権限付与"
echo ""
echo "3. ✅ ChatGPTアプリの準備"
echo "   → ChatGPTアプリを起動してログイン"
echo "   → チャット画面を開いてチャット入力欄をアクティブに"
echo ""
echo "4. ✅ startVoiceBtn.png の配置"
echo "   → 音声開始ボタンの画像ファイルを作業ディレクトリに配置"
echo "   → 画面上の音声開始ボタンをスクリーンショットで取得"
echo ""
echo "5. ✅ 音声・マイク設定"
echo "   → システムのマイク音量を適切に設定"
echo "   → 静かな環境で使用（音声認識精度向上）"
echo ""
echo "🚀 起動方法:"
echo "   python3 voice_chat_bot.py"
echo ""
echo "🎤 使用方法:"
echo "   - 全ての操作を音声のみで制御"
echo "   - 音声①: macOS純正（ChatGPT質問用）"
echo "   - 音声②: Whisper（制御コマンド用）"
echo "   - キーボード入力は一切不要"
echo ""
echo "🧪 テスト方法:"
echo "   python3 voice_chat_bot.py test    # 音声機能テスト"
echo "   python3 voice_chat_bot.py scroll  # 画面操作機能テスト"
echo ""
echo "📖 詳細: README.md を参照"
