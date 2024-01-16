import os
from croniter import croniter
import time
import subprocess
import re
import requests


def update_dns():
    # 读取文件内容
    file_path = "path/to/your/file.txt"
    with open(file_path, 'r') as file:
        content = file.read()

    # 使用正则表达式提取IPv4地址
    ipv4_addresses = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', content)

    # 打印提取到的IPv4地址
    print("IPv4 Addresses:")
    for ip_address in ipv4_addresses:
        print(ip_address)

    # Cloudflare API 相关配置
    cloudflare_api_key = "your_cloudflare_api_key"
    cloudflare_email = "your_cloudflare_email"
    zone_id = "your_cloudflare_zone_id"
    dns_record_id = "your_dns_record_id"

    # 更新 CDN 记录
    for ip_address in ipv4_addresses:
        api_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{dns_record_id}"
        headers = {
            "X-Auth-Key": cloudflare_api_key,
            "X-Auth-Email": cloudflare_email,
            "Content-Type": "application/json"
        }
        data = {
            "type": "A",
            "name": "your.domain.com",  # 替换为你的域名
            "content": ip_address,
            "ttl": 120,  # 根据需要设置 TTL
            "proxied": True
        }

        # 发送更新请求
        response = requests.put(api_url, json=data, headers=headers)
        if response.status_code == 200:
            print(f"DNS record updated successfully for IP: {ip_address}")
        else:
            print(f"Failed to update DNS record for IP: {ip_address}, Status Code: {response.status_code}")


def optimal_ip():
    # 定义要执行的 shell 命令或脚本
    shell_command = "./optimal_ip.sh"

    # 使用 subprocess 运行 shell 命令
    try:
        subprocess.run(shell_command, shell=True, check=True)
        print("Command executed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error executing shell script: {e}")

    # update_dns()


def my_task():
    print("Running my task...")
    optimal_ip()
    print("Running task successfully")


# Docker 环境变量获取 cron 表达式，默认为每隔5分钟执行一次
cron_expression = os.environ.get("CRON_EXPRESSION", "*/5 * * * *")

# 创建 croniter 实例
cron = croniter(cron_expression, time.time())

while True:
    # 获取下一个执行时间
    next_execution_time = cron.get_next()
    # 等待直到下一个执行时间
    time.sleep(next_execution_time - time.time())
    # 执行任务
    my_task()
