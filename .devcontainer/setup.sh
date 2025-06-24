#!/bin/bash

# start-ollama.shに実行権限を付与
chmod +x /home/klab/start-ollama.sh

# Ollamaディレクトリの権限を修正
echo "Fixing Ollama directory permissions..."
sudo chown -R klab:klab /home/klab/.ollama
sudo chmod -R 755 /home/klab/.ollama

# ollama_code.pyに実行権限を付与
chmod +x /home/klab/ollama_code.py

# エイリアスをbashrcに追加
echo "Setting up aliases..."
if ! grep -q "alias olc=" /home/klab/.bashrc; then
    echo 'alias olc="python3 /home/klab/ollama_code.py"' >> /home/klab/.bashrc
    echo 'alias ollama-code="python3 /home/klab/ollama_code.py"' >> /home/klab/.bashrc
fi

# 自前の.bashrcがある場合は置き換える（エイリアス追加後）
if [ -f "/workspace/.bashrc" ]; then
    echo "Merging custom .bashrc with ollama aliases..."
    # エイリアスを保持しつつカスタム.bashrcを適用
    tail -2 /home/klab/.bashrc > /tmp/ollama_aliases
    cp /workspace/.bashrc /home/klab/.bashrc
    cat /tmp/ollama_aliases >> /home/klab/.bashrc
    echo "Custom .bashrc applied with ollama aliases"
else
    echo "No custom .bashrc found in /workspace/"
fi

# Ollamaサービスの起動
echo "Starting Ollama service..."
/home/klab/start-ollama.sh &
sleep 3

# Ollamaが起動しているかチェック
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✅ Ollama service is running"
    echo "Available models:"
    ollama list
else
    echo "⚠️ Waiting for Ollama service..."
    sleep 5
    echo "Available models:"
    ollama list
fi

echo "🎉 Development environment is ready!"
echo "🤖 Ollama Coding Agent is available!"
echo ""
echo "Usage examples:"
echo "  olc \"Create a simple Python web server\""
echo "  ollama-code \"Add error handling to main.py\""
echo "  python3 /home/klab/ollama_code.py \"Write unit tests\""
echo ""
echo "Use 'sudo apt-get install <package>' to install additional tools as needed."