# 使用Python 3.10 slim作为基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 更新包列表并安装必要的依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    # Playwright所需的依赖
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# 通过官方脚本安装uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# 添加uv到PATH（使用绝对路径确保可靠访问）
ENV PATH="/root/.local/bin:$PATH"

# 复制项目配置和代码
COPY pyproject.toml uv.lock ./

# 使用uv sync创建虚拟环境并安装依赖（包括可编辑模式）
RUN uv sync

# 安装Playwright浏览器
RUN uv run python -m playwright install

# 复制代码
COPY worker/ .
COPY common /app/common
COPY config /app/config

# 创建日志目录
RUN mkdir -p /app/logs

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1

# 启动Celery worker和worker.py，通过不同前缀区分日志
CMD ["bash", "-c", \
    "cd /app && \
    uv run celery -A common.celery_config worker --loglevel=info 2>&1 | sed 's/^/[CELERY] /' & \
    uv run python worker.py 2>&1 | sed 's/^/[WORKER] /' & \
    wait -n"]