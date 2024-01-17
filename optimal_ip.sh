#!/bin/bash

[[ ! -d "/cloudflare" ]] && mkdir -p /cloudflare
cd /cloudflare

arch=$(uname -m)
if [[ ${arch} =~ "x86" ]]; then
	tag="amd"
	[[ ${arch} =~ "64" ]] && tag="amd64"
elif [[ ${arch} =~ "aarch" ]]; then
	tag="arm"
	[[ ${arch} =~ "64" ]] && tag="arm64"
else
	exit 1
fi



version=$(curl -s https://api.github.com/repos/XIU2/CloudflareSpeedTest/tags | sed -n 's/.*"name": "\(.*\)".*/\1/p' | head -n 1)
old_version=$(cat CloudflareST_version.txt )

if [[ ! -f "CloudflareST" || ${version} != ${old_version} ]]; then
	rm -rf CloudflareST_linux_${tag}.tar.gz
	wget -N https://github.com/XIU2/CloudflareSpeedTest/releases/download/${version}/CloudflareST_linux_${tag}.tar.gz
	echo "${version}" > CloudflareST_version.txt
	tar -xvf CloudflareST_linux_${tag}.tar.gz
	chmod +x CloudflareST
fi

# 新的默认网关IP
new_gateway="192.168.31.1"
# 更新默认网关
ip route change default via $new_gateway
echo "默认网关已更改为: $new_gateway"

./CloudflareST -tll 40 -tl 200 -n 400 -url https://speedtest.soapmans.eu.org -o cf_result.txt

# 新的默认网关IP
new_gateway="192.168.31.111"
# 更新默认网关
ip route change default via $new_gateway
echo "默认网关已更改为: $new_gateway"
