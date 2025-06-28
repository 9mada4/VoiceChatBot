#!/bin/bash

echo "🎤 VoiceChatBot Setup Script"
echo "============================"
echo "完全音声操作ChatGPT自動化ツール"
echo ""

# Python環境の確認
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python3 is not installed"
    echo "Homebrewでインストール: brew install python"
    exit 1
fi

echo "✅ Python3 detected: $(python3 --version)"

# SOXの確認・インストール（録音機能用）
if ! command -v rec &> /dev/null; then
    echo "⚠️ SOX (録音機能) が見つかりません"
    echo "Homebrewでインストールしています..."
    if command -v brew &> /dev/null; then
        brew install sox
    else
        echo "❌ Homebrewが必要です: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
fi

echo "✅ SOX録音機能: $(rec --version | head -1)"

echo ""
echo "📦 Pythonパッケージをインストール中..."

# 必要なパッケージをインストール
pip3 install -r requirements.txt

echo ""
echo "🎉 セットアップ完了!"
echo ""
echo "📋 使用前の設定確認チェックリスト:"
echo ""
echo "1. ✅ システム環境設定 > セキュリティとプライバシー > プライバシー > アクセシビリティ"
echo "   → ターミナル（このスクリプト実行環境）にアクセス権限を付与"
echo ""
echo "2. ✅ システム環境設定 > キーボード > 音声入力"
echo "   → 音声入力を「オン」に設定"
echo "   → ショートカット「右コマンドキーを2回押す」を確認"
echo "   → 「拡張音声入力」をオンに設定（推奨）"
echo ""
echo "3. ✅ ChatGPTアプリの準備"
echo "   → ChatGPTアプリを起動してログイン"
echo "   → チャット画面を開いてチャット入力欄をアクティブに"
echo ""
echo "4. ✅ 音声・マイク設定"
echo "   → システムのマイク音量を適切に設定"
echo "   → 静かな環境で使用（音声認識精度向上）"
echo ""
echo "🚀 起動方法:"
echo "   python3 final_voice_bot.py"
echo ""
echo "🎤 使用方法:"
echo "   - 全ての操作を音声のみで制御"
echo "   - 音声①: macOS純正（ChatGPT質問用）"
echo "   - 音声②: Whisper（制御コマンド用）"
echo "   - キーボード入力は一切不要"
echo ""
echo "📖 詳細: README.md を参照"
