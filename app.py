import os
import subprocess

import requests
from croniter import croniter
import time
from CloudFlare import CloudFlare


def send_telegram_message(bot_token, chat_id, message):
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message
        }
        response = requests.post(url, json=payload)
    except requests.exceptions.RequestException as e:
        print(f"发送消息异常: {e.response}")


def cf_dns_update(subdomain, ip_address):
    cf = CloudFlare(email=os.environ.get("EMAIL"), token=os.environ.get("TOKEN"))
    # Get the zone_id for your domain
    zones = cf.zones.get(params={'name': os.environ.get("MAINDOMAIN")})
    zone_id = zones[0]['id']
    # Get the DNS records for your domain
    dns_records = cf.zones.dns_records.get(zone_id)
    # Update the IP address for appropriate DNS record
    for record in dns_records:
        if record['name'] == subdomain and record['type'] == 'A':
            record_id = record['id']
            record_content = record['content']
            if record_content != ip_address:
                print(f"原IP为: {record_content}")
                data = {'type': 'A', 'name': subdomain, 'content': ip_address}
                cf.zones.dns_records.put(zone_id, record_id, data=data)
                print(f"更新后IP为: {ip_address}")
            break


def optimal_ip(message):
    # 定义要执行的 shell 命令或脚本
    shell_command = "./optimal_ip.sh"

    # 使用 subprocess 运行 shell 命令
    try:
        subprocess.run(shell_command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        message.append("😔IP筛选脚本运行异常")


def cfip_optimal(message):
    try:
        # 读取文件内容
        file_path = "/cloudflare/cf_result.txt"
        with open(file_path, 'r') as f:
            lines = f.readlines()
            if len(lines) < 2:
                return
            # 获取第二行的数据
            second_line = lines[1]
            # 分割每个字段
            fields = second_line.split(',')
            # 获取 IP 地址
            ip_address = fields[0]
            # 获取测试到的速度
            speed_url = fields[5].strip()

        # 开启实时通知
        if os.environ.get("PUSH_SWITCH") == "Y":
            message.append(f"😍IP优选结果\n{ip_address} - {speed_url}")

        if {speed_url} == "0.00":
            return

        # 更新DNS
        cf_dns_update(os.environ.get("DOMAIN"), ip_address)
    except Exception as e:
        print(f"IP优选异常{e}")


def cfbest_optimal(message):
    try:
        # 读取文件内容
        file_path = "/cloudflare/cf_result_1.txt"
        with open(file_path, 'r') as f:
            lines = f.readlines()
            if len(lines) < 2:
                return
            # 获取第二行的数据
            second_line = lines[1]
            # 分割每个字段
            fields = second_line.split(',')
            # 获取 IP 地址
            ip_address = fields[0]
            # 获取测试到的速度
            speed_url = fields[5].strip()

        # 读取文件内容
        # file_path2 = "/cloudflare/cf_result_0.txt"
        # with open(file_path2, 'r') as f2:
        #     lines2 = f2.readlines()
        #     if len(lines2) < 2:
        #         return
        #     # 获取第二行的数据
        #     second_line2 = lines2[1]
        #     # 分割每个字段
        #     fields2 = second_line2.split(',')
        #     # 获取 IP 地址
        #     ip_address2 = fields2[0]
        #     # 获取测试到的速度
        #     speed_url2 = fields2[5].strip()

        # 打印提取到的IPv4地址及对应速度
        # 开启实时通知
        if os.environ.get("PUSH_SWITCH") == "Y":
            message.append(f"😍cfBest优选结果\n{ip_address} - {speed_url}")
            # message.append(f"😍cfBest优选结果\n{ip_address} - {speed_url}\n{ip_address2} - {speed_url2}")

        # 更新DNS记录
        if {speed_url} != "0.00":
            cf_dns_update('cfbest.soapmans.eu.org', ip_address)
        # if {speed_url2} != "0.00":
        #     cf_dns_update('cfbest80.soapmans.eu.org', ip_address2)
    except Exception as e:
        print(f"cfBest优选异常:{e}")


def my_task():
    message = ["🎉优选IP已完成\n"]

    print("---Running my task---\n")

    print("---开始运行IP筛选脚本---")
    optimal_ip(message)
    print("---结束运行IP筛选脚本---\n")

    print("---开始IP优选DNS---")
    cfip_optimal(message)
    print("---结束IP优选DNS---\n")

    print("---开始cfBest优选---")
    cfbest_optimal(message)
    print("---结束cfBest优选---\n")

    print("---开始发送消息---")
    message_res = "\n".join(message)
    print(message_res)
    send_telegram_message(os.environ.get("BOT_TOKEN"), os.environ.get("CHAT_ID"), message_res)
    print("---结束发送消息---\n")

    print("---Running task successfully---")


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
