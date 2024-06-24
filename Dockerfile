# 使用官方的 Python 镜像作为基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 将本地的 Python 脚本复制到容器中
COPY app.py /app/

# 安装脚本所需的依赖
RUN pip install --no-cache-dir croniter CloudFlare==2.19.4

# 切换到 root 用户
USER root

# 定义容器启动时执行的命令
CMD ["python", "-u", "app.py"]
