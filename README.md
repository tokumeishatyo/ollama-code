# Ollama DevContainer with Coding Agent

Docker Desktop + VS Code + Ollama を使用したローカル LLM 開発環境です。Claude Code 風のターミナルベースコーディングアシスタント付き。

## 🚀 特徴

- **既存の Ollama データを活用**: インストール済みモデルをそのまま利用
- **GPU サポート**: NVIDIA GPU による高速推論
- **Claude Code 風エージェント**: ターミナルからの自然言語コーディング指示
- **完全な開発環境**: Python, Git, sudo 権限付き

## 📋 前提条件

### 必須要件
- **Docker Desktop** (GPU サポート有効)
- **VS Code** + Dev Containers 拡張機能
- **既存の Ollama 環境**:
  - `ollama` という名前のボリューム
  - `ollama/ollama` イメージ
  - インストール済みのモデル

### GPU サポート (推奨)
- NVIDIA GPU
- NVIDIA Container Runtime
- Docker Desktop で GPU サポート有効化

### 既存環境の確認
```bash
# Ollama ボリュームの確認
docker volume ls | grep ollama

# インストール済みモデルの確認
docker run --rm -v ollama:/root/.ollama ollama/ollama ollama list
```

## 🔧 セットアップ

### 1. プロジェクトディレクトリ作成
```bash
mkdir my-ollama-project
cd my-ollama-project
```

### 2. DevContainer 設定ファイルの配置
以下のディレクトリ構造で設定ファイルを配置：

```
my-ollama-project/
├── .devcontainer/
│   ├── devcontainer.json
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── start-ollama.sh
│   ├── setup.sh
│   └── ollama_code.py
├── .bashrc (オプション)
└── (your project files)
```

### 3. 既存 Ollama コンテナの停止
```bash
# 重要: 既存の ollama コンテナを停止
docker stop ollama
```

### 4. VS Code でコンテナを起動
1. VS Code でプロジェクトフォルダを開く
2. コマンドパレット (`Ctrl+Shift+P`) を開く
3. "Dev Containers: Reopen in Container" を選択
4. 初回ビルド完了まで待機 (5-10分)

## 🎯 使い方

### Ollama の基本操作
```bash
# インストール済みモデルの確認
ollama list
# または
models

# モデルの実行
ollama run mistral:latest
# または  
orun mistral:latest

# プロセス確認
ollama ps
# または
ops
```

### Coding Agent の使用

#### インタラクティブモード (推奨)
```bash
# エイリアスで起動
ollama-code

# または直接実行
python3 /home/klab/ollama_code.py
```

**実行例**:
```bash
klab@ollama-dev:/workspace$ ollama-code

🤖 Available models:
  1. mistral:latest
  2. codegemma:7b-instruct
  3. phi4-reasoning:latest

Select model (1-3): 2
✅ Selected: codegemma:7b-instruct

💬 Task: Create a Python web server that serves static files
🤖 Analyzing task and planning actions...
```

#### ワンショット実行
```bash
# 引用符で囲んで実行
ollama-code "Write a C program that prints Hello World"

# 複数単語も可能
ollama-code Write unit tests for main.py
```

### Coding Agent のコマンド

インタラクティブモード中で使用可能：
- **タスク入力**: 自然言語でコーディング指示
- **`help`**: 使用例とヘルプ表示
- **`model`**: 使用モデルの変更
- **`exit`**, **`quit`**, **`q`**: 終了
- **Ctrl+C**: 強制終了

### 実用的なタスク例

```bash
💬 Task: Create a REST API with Flask for a todo application
💬 Task: Add error handling and logging to main.py  
💬 Task: Write comprehensive unit tests for the calculator module
💬 Task: Create a professional README.md for this project
💬 Task: Fix the import error in app.py and make it executable
💬 Task: Implement a simple JWT authentication system
```

## 🛠️ 高度な設定

### カスタム .bashrc の使用
プロジェクトルートに `.bashrc` を配置すると、コンテナ起動時に自動適用：

```bash
# Custom .bashrc example
export PS1='\[\033[01;32m\]\u@ollama-dev\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
alias ll='ls -alF'
# (Ollama関連のエイリアスは自動追加)
```

### 追加パッケージのインストール
```bash
# 開発ツールの追加インストール
sudo apt-get update && sudo apt-get install -y vim htop

# Python パッケージの追加
pip install numpy pandas matplotlib
```

### GPU 使用状況の確認
```bash
# GPU 認識確認
nvidia-smi

# Ollama の GPU 使用確認 (モデル実行時に高速化)
ollama run mistral:latest
```

## 🐛 トラブルシューティング

### よくある問題

**Q: `ollama list` で "permission denied" エラー**
```bash
# 権限修正
sudo chown -R klab:klab /home/klab/.ollama
```

**Q: GPU が認識されない**
- Docker Desktop で GPU サポートが有効か確認
- `nvidia-smi` コマンドで GPU が見えるか確認

**Q: モデルが見つからない**
```bash
# 既存 ollama コンテナが停止しているか確認
docker ps | grep ollama

# ボリュームのマウント確認
docker inspect ollama_dev | grep -A 10 Mounts
```

**Q: Coding Agent が応答しない**
- Ollama サービスが起動しているか確認: `curl http://localhost:11434/api/tags`
- モデルが存在するか確認: `ollama list`

### ログの確認
```bash
# Ollama サービスログ
docker logs ollama_dev

# コンテナ内でのデバッグ
curl http://localhost:11434/api/tags
```

## 📝 ライセンス

MIT License

## 🤝 コントリビューション

Issues and Pull Requests are welcome!

---

**Happy Coding with Ollama! 🤖✨**
