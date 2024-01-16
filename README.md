# optimalIpCloudFlareDns
本地优选IP并更新cloudflareDns

# docker-compose示例
```
version: '3.7'

services:
  app:
    image: soapmans/optimalipcloudflaredns
    privileged: true
    network_mode: host
    restart: always
    environment:
      - TZ=Asia/Shanghai
      - CRON_EXPRESSION=*/5 * * * *
```