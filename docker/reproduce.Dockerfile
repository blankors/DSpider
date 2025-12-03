# 使用与celery_worker相同的基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装依赖（与celery_worker.Dockerfile相同）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
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

# 安装uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# 复制项目文件
COPY ../pyproject.toml ../uv.lock ./
COPY ../src/ ./src
COPY ../test/ ./test
COPY ../config/ ./config

# 安装依赖
RUN uv sync

# 安装Playwright
RUN uv run python -m playwright install-deps
RUN uv run python -m playwright install

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# 运行复现脚本
CMD ["bash", "-c", "cd /app && uv run python -m test.container_reproduce"]