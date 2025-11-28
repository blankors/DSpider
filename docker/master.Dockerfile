# 使用Python 3.10 slim作为基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 通过官方脚本安装uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# 添加uv到PATH（使用绝对路径确保可靠访问）
ENV PATH="/root/.local/bin:$PATH"

# 复制项目配置和代码
COPY ../pyproject.toml ../uv.lock ./

# 使用uv sync创建虚拟环境并安装依赖（包括可编辑模式）
RUN uv sync

# 复制代码
COPY ../src/dspider/ ./dspider
COPY ../config/ ./config

# 创建日志目录
RUN mkdir -p /app/logs

# 环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1

# 使用uv run在虚拟环境中启动程序
CMD ["uv", "run", "python", "dspider/master/master.py"]