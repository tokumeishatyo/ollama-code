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
            
            # ディレクトリ作成（親ディレクトリも含めて）
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
- To write/create a file: WRITE_FILE: filename
```
file content here
```
- To run a command: RUN_COMMAND: command

IMPORTANT: Use exactly "WRITE_FILE:" (not CREATE_FILE or other variations) followed by the filename.

Task: {task}

Think step by step and take actions as needed. Always explain what you're doing and why."""

        print("🤖 Analyzing task and planning actions...")
        response = self.call_ollama(system_prompt)
        print(f"\\n📋 Plan:\\n{response}\\n")
        
        # デバッグ: レスポンスを詳細表示
        if "RUN_COMMAND:" in response or "WRITE_FILE:" in response or "CREATE_FILE:" in response:
            print("🔍 Debug: Found operations in response")
            print("Raw response lines:")
            for i, line in enumerate(response.split('\\n')):
                if 'RUN_COMMAND:' in line or 'WRITE_FILE:' in line or 'CREATE_FILE:' in line:
                    print(f"  {i}: '{line}'")
            print()
        
        # アクションを実行
        actions_taken = []
        lines = response.split('\\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # RUN_COMMAND の検出（優先処理）
            if "RUN_COMMAND:" in line:
                print(f"🔍 Debug: Found RUN_COMMAND in line: '{line}'")
                
                command = ""
                if line.startswith("RUN_COMMAND:"):
                    command = line.replace("RUN_COMMAND:", "").strip()
                elif "RUN_COMMAND:" in line:
                    parts = line.split("RUN_COMMAND:")
                    if len(parts) > 1:
                        command = parts[-1].strip()
                
                # コマンドのクリーンアップ
                command = command.replace('`', '').strip()
                command = command.replace('```', '').strip()
                
                if not command or len(command) > 200:
                    print(f"❌ Invalid command detected: '{command}', skipping...")
                else:
                    print(f"⚡ Running command: {command}")
                    result = self.run_command(command)
                    print(f"Result:\\n{result}\\n")
                    actions_taken.append(f"Ran: {command}")
                
            # ディレクトリ作成の検出
            elif ("TO_CREATE_DIRECTORY:" in line or 
                  "CREATE_DIRECTORY:" in line or 
                  "MKDIR:" in line or
                  ("mkdir" in line.lower() and ("フォルダ" in line or "ディレクトリ" in line))):
                
                print(f"🔍 Debug: Found directory creation in line: '{line}'")
                
                directory_name = ""
                if "TO_CREATE_DIRECTORY:" in line:
                    directory_name = line.split("TO_CREATE_DIRECTORY:")[-1].strip()
                elif "CREATE_DIRECTORY:" in line:
                    directory_name = line.split("CREATE_DIRECTORY:")[-1].strip()
                elif "MKDIR:" in line:
                    directory_name = line.split("MKDIR:")[-1].strip()
                else:
                    import re
                    match = re.search(r'([a-zA-Z0-9_-]+)(?:という|と|の)(?:フォルダ|ディレクトリ)', line)
                    if match:
                        directory_name = match.group(1)
                
                directory_name = directory_name.replace('`', '').strip()
                
                if directory_name and len(directory_name) < 50:
                    print(f"📁 Creating directory: {directory_name}")
                    result = self.run_command(f"mkdir -p {directory_name}")
                    print(f"Result:\\n{result}\\n")
                    actions_taken.append(f"Created directory: {directory_name}")
                else:
                    print(f"❌ Invalid directory name: '{directory_name}'")
                
            # READ_FILE の検出
            elif line.startswith("READ_FILE:"):
                filepath = line.replace("READ_FILE:", "").strip()
                print(f"📖 Reading file: {filepath}")
                content = self.read_file(filepath)
                print(f"File content preview:\\n{content[:500]}{'...' if len(content) > 500 else ''}\\n")
                actions_taken.append(f"Read {filepath}")
                
            # WRITE_FILE/CREATE_FILE の検出
            elif line.startswith("WRITE_FILE:") or line.startswith("CREATE_FILE:") or "WRITE_FILE:" in line:
                print(f"🔍 Debug: Processing file operation: '{line[:100]}...'")
                
                filepath = ""
                if line.startswith("WRITE_FILE:"):
                    filepath = line.replace("WRITE_FILE:", "").strip()
                elif line.startswith("CREATE_FILE:"):
                    filepath = line.replace("CREATE_FILE:", "").strip()
                elif "WRITE_FILE:" in line:
                    parts = line.split("WRITE_FILE:")
                    if len(parts) > 1:
                        filepath = parts[1].strip()
                
                filepath = filepath.replace('`', '').replace(':', '').strip()
                
                if ' ' in filepath:
                    filepath = filepath.split()[0]
                
                if not filepath or len(filepath) > 50 or '\\n' in filepath or filepath in ['mkdir', 'cd', 'touch', 'command', 'bash']:
                    print(f"❌ Invalid filepath detected: '{filepath}', skipping...")
                else:
                    print(f"✏️  Writing file: {filepath}")
                    
                    # コンテンツの検索と抽出
                    content_lines = []
                    i += 1
                    in_code_block = False
                    found_content = False
                    
                    search_limit = min(i + 10, len(lines))
                    while i < search_limit:
                        current_line = lines[i]
                        
                        if current_line.strip().startswith("```") and not current_line.strip().startswith("```bash"):
                            print(f"🔍 Debug: Found code block start at line {i}: '{current_line.strip()}'")
                            in_code_block = True
                            found_content = True
                            i += 1
                            continue
                        elif current_line.strip() == "```" and in_code_block:
                            print(f"🔍 Debug: Found code block end at line {i}")
                            break
                        elif in_code_block:
                            content_lines.append(current_line)
                        
                        i += 1
                    
                    if not found_content:
                        print("🔍 Debug: No code block found, creating empty file")
                        content_lines = [""]
                    
                    if content_lines:
                        content = "\\n".join(content_lines)
                        content = content.replace("**name**", "__name__")
                        
                        print(f"🔍 Debug: Writing content ({len(content_lines)} lines) to '{filepath}'")
                        result = self.write_file(filepath, content)
                        print(result)
                        actions_taken.append(f"Wrote {filepath}")
                    else:
                        print("❌ No content found for file creation")
                    
                    continue
            
            i += 1
        
        # 手動フォールバック処理
        if not actions_taken:
            print("ℹ️  No file operations were detected in the response.")
            print("🔍 Debug: Attempting manual file creation...")
            
            if "main.py" in task.lower():
                content = ""
                result = self.write_file("main.py", content)
                print(f"🛠️  Manual creation: {result}")
            elif any(keyword in task.lower() for keyword in ["フォルダを作", "ディレクトリを作", "folder", "directory"]):
                import re
                patterns = [
                    r'([a-zA-Z0-9_-]+)(?:という|と|の)(?:フォルダ|ディレクトリ)',
                    r'(?:フォルダ|ディレクトリ)(?:.*?)([a-zA-Z0-9_-]+)',
                    r'([a-zA-Z0-9_-]+)(?:.*?)(?:フォルダ|ディレクトリ)'
                ]
                
                directory_name = ""
                for pattern in patterns:
                    match = re.search(pattern, task)
                    if match:
                        directory_name = match.group(1)
                        break
                
                if directory_name:
                    result = self.run_command(f"mkdir -p {directory_name}")
                    print(f"🛠️  Manual directory creation: Created {directory_name}")
                    print(f"Result: {result}")
            elif any(keyword in task.lower() for keyword in ["ファイルを作成", "create", "file"]):
                import re
                file_patterns = re.findall(r'([a-zA-Z0-9_]+\.[a-zA-Z0-9]+)', task)
                if file_patterns:
                    filename = file_patterns[0]
                    content = ""
                    result = self.write_file(filename, content)
                    print(f"🛠️  Manual creation: {result}")
        else:
            print(f"✅ Actions completed: {', '.join(actions_taken)}")
        
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