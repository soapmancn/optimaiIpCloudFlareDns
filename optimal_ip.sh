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

# 定义代理服务器地址、端口以及用户名和密码
authProxy=$PROXIES

version=$(curl -x ${authProxy} -s https://api.github.com/repos/XIU2/CloudflareSpeedTest/tags | sed -n 's/.*"name": "\(.*\)".*/\1/p' | head -n 1)
old_version=$(cat CloudflareST_version.txt )

if [[ ! -f "CloudflareST" || ${version} != ${old_version} ]]; then
	rm -rf CloudflareST_linux_${tag}.tar.gz
	wget -N -e use_proxy=yes -e http_proxy=${authProxy} https://github.com/XIU2/CloudflareSpeedTest/releases/download/${version}/CloudflareST_linux_${tag}.tar.gz
	echo "${version}" > CloudflareST_version.txt
	tar -xvf CloudflareST_linux_${tag}.tar.gz
	chmod +x CloudflareST
fi

# 请求接口并下载zip文件
curl -x ${authProxy} -o temp.zip https://zip.baipiao.eu.org
# 解压zip文件
unzip temp.zip -d temp_folder
# 清除之前可能存在的输出文件
rm -f ip_best_*.txt
# 合并所有txt文件内容并根据文件名中的数字部分分类到不同的文件中，并去除重复IP
for file in temp_folder/*.txt; do
    num=$(echo "$file" | grep -oP '(?<=-)\d+(?=-)')
    cat "$file" | sort | uniq >> "ip_best_${num}.txt"
done
# 清理临时文件
rm temp.zip
rm -rf temp_folder

# 打印系统环境变量配置的测速地址
speed_url=$SPEEDURL
echo "测速地址为：${speed_url}"

./CloudflareST -tll 40 -tl 200 -n 400 -sl 10 -dn 10 -url "${speed_url}" -o cf_result.txt

# 延时2分钟
sleep 120

./CloudflareST -f ip_best_1.txt -tll 10 -tl 90 -sl 3 -dn 3 -n 400 -url "${speed_url}" -o cf_result_1.txt

# 延时2分钟
sleep 120

./CloudflareST -f ip_best_0.txt -tll 10 -tl 90 -sl 3 -dn 3 -n 400 -url "${speed_url}" -o cf_result_0.txt
