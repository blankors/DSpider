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
COPY ../README.md ./
COPY ../src/ ./src
COPY ../config/ ./config

# 使用uv sync创建虚拟环境并安装依赖（包括可编辑模式），使用国内镜像源加速下载
RUN uv sync --index-url https://mirrors.aliyun.com/pypi/simple/ --extra-index-url https://pypi.org/simple/

# 创建日志目录
RUN mkdir -p /app/logs

# 环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1

# 使用uv run在虚拟环境中启动程序
CMD ["uv", "run", "python", "dspider/master/master.py"]