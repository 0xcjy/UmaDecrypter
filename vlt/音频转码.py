print('使用前确认: 下载 vgmstream-cli 并添加到环境变量或者放到此程序同目录下')

import os
import subprocess
import json

src_dir = 'E:\\program\\UmaDecryptor\\dat\\sound'#示例文件夹，替换成你的
dst_dir = 'E:\\program\\UmaDecryptor\\audio\\exported_sound'#示例文件夹，替换成你的

function_list = [
    '单角色音频导出',
    '导出所有名字包含"valentine"的音频文件'
]

def run_cmd(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        if result.stderr:
            print(f"错误: \n{result.stderr}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败，退出码 {e.returncode}: {' '.join(command) if isinstance(command, list) else command}")
        print(f"输出: \n{e.stdout}\n错误: \n{e.stderr}")
        return None
    except FileNotFoundError:
        print(f"错误: 找不到命令: {' '.join(command) if isinstance(command, list) else command}")
        return None

def parent(path):
    abs_path = os.path.abspath(path)
    parent_dir = os.path.dirname(abs_path)
    parent_name = os.path.basename(parent_dir)
    return parent_name

def single_chara_export(chara_id): # 单角色音频导出
    def check_file(root, file, chara_id): # 检查文件是否为指定角色的音频文件
        full_path = os.path.join(root, file)
        if file.endswith('.awb') and len(file) >= 10:
            if parent(root) == 'l' or parent(full_path) in ['c','v']:
                if file[-10:-6] == chara_id or (file[-11:-7] == chara_id and file[-12] == '_'):
                    return True
        return False

    def count_stream(full_path): # 统计音频文件的流数量
        os.makedirs(dst_dir_chara, exist_ok=True)
        command = [vgmstream_cli, "-I", full_path]
        result = run_cmd(command)
        if result is None:
            return
        meta = json.loads(result)
        total = meta['streamInfo']['total']
        return total

    def process(full_path, file, total): # 处理音频文件
        if total <= 1:
            command = [vgmstream_cli, "-o", os.path.join(dst_dir_chara, file.replace('.awb', '.wav')), full_path]
        elif total > 1 and total < 10:
            command = [vgmstream_cli, "-S", "0", "-o", os.path.join(dst_dir_chara, f'{file.replace(".awb", "")}_?s.wav'), full_path]
        elif total >= 10 and total < 100:
            command = [vgmstream_cli, "-S", "0", "-o", os.path.join(dst_dir_chara, f'{file.replace(".awb", "")}_?02s.wav'), full_path]
        else:
            command = [vgmstream_cli, "-S", "0", "-o", os.path.join(dst_dir_chara, f'{file.replace(".awb", "")}_?04s.wav'), full_path]
        run_cmd(command)
        if os.path.exists(full_path + '.wav'):
            os.remove(full_path + '.wav')
        if total > 1:
            if os.path.exists(os.path.join(dst_dir_chara, file.replace('.awb', '.wav'))):
                os.remove(os.path.join(dst_dir_chara, file.replace('.awb', '.wav')))

    file_list = []
    total_stream = 0
    print(f'正在统计 {chara_id} 的所有音频文件信息')
    for root, _, files in os.walk(src_dir):
        for file in files:
            if check_file(root, file, chara_id):
                vgmstream_cli = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vgmstream-cli.exe")
                dst_dir_chara = os.path.join(dst_dir, chara_id)
                total = count_stream(os.path.join(root, file))
                total_stream += total
                file_list.append((os.path.join(root, file), total))
                print(f'{len(file_list)}. 文件 {file} 有 {total} 个流, 目前一共有 {total_stream} 个流')
    print(f'共统计到 {len(file_list)} 个文件, 包含 {total_stream} 个流, 开始处理...')
    for file, total in file_list:
        process(file, os.path.basename(file), total)
        print(f'文件 {os.path.basename(file)} 处理完成')
    print(f'所有音频成功导出!')

def export_valentine_audio(): # 导出所有名字包含"valentine"的音频文件
    def check_file_valentine(root, file):
        full_path = os.path.join(root, file)
        if file.endswith('.awb') and "valentine" in file.lower():
            return True
        return False

    def count_stream_valentine(full_path):
        os.makedirs(dst_dir_valentine, exist_ok=True)
        command = [vgmstream_cli, "-I", full_path]
        result = run_cmd(command)
        if result is None:
            return
        meta = json.loads(result)
        total = meta['streamInfo']['total']
        return total

    def process_valentine(full_path, file, total):
        # Extract the core ID from the filename (e.g., '1234' from 'snd_voi_valentine_123400.awb')
        # Assuming the format is always 'snd_voi_valentine_XXXX00.awb'
        file_without_ext = file.replace('.awb', '')
        # Find the index after 'snd_voi_valentine_' and before '00'
        prefix = 'snd_voi_valentine_'
        suffix_len = 2 # for '00'
        if prefix in file_without_ext and file_without_ext.endswith('00'):
            start_index = file_without_ext.find(prefix) + len(prefix)
            end_index = len(file_without_ext) - suffix_len
            new_base_name = file_without_ext[start_index:end_index]
        else:
            # Fallback if the expected pattern is not found
            new_base_name = file_without_ext

        if total <= 1:
            command = [vgmstream_cli, "-o", os.path.join(dst_dir_valentine, f'{new_base_name}.wav'), full_path]
        elif total > 1 and total < 10:
            command = [vgmstream_cli, "-S", "0", "-o", os.path.join(dst_dir_valentine, f'{new_base_name}_?s.wav'), full_path]
        elif total >= 10 and total < 100:
            command = [vgmstream_cli, "-S", "0", "-o", os.path.join(dst_dir_valentine, f'{new_base_name}_?02s.wav'), full_path]
        else:
            command = [vgmstream_cli, "-S", "0", "-o", os.path.join(dst_dir_valentine, f'{new_base_name}_?04s.wav'), full_path]
        run_cmd(command)
        if os.path.exists(full_path + '.wav'):
            os.remove(full_path + '.wav')
        if total > 1:
            if os.path.exists(os.path.join(dst_dir_valentine, file.replace('.awb', '.wav'))):
                os.remove(os.path.join(dst_dir_valentine, file.replace('.awb', '.wav')))

    file_list = []
    total_stream = 0
    print(f'正在统计所有名字包含"valentine"的音频文件信息')
    for root, _, files in os.walk(src_dir):
        for file in files:
            if check_file_valentine(root, file):
                vgmstream_cli = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vgmstream-cli.exe")
                dst_dir_valentine = os.path.join(dst_dir, "valentine_audios")
                total = count_stream_valentine(os.path.join(root, file))
                total_stream += total
                file_list.append((os.path.join(root, file), total))
                print(f'{len(file_list)}. 文件 {file} 有 {total} 个流, 目前一共有 {total_stream} 个流')
    print(f'共统计到 {len(file_list)} 个文件, 包含 {total_stream} 个流, 开始处理...')
    for file, total in file_list:
        process_valentine(file, os.path.basename(file), total)
        print(f'文件 {os.path.basename(file)} 处理完成')
    print(f'所有名字包含"valentine"的音频成功导出!')
                    
if __name__ == "__main__":
    while True:
        numbered_functions = [f"{i+1}. {func}" for i, func in enumerate[str](function_list)]
        func = input('功能列表\n' + '\n'.join(numbered_functions) + '\n请输入要执行第几个功能(输入0退出): ' )
        if not func.isdigit():
            print("请输入一个数字")
            continue
        func = int(func) - 1
        if 0 <= func < len(function_list):
            if func == 0:
                chara_id = input('请输入要导出的角色ID: ')
                single_chara_export(chara_id)
            elif func == 1:
                export_valentine_audio()
        elif func == -1:
            break
        else:
            print("无效的选择")
    print("程序退出")
