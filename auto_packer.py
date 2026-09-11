import os

def write_file_to_md(file_path, out_f):
    try:
        with open(file_path, 'r', encoding='utf-8') as in_f:
            content = in_f.read()
        out_f.write(f"```python\n")
        out_f.write(f"File: {file_path}\n")
        out_f.write(f"{content}\n")
        out_f.write(f"```\n\n")
    except Exception as e:
        print(f"读取文件 {file_path} 失败: {e}")

def pack_source_code():
    core_dirs = ['gui_fluent']
    core_files = ['main_fluent.py']
    output_file = 'repo_context.md'
    
    with open(output_file, 'w', encoding='utf-8') as out_f:
        for file_name in core_files:
            if os.path.exists(file_name) and file_name.endswith('.py'):
                write_file_to_md(file_name, out_f)
        
        for dir_name in core_dirs:
            if not os.path.exists(dir_name):
                continue
            for root, dirs, files in os.walk(dir_name):
                if '__pycache__' in dirs:
                    dirs.remove('__pycache__')
                if '.git' in dirs:
                    dirs.remove('.git')
                    
                for file_name in files:
                    if file_name.endswith('.py'):
                        file_path = os.path.join(root, file_name)
                        file_path = file_path.replace('\\', '/')
                        write_file_to_md(file_path, out_f)

if __name__ == '__main__':
    pack_source_code()
    print("源码打包完成，已生成至根目录的 repo_context.md 文件中。")
