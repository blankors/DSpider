# 分布式爬虫系统 (DistributeSpiderV2)

基于Docker和RabbitMQ的大规模分布式爬虫系统，支持多节点并行爬取和数据处理。

## 系统架构

![系统架构](https://i.imgur.com/placeholder.png)

系统由以下核心组件组成：

1. **MongoDB**：存储网站配置和爬取结果
2. **RabbitMQ**：任务分发和结果缓存
3. **Master节点**：任务调度中心，负责分发任务
4. **Worker节点**：爬虫执行节点，负责网页抓取
5. **Processor节点**：数据处理节点，负责清洗和存储数据

## 目录结构

```
DistributeSpiderV2/
├── common/          # 公共模块
│   ├── mongodb_client.py    # MongoDB连接类
│   ├── rabbitmq_client.py   # RabbitMQ连接类
│   └── logger_config.py     # 日志配置类
├── config/          # 配置文件
│   ├── config.json          # 主配置文件
│   └── logging.json         # 日志配置文件
├── master/          # Master节点
│   ├── master.py            # Master节点主程序
│   ├── Dockerfile           # Docker构建文件
│   └── requirements.txt     # 依赖文件
├── worker/          # Worker节点
│   ├── worker.py            # Worker节点主程序
│   ├── Dockerfile           # Docker构建文件
│   └── requirements.txt     # 依赖文件
├── processor/       # Processor节点
│   ├── processor.py         # Processor节点主程序
│   ├── Dockerfile           # Docker构建文件
│   └── requirements.txt     # 依赖文件
├── data/            # 数据和配置
│   ├── mongod.conf          # MongoDB配置
│   └── rabbitmq.conf        # RabbitMQ配置
├── logs/            # 日志目录
├── docker-compose.yml       # Docker Compose配置
└── README.md                # 项目说明文档
```

## 快速开始

### 前置条件

- Docker 20.10+ 
- Docker Compose 2.0+

### 启动系统

1. 克隆项目到本地

```bash
git clone <项目地址>
cd DistributeSpiderV2
```

2. 创建必要的目录

```bash
mkdir -p logs/master logs/worker logs/processor data/mongo_data data/rabbitmq_data
```

3. 启动所有服务

```bash
docker-compose up -d
```

### 停止系统

```bash
docker-compose down
```

### 查看服务状态

```bash
docker-compose ps
```

### 查看日志

```bash
# 查看Master日志
docker-compose logs master

# 查看Worker日志
docker-compose logs worker

# 查看Processor日志
docker-compose logs processor

# 实时查看日志
docker-compose logs -f [服务名]
```

## 系统配置

### 配置文件说明

- **config/config.json**：主配置文件，包含MongoDB、RabbitMQ等服务的连接信息
- **config/logging.json**：日志配置文件，控制日志输出格式和级别

### 主要配置项

| 配置项 | 说明 | 默认值 |
|-------|------|-------|
| mongodb.host | MongoDB主机地址 | mongodb |
| mongodb.port | MongoDB端口 | 27017 |
| rabbitmq.host | RabbitMQ主机地址 | rabbitmq |
| rabbitmq.port | RabbitMQ端口 | 5672 |
| master.task_queue | 任务队列名称 | spider_tasks |
| worker.prefetch_count | Worker预取消息数 | 5 |
| processor.batch_size | 批处理大小 | 50 |

## 使用指南

### 添加爬虫任务

1. 连接到MongoDB

```bash
docker exec -it mongodb mongo -u admin -p admin123 --authenticationDatabase admin spider_db
```

2. 插入爬虫任务配置

```javascript
db.WebsiteConfig.insertOne({
  "id": "1",
  "jump_from_url": "https://example.com",
  "need_headers": true,
  "status": "pending",
  "request_params": {
    "api_url": "https://example.com/api/data",
    "data": {
      "page": 1,
      "limit": 10
    },
    "field_marked": {
      "page": "page"
    }
  },
  "parse_rule": {
    "title": "data.title",
    "content": "data.content"
  }
});
```

### 扩展Worker节点数量

```bash
# 扩展到5个Worker节点
docker-compose up -d --scale worker=5
```

### 监控系统

- **RabbitMQ管理界面**：访问 http://localhost:15672 (用户名: admin, 密码: admin123)
- **MongoDB数据查看**：使用MongoDB Compass或其他工具连接到 localhost:27017

## 故障排查

1. **服务启动失败**：检查Docker Compose日志，确认端口是否被占用
2. **任务未分发**：检查MongoDB中的WebsiteConfig集合是否有任务
3. **爬取失败**：查看Worker节点日志，检查网络连接和请求参数
4. **数据未存储**：查看Processor节点日志，检查MongoDB连接状态

## 性能优化

1. 调整Worker节点数量以适应系统负载
2. 修改`worker.prefetch_count`以控制每个Worker的并行任务数
3. 调整`processor.batch_size`以优化批处理性能
4. 为MongoDB集合创建合适的索引

## 安全注意事项

1. 生产环境中请修改默认的用户名和密码
2. 限制MongoDB和RabbitMQ的访问IP
3. 配置适当的资源限制，防止单个服务占用过多资源

## 许可证

[MIT License](LICENSE)