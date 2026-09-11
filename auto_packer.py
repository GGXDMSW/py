import os

# 核心目录白名单 (已核实并扩充当前仓库所有最新核心子模块)
core_dirs = [
    'config',
    'core',
    'gui',
    'gui_fluent',
    'pipelines',
    'services',
    'utils'
]

# 核心文件白名单
core_files = [
    'main.py',
    'main_fluent.py',
    'AGENTS.md'
]

# 忽略的目录和文件特征
ignore_dirs = ['__pycache__', '.git', '.idea', '.vscode']
ignore_exts = ['.pyc', '.bak', '.zip', '.json', '.txt', '.js']

def generate_tree(startpath):
    tree_str = ""
    for root, dirs, files in os.walk(startpath):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * level
        tree_str += f"{indent}{os.path.basename(root)}/\n"
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            if not any(f.endswith(ext) for ext in ignore_exts):
                tree_str += f"{subindent}{f}\n"
    return tree_str

def pack_code():
    output_file = 'repo_context.md'
    
    with open(output_file, 'w', encoding='utf-8') as out:
        out.write("# Repository Global Context\n\n")
        
        out.write("## Directory Tree\n```text\n")
        out.write(generate_tree('.'))
        out.write("```\n\n")
        
        out.write("## Core Files\n\n")
        for file in core_files:
            if os.path.exists(file):
                out.write(f"### File: {file}\n```python\n")
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        out.write(f.read())
                except Exception as e:
                    out.write(f"# Error reading file: {e}")
                out.write("\n```\n\n")
                
        out.write("## Core Modules\n\n")
        for d in core_dirs:
            if os.path.exists(d):
                for root, dirs, files in os.walk(d):
                    dirs[:] = [dir_name for dir_name in dirs if dir_name not in ignore_dirs]
                    for file in files:
                        if file.endswith('.py') or file.endswith('.md'):
                            filepath = os.path.join(root, file)
                            filepath_posix = filepath.replace('\\', '/')
                            out.write(f"### File: {filepath_posix}\n```python\n")
                            try:
                                with open(filepath, 'r', encoding='utf-8') as f:
                                    out.write(f.read())
                            except Exception as e:
                                out.write(f"# Error reading file: {e}")
                            out.write("\n```\n\n")

if __name__ == '__main__':
    pack_code()
    print("Successfully generated repo_context.md with complete core modules.")
