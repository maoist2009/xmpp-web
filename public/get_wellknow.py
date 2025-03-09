import requests
import os

# 定义代理配置
proxies = {
    'http': 'http://127.0.0.1:2500',
    'https': 'http://127.0.0.1:2500'
}

# 检查 xmppservers 目录是否存在，不存在则创建
if not os.path.exists('xmppservers'):
    os.makedirs('xmppservers')

try:
    # 打开文件并逐行读取
    with open('all_server.txt', 'r') as file:
        for line in file:
            # 去除行尾的换行符
            domain = line.strip()
            # 构建请求的 URL
            url = f'https://{domain}/.well-known/host-meta'
            try:
                # 发送请求
                response = requests.get(url, proxies=proxies)
                # 检查响应状态码
                if response.status_code == 200:
                    print(f"成功获取 {url} 的内容，正在写入文件...")
                    # 构建文件路径
                    file_path = os.path.join('xmppservers', domain)
                    # 写入文件
                    with open(file_path, 'w', encoding='utf-8') as output_file:
                        output_file.write(response.text)
                    print(f"内容已成功写入 {file_path}")
                else:
                    print(f"请求 {url} 失败，状态码：{response.status_code}")
            except requests.RequestException as e:
                print(f"请求 {url} 时发生错误：{e}")
except FileNotFoundError:
    print("未找到 all_server.txt 文件，请确保该文件存在于当前目录下。")