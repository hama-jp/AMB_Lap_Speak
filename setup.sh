#!/bin/bash
# AMB RC Timer - Setup Script
# 日本語音声読み上げ機能付きRCカータイミングシステムのセットアップ

set -e

echo "🏎️ AMB RC Timer セットアップ開始"
echo "======================================"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 uv をインストール中..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Create virtual environment
echo "🐍 仮想環境を作成中..."
uv venv

# Activate virtual environment
echo "⚡ 仮想環境を有効化中..."
source .venv/bin/activate

# Install dependencies
echo "📚 依存関係をインストール中..."
uv pip install PyYAML>=6.0
grep -v "PyYAML" requirements.txt | uv pip install -r /dev/stdin

# Install additional packages for voice
echo "🎤 音声読み上げパッケージをインストール中..."
uv pip install flask gtts pygame

echo ""
echo "✅ セットアップ完了！"
echo ""
echo "次のステップ:"
echo "1. MySQLデータベースをセットアップ:"
echo "   docker run -d --name mysql-amb -e MYSQL_ROOT_PASSWORD=root -e MYSQL_DATABASE=karts -e MYSQL_USER=kart -e MYSQL_PASSWORD=karts -p 3307:3306 mysql:5.7"
echo ""
echo "2. データベーススキーマを読み込み:"
echo "   sleep 30 && cat schema | docker exec -i mysql-amb mysql -u kart -pkarts karts"
echo ""
echo "3. 設定ファイル conf.yaml でAMBデコーダーのIPアドレスを設定"
echo ""
echo "4. システムを起動:"
echo "   # ターミナル1: データ収集"
echo "   source .venv/bin/activate && python amb_client.py"
echo ""
echo "   # ターミナル2: Webインターフェース"
echo "   source .venv/bin/activate && python web_app.py"
echo ""
echo "5. ブラウザで http://localhost:5000 にアクセス"
echo ""
echo "Happy RC Racing! 🏁🎌"