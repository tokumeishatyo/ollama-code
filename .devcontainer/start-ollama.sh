#!/bin/bash

# Ollamaサービスを背景で起動
ollama serve &

# サービスが起動するまで待機
sleep 5

# コンテナを起動状態に保つ
exec tail -f /dev/null