# Custom .bashrc for Ollama development

# 基本設定
export PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]:\[\e[31m\]$(branch=$(git branch --show-current 2>/dev/null); [ -n "$branch" ] && echo "($branch)\[\e[0m\]:")\[\e[0m\]\$'
export EDITOR=vim

# エイリアス
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias ..='cd ..'
alias ...='cd ../..'

# Ollama関連のエイリアス
alias models='ollama list'
alias orun='ollama run'
alias opull='ollama pull'
alias ops='ollama ps'

# 環境変数
export OLLAMA_HOST=localhost:11434

echo "🤖 Welcome to Ollama Development Environment"
echo "Available commands: models, orun, opull, ops"
echo "Coding Agent: olc, ollama-code"
echo "Install tools as needed: sudo apt-get install <package>"

# Ollama Coding Agent のエイリアスは setup.sh で自動追加されます