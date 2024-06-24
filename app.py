import json
import os

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


def cf_optimal(message):
    try:
        url = "https://api.hostmonit.com/get_optimization_ip"
        payload = {
            "key": "iDetkOys"
        }
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            data = json.loads(response.content)
            max_speed_ip = max((entry for entry in data['info']
                                if entry['node'] == 'QYZJBGP' and entry['ip'].startswith('104')),
                               key=lambda x: x['speed'])['ip']

            cf_dns_update(f"cfyes1.soapmans.eu.org", max_speed_ip)
            if os.environ.get("PUSH_SWITCH") == "Y":
                message.append(f"😍cfyes优选结果\n{max_speed_ip}")
    except Exception as e:
        print(f"cfYes优选异常:{e}")


def my_task():
    message = ["🎉优选IP已完成\n"]

    print("---Running my task---\n")

    print("---开始cfYes优选---")
    cf_optimal(message)
    print("---结束cfYes优选---\n")

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
