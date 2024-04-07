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
        print(f"---开始插入数据---")
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
        print(f"---结束插入数据---")
    except Exception as e:
        send_telegram_message(os.environ.get("BOT_TOKEN"), os.environ.get("CHAT_ID"),
                              f"优选结果插入mysql异常")
        print(f"Error executing insert_update: {e}")


def send_telegram_message(bot_token, chat_id, message):
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message
        }
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("Message sent successfully!")
        else:
            print(f"Failed to send message. Error: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send message. Error: {e.response}")


def update_dns():
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

    # 打印提取到的IPv4地址及对应速度
    print(f"IPv4 Addresses & Speed: ${ip_address} - ${speed_url}")
    # 开启实时通知
    if os.environ.get("PUSH_SWITCH") == "Y":
        send_telegram_message(os.environ.get("BOT_TOKEN"), os.environ.get("CHAT_ID"),
                              f"优选结果: ${ip_address} - ${speed_url}")

    # 更新DNS记录
    print(f"---开始更新DNS记录---")
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
                print(f"原IP为: {record_content}")
                data = {'type': 'A', 'name': os.environ.get("DOMAIN"), 'content': ip_address}
                cf.zones.dns_records.put(zone_id, record_id, data=data)
                print(f"更新后IP为: {ip_address}")
                print(f"---结束更新DNS记录---")
                insert_update(record_content, ip_address, speed_url)
            break


def optimal_ip():
    # 定义要执行的 shell 命令或脚本
    shell_command = "./optimal_ip.sh"

    # 使用 subprocess 运行 shell 命令
    try:
        subprocess.run(shell_command, shell=True, check=True)
        print("Command executed successfully")
    except subprocess.CalledProcessError as e:
        send_telegram_message(os.environ.get("BOT_TOKEN"), os.environ.get("CHAT_ID"),
                              f"优选脚本optimal_ip执行异常")
        print(f"Error executing shell script: {e}")

    # 更新DNS
    try:
        update_dns()
    except Exception as e:
        send_telegram_message(os.environ.get("BOT_TOKEN"), os.environ.get("CHAT_ID"),
                              f"update_dns执行异常")
        print(f"update_dns Error: {e}")


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


def cfyes_optimal():
    try:
        print(f"cfyes_optimal start...")
        url = "https://api.hostmonit.com/get_optimization_ip"
        payload = {
            "key": "iDetkOys"
        }
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            parsed_data = json.loads(response.content)
            data_ips = [node_info['ip'] for node_info in parsed_data['info'] if node_info['node'] == 'QYZJBGP']
            cfyes_count = 1
            print(f"---开始更新cfyes DNS记录---")
            for ip in data_ips:
                cf_dns_update(f"cfyes{cfyes_count}.soapmans.eu.org", ip)
                cfyes_count += 1
            print(f"---结束更新cfyes DNS记录---")
            if os.environ.get("PUSH_SWITCH") == "Y":
                send_telegram_message(os.environ.get("BOT_TOKEN"), os.environ.get("CHAT_ID"),
                                      f"cfyes优选结果: ${data_ips}")
        else:
            print(f"cfyes_optimal Error: {response.text}")
    except Exception as e:
        send_telegram_message(os.environ.get("BOT_TOKEN"), os.environ.get("CHAT_ID"),
                              f"cfyes_optimal异常")
        print(f"cfyes_optimal Error: {e}")


def cfbest_optimal():
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
        print(f"cfbest_optimal IPv4 Addresses & Speed: ${ip_address} - ${speed_url}   ${ip_address2} - ${speed_url2}")
        # 开启实时通知
        if os.environ.get("PUSH_SWITCH") == "Y":
            send_telegram_message(os.environ.get("BOT_TOKEN"), os.environ.get("CHAT_ID"),
                                  f"cfbest_optimal优选结果: ${ip_address} - ${speed_url}   ${ip_address2} - ${speed_url2}")

        # 更新DNS记录
        print(f"---开始更新cfbestDNS记录---")
        cf_dns_update('cfbest.soapmans.eu.org', ip_address)
        cf_dns_update('cfbest80.soapmans.eu.org', ip_address2)
        print(f"---结束更新cfbestDNS记录---")
    except Exception as e:
        send_telegram_message(os.environ.get("BOT_TOKEN"), os.environ.get("CHAT_ID"),
                              f"cfbest_optimal异常")
        print(f"cfbest_optimal 异常")


def my_task():
    print("Running my task......")
    optimal_ip()
    print("Running task successfully")

    print("cfyes 开始获取优选......")
    cfyes_optimal()
    print("cfyes 优选完成......")

    print("cfbest 开始优选....")
    cfbest_optimal()
    print("cfbest 开始优选....")


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
