FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update -y --fix-missing && apt-get install -y --no-install-recommends --fix-missing \
    gcc \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装uv
RUN pip install --no-cache-dir uv

# 复制依赖文件
COPY worker/requirements.txt .

# 安装Python依赖
RUN uv pip install --no-cache-dir --system -r requirements.txt

# 安装Playwright浏览器
RUN playwright install

# 复制代码
COPY worker/ .
COPY common /app/common
COPY config /app/config

# 创建日志目录
RUN mkdir -p /app/logs

# 环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 运行命令
CMD ["bash", "-c", "cd /app && celery -A common.celery_config worker --loglevel=info & python worker.py"]