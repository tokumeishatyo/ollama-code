#!/usr/bin/env python3
"""
Ollama Coding Agent - Claude Code風のターミナルベースコーディングアシスタント
使用方法: python ollama_code.py [タスクの説明（オプション）]
"""

import sys
import os
import subprocess
import requests
import json
import argparse
from pathlib import Path
import tempfile

class OllamaCodingAgent:
    def __init__(self, model="mistral:latest", base_url="http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.work_dir = Path.cwd()
        
    def call_ollama(self, prompt: str) -> str:
        """Ollamaにプロンプトを送信"""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # 一貫性重視
                        "top_p": 0.9
                    }
                }
            )
            return response.json()['response']
        except Exception as e:
            return f"Error calling Ollama: {str(e)}"
    
    def get_available_models(self) -> list:
        """利用可能なモデル一覧を取得"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            models = response.json().get('models', [])
            return [model['name'] for model in models]
        except Exception as e:
            print(f"❌ Error getting models: {str(e)}")
            return []
    
    def select_model(self) -> str:
        """モデル選択インターフェース"""
        models = self.get_available_models()
        
        if not models:
            print("❌ No models available. Please install a model first.")
            print("Example: ollama pull mistral:latest")
            return None
        
        print("🤖 Available models:")
        for i, model in enumerate(models, 1):
            print(f"  {i}. {model}")
        
        while True:
            try:
                choice = input(f"\nSelect model (1-{len(models)}): ").strip()
                if choice.isdigit():
                    index = int(choice) - 1
                    if 0 <= index < len(models):
                        selected_model = models[index]
                        print(f"✅ Selected: {selected_model}")
                        return selected_model
                print(f"Please enter a number between 1 and {len(models)}")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                return None
            except Exception:
                print("Invalid input. Please try again.")
    
    def analyze_directory(self) -> str:
        """現在のディレクトリ構造を分析"""
        files_info = []
        
        for file_path in self.work_dir.rglob("*"):
            if file_path.is_file() and not any(skip in str(file_path) for skip in ['.git', '__pycache__', '.venv', 'node_modules']):
                try:
                    size = file_path.stat().st_size
                    if size < 10000:  # 10KB以下のファイルのみ詳細表示
                        files_info.append(f"📁 {file_path.relative_to(self.work_dir)} ({size} bytes)")
                    else:
                        files_info.append(f"📁 {file_path.relative_to(self.work_dir)} ({size} bytes) [large file]")
                except:
                    pass
        
        return "\\n".join(files_info[:20])  # 最大20ファイルまで
    
    def read_file(self, filepath: str) -> str:
        """ファイルを読み込み"""
        try:
            path = Path(filepath)
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if len(content) > 5000:
                        return content[:5000] + "\\n... [truncated]"
                    return content
            return f"File not found: {filepath}"
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    def write_file(self, filepath: str, content: str) -> str:
        """ファイルを作成/更新"""
        try:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"✅ Created/updated: {filepath}"
        except Exception as e:
            return f"❌ Error writing file: {str(e)}"
    
    def run_command(self, command: str) -> str:
        """シェルコマンドを実行"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                cwd=self.work_dir,
                timeout=30
            )
            
            output = f"Exit code: {result.returncode}\\n"
            if result.stdout:
                output += f"Output:\\n{result.stdout}\\n"
            if result.stderr:
                output += f"Error:\\n{result.stderr}\\n"
            return output
        except subprocess.TimeoutExpired:
            return "❌ Command timed out after 30 seconds"
        except Exception as e:
            return f"❌ Error running command: {str(e)}"
    
    def extract_code_blocks(self, text: str) -> list:
        """コードブロックを抽出"""
        import re
        
        # ```language または ``` で囲まれたコードブロックを抽出
        pattern = r'```(?:\\w+)?\\n(.*?)```'
        blocks = re.findall(pattern, text, re.DOTALL)
        return blocks
    
    def execute_task(self, task: str) -> str:
        """タスクを実行"""
        directory_info = self.analyze_directory()
        
        system_prompt = f"""You are a coding assistant similar to Claude Code. You help users with programming tasks by:
1. Analyzing the current directory structure
2. Reading existing files when needed
3. Writing/modifying code files
4. Running commands to test or execute code
5. Providing explanations for your actions

Current directory: {self.work_dir}
Directory structure:
{directory_info}

For each action you want to take, use the following format:
- To read a file: READ_FILE: filename
- To write a file: WRITE_FILE: filename
```
file content here
```
- To run a command: RUN_COMMAND: command

Task: {task}

Think step by step and take actions as needed. Always explain what you're doing and why."""

        print("🤖 Analyzing task and planning actions...")
        response = self.call_ollama(system_prompt)
        print(f"\\n📋 Plan:\\n{response}\\n")
        
        # アクションを実行
        actions_taken = []
        lines = response.split('\\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith("READ_FILE:"):
                filepath = line.replace("READ_FILE:", "").strip()
                print(f"📖 Reading file: {filepath}")
                content = self.read_file(filepath)
                print(f"File content preview:\\n{content[:500]}{'...' if len(content) > 500 else ''}\\n")
                actions_taken.append(f"Read {filepath}")
                
            elif line.startswith("WRITE_FILE:"):
                filepath = line.replace("WRITE_FILE:", "").strip()
                print(f"✏️  Writing file: {filepath}")
                
                # 次の```までのコンテンツを取得
                content_lines = []
                i += 1
                in_code_block = False
                
                while i < len(lines):
                    current_line = lines[i]
                    if current_line.strip() == "```" and not in_code_block:
                        in_code_block = True
                    elif current_line.strip() == "```" and in_code_block:
                        break
                    elif in_code_block:
                        content_lines.append(current_line)
                    i += 1
                
                if content_lines:
                    content = "\\n".join(content_lines)
                    result = self.write_file(filepath, content)
                    print(result)
                    actions_taken.append(f"Wrote {filepath}")
                
            elif line.startswith("RUN_COMMAND:"):
                command = line.replace("RUN_COMMAND:", "").strip()
                print(f"⚡ Running command: {command}")
                result = self.run_command(command)
                print(f"Result:\\n{result}\\n")
                actions_taken.append(f"Ran: {command}")
            
            i += 1
        
        if actions_taken:
            print(f"✅ Actions completed: {', '.join(actions_taken)}")
        else:
            print("ℹ️  No file operations were needed for this task.")
        
        return response

    def interactive_mode(self):
        """インタラクティブモード"""
        print(f"🚀 Ollama Coding Agent - Interactive Mode")
        print(f"📍 Working directory: {self.work_dir}")
        print(f"🤖 Model: {self.model}\\n")
        
        print("Commands:")
        print("  - Type your coding task")
        print("  - 'exit' or 'quit' to leave")
        print("  - 'model' to change model")
        print("  - 'help' for help\\n")
        
        while True:
            try:
                task = input("💬 Task: ").strip()
                
                if task.lower() in ['exit', 'quit', 'q']:
                    print("👋 Goodbye!")
                    break
                elif task.lower() == 'help':
                    print("\\nExample tasks:")
                    print("  - Write a Python program that calculates factorial")
                    print("  - Create a simple web server in Node.js")
                    print("  - Add error handling to main.py")
                    print("  - Write unit tests for the calculator module")
                    print("  - Create a README.md for this project\\n")
                elif task.lower() == 'model':
                    new_model = self.select_model()
                    if new_model:
                        self.model = new_model
                elif task:
                    print(f"\\n🎯 Executing: {task}")
                    self.execute_task(task)
                    print("\\n" + "="*50 + "\\n")
                
            except KeyboardInterrupt:
                print("\\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Ollama Coding Agent - Claude Code風のアシスタント")
    parser.add_argument("task", nargs='*', help="実行したいタスクの説明（省略するとインタラクティブモード）")
    parser.add_argument("--model", help="使用するOllamaモデル（指定しない場合は選択画面表示）")
    parser.add_argument("--url", default="http://localhost:11434", help="OllamaのベースURL")
    
    args = parser.parse_args()
    
    agent = OllamaCodingAgent(base_url=args.url)
    
    # モデル選択
    if args.model:
        agent.model = args.model
        print(f"🤖 Using model: {args.model}")
    else:
        selected_model = agent.select_model()
        if not selected_model:
            return
        agent.model = selected_model
    
    # タスクが指定されている場合は一回実行、そうでなければインタラクティブモード
    if args.task:
        task = " ".join(args.task)
        print(f"\\n🎯 Executing: {task}")
        agent.execute_task(task)
    else:
        agent.interactive_mode()

if __name__ == "__main__":
    main()