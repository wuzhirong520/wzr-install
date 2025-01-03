import requests
from tqdm import tqdm
import time
import subprocess

def cmp_version(version1, version2):
    res = run_command(f"dpkg --compare-versions \'{version1}\' eq \'{version2}\' && echo True")
    if res=="True\n":
        return 0
    res = run_command(f"dpkg --compare-versions \'{version1}\' ge \'{version2}\' && echo True")
    if res=="True\n":
        return 1
    return -1
    
def run_command(command):
    """
    执行外部命令并捕获其输出。

    :param command: 字符串或列表形式的命令，例如 "ls -l" 或 ["ls", "-l"]
    :return: 命令的输出内容（字符串形式）
    """
    try:
        # 执行命令并捕获输出
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,  # 捕获标准输出
            stderr=subprocess.PIPE,  # 捕获标准错误
            text=True,  # 输出以字符串形式返回
            shell=isinstance(command, str)  # 如果是字符串命令，使用 shell 模式
        )
        # 返回标准输出（也可以同时返回 result.stderr 查看错误信息）
        return result.stdout
    except Exception as e:
        return f"Error occurred: {e}"

def download_file_with_progress(url, output_file):
    """
    下载文件并显示进度条和实时下载速度。

    :param url: 文件的下载链接
    :param output_file: 保存文件的路径
    """
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))  # 文件总大小
    block_size = 1024  # 每次读取的块大小（1KB）

    # 使用 tqdm 显示进度条
    with open(output_file, 'wb') as file, tqdm(
        desc=f"Downloading {output_file.split('/')[-1]}",
        total=total_size,
        unit='B',
        unit_scale=True,
        unit_divisor=1024,
        dynamic_ncols=True,  # 动态调整列宽
    ) as bar:
        downloaded = 0
        start_time = time.time()
        for data in response.iter_content(block_size):
            file.write(data)
            bar.update(len(data))
            downloaded += len(data)
            elapsed = time.time() - start_time
            if elapsed > 0:
                speed = downloaded / elapsed  # 计算速度
                bar.set_postfix(speed=f"{speed / 1024:.2f} KB/s")