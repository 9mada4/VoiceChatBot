#!/bin/bash

echo "VoiceChatBot Setup Script"
echo "========================="

# Python環境の確認
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed"
    exit 1
fi

echo "Installing required packages..."

# 必要なパッケージをインストール
pip3 install -r requirements.txt

echo ""
echo "Setup completed!"
echo ""
echo "使用前の設定確認:"
echo "1. システム環境設定 > セキュリティとプライバシー > プライバシー > アクセシビリティ"
echo "   でこのスクリプトを実行するターミナル/アプリにアクセス権限を付与してください"
echo ""
echo "2. システム環境設定 > キーボード > 音声入力"
echo "   で音声入力を有効にし、ショートカットを確認してください"
echo ""
echo "3. ChatGPTアプリを起動してチャット画面を開いてください"
echo ""
echo "起動方法:"
echo "python3 voice_chat_bot.py"
