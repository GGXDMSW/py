import os

def is_ignored(path):
    ignored_dirs = {'.git', '__pycache__', '.idea', '.vscode', 'venv', 'env', 'node_modules', 'dist', 'build'}
    ignored_exts = {'.pyc', '.pyd', '.exe', '.dll', '.so', '.dylib', '.png', '.jpg', '.jpeg', '.gif', '.zip', '.tar', '.gz', '.ico', '.pdf', '.bak', '.json', '.txt', '.log'}
    
    parts = path.split(os.sep)
    if any(part in ignored_dirs for part in parts):
        return True
        
    ext = os.path.splitext(path)[1].lower()
    if ext in ignored_exts:
        return True
        
    if os.path.basename(path) == 'repo_context.md':
        return True
        
    return False

def pack_repo():
    output_file = 'repo_context.md'
    
    with open(output_file, 'w', encoding='utf-8') as out_f:
        out_f.write("# Repository Context\n\n")
        out_f.write("This file contains the complete, un-truncated source code of the repository to provide a full context.\n\n")
        
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if not is_ignored(os.path.join(root, d))]
            
            for file in files:
                file_path = os.path.join(root, file)
                if is_ignored(file_path):
                    continue
                    
                display_path = os.path.normpath(file_path).replace('\\', '/')
                if display_path.startswith('./'):
                    display_path = display_path[2:]
                    
                try:
                    with open(file_path, 'r', encoding='utf-8') as in_f:
                        content = in_f.read()
                        
                    out_f.write(f"## File: `{display_path}`\n\n")
                    
                    ext = os.path.splitext(file)[1].lower()
                    lang = ext[1:] if ext else 'text'
                    if lang == 'py': 
                        lang = 'python'
                    elif lang == 'md':
                        lang = 'markdown'
                    
                    out_f.write(f"```{lang}\n")
                    out_f.write(content)
                    if content and not content.endswith('\n'):
                        out_f.write('\n')
                    out_f.write("```\n\n")
                except Exception as e:
                    out_f.write(f"## File: `{display_path}`\n\n")
                    out_f.write(f"> Error reading file: {str(e)}\n\n")

if __name__ == '__main__':
    print("Packing repository into repo_context.md without truncation...")
    pack_repo()
    print("Done! repo_context.md is now fully updated.")
