# 使用官方 Python 3.9 精简版镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置时区为上海
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 复制当前目录下的所有文件到容器中
COPY . /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 设置环境变量 (默认值，实际运行推荐挂载 .env)
ENV PYTHONUNBUFFERED=1

# 启动命令
CMD ["python", "main_scheduler.py"]
