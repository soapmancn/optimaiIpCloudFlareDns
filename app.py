import json
import os

import requests
from croniter import croniter
import time
import subprocess
from CloudFlare import CloudFlare
import mysql.connector
from datetime import datetime


def insert_update(record_content, ip_address, speed_url):
    try:
        # 建立数据库连接
        conn = mysql.connector.connect(
            host=os.environ.get("MYSQLHOST"),
            user=os.environ.get("MYSQLROOT"),
            password=os.environ.get("MYSQLPASSWORD"),
            database=os.environ.get("MYSQLDB")
        )
        # 创建游标对象
        cursor = conn.cursor()
        # 获取当前日期和时间
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # 插入一条记录
        sql = "INSERT INTO cf_ips (update_date, previous_ip, updated_ip, speed_test) VALUES (%s, %s, %s, %s)"
        values = (now, record_content, ip_address, speed_url + "MB/S")
        cursor.execute(sql, values)
        # 提交更改
        conn.commit()
        # 关闭游标和连接
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error executing insert_update: {e}")


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


def update_dns(message):
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
        speed_url = fields[5]

    # 开启实时通知
    if os.environ.get("PUSH_SWITCH") == "Y":
        message += f"优选IP结果：${ip_address} - ${speed_url}\n"

    if {speed_url} == "0.00":
        return

    # 更新DNS记录
    cf = CloudFlare(email=os.environ.get("EMAIL"), token=os.environ.get("TOKEN"))
    # Get the zone_id for your domain
    zones = cf.zones.get(params={'name': os.environ.get("MAINDOMAIN")})
    zone_id = zones[0]['id']
    # Get the DNS records for your domain
    dns_records = cf.zones.dns_records.get(zone_id)
    # Update the IP address for appropriate DNS record
    for record in dns_records:
        if record['name'] == os.environ.get("DOMAIN") and record['type'] == 'A':
            record_id = record['id']
            record_content = record['content']
            if record_content != ip_address:
                data = {'type': 'A', 'name': os.environ.get("DOMAIN"), 'content': ip_address}
                cf.zones.dns_records.put(zone_id, record_id, data=data)
                insert_update(record_content, ip_address, speed_url)
            break


def optimal_ip(message):
    # 定义要执行的 shell 命令或脚本
    shell_command = "./optimal_ip.sh"

    # 使用 subprocess 运行 shell 命令
    try:
        subprocess.run(shell_command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        message += "优选IP脚本异常\n"
    # 更新DNS
    try:
        update_dns(message)
    except Exception as e:
        message += "优选IP更新DNS异常"


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


def cfyes_optimal(message):
    try:
        url = "https://api.hostmonit.com/get_optimization_ip"
        payload = {
            "key": "iDetkOys"
        }
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            parsed_data = json.loads(response.content)
            data_ips = [node_info['ip'] for node_info in parsed_data['info'] if node_info['node'] == 'QYZJBGP']
            cfyes_count = 1
            for ip in data_ips:
                cf_dns_update(f"cfyes{cfyes_count}.soapmans.eu.org", ip)
                cfyes_count += 1
            if os.environ.get("PUSH_SWITCH") == "Y":
                message += f"cfYes优选结果：${data_ips}\n"
    except Exception as e:
        message += f"cfYes优选异常\n"


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
            speed_url = fields[5]

        # 读取文件内容
        file_path2 = "/cloudflare/cf_result_0.txt"
        with open(file_path2, 'r') as f2:
            lines2 = f2.readlines()
            if len(lines2) < 2:
                return
            # 获取第二行的数据
            second_line2 = lines2[1]
            # 分割每个字段
            fields2 = second_line2.split(',')
            # 获取 IP 地址
            ip_address2 = fields2[0]
            # 获取测试到的速度
            speed_url2 = fields2[5]

        # 打印提取到的IPv4地址及对应速度
        # 开启实时通知
        if os.environ.get("PUSH_SWITCH") == "Y":
            message += f"cfBest优选结果: ${ip_address} - ${speed_url}   ${ip_address2} - ${speed_url2}\n"

        # 更新DNS记录
        if {speed_url} != "0.00":
            cf_dns_update('cfbest.soapmans.eu.org', ip_address)
        if {speed_url2} != "0.00":
            cf_dns_update('cfbest80.soapmans.eu.org', ip_address2)
    except Exception as e:
        message += f"cfBest优选异常\n"


def my_task():
    message = "\n😀优选IP已完成\n"

    print("---Running my task---")
    print("---开始IP优选---")
    optimal_ip(message)
    print("---结束IP优选---")

    print("---开始cfYes优选---")
    cfyes_optimal(message)
    print("---结束cfYes优选---")

    print("---开始cfBest优选---")
    cfbest_optimal(message)
    print("---结束cfBest优选---")

    print("---开始发送消息---")
    send_telegram_message(os.environ.get("BOT_TOKEN"), os.environ.get("CHAT_ID"), message)
    print("---结束发送消息---")

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
