设计并实现一个分布式爬虫系统

核心组件：
1、MongoDB，用于存储网站配置，爬取结果
2、RabbitMQ，用于任务分发，缓存爬取结果
3、

流程：
1、Master节点从MongoDB的WebsiteConfig表中读取任务配置，将任务配置分发到RabbitMQ的任务队列中。
2、每个爬虫节点作为一个独立的Docker容器，负责从RabbitMQ获取任务并执行网页抓取。
3、每个爬虫节点将抓取到的数据发送到RabbitMQ的结果队列中。
4、数据处理节点作为另一个独立的Docker容器，负责从RabbitMQ的结果队列中获取数据，进行清洗、存储或进一步分析。

任务配置示例：
{
   "id": "1",
   "jump_from_url": "https://recruit.midea.com/recruitOut/ihr/social/socialHome",
   'need_headers': False,
   'request_params': {
      'api_url': "https://recruit.midea.com/backend/rec/home/out/official/position/list",
      'data': {
         "pageSize": "10",
         "pageIndex": "2",
         "publicationName": ""
      },
      'field_marked': {
         'page': 'pageIndex'
      }
   },
   'parse_rule': {
      'url_rule'
   }
}

基于Docker和RabbitMQ的大规模分布式爬虫系统。整个系统由多个容器组成，包括RabbitMQ消息队列服务、爬虫节点和数据处理节点。

系统需求如下：

1. 日志

   - 要有良好的日志设计，帮助排查运行中的问题。
   - 日志配置由项目根目录的配置文件统一配置。确保日志同时输出到文件和标准输出，方便通过Docker日志查看。
2. 设计公共类

   - 为了实现代码的复用和维护，设计并实现一些公共类，例如MongoDB连接类、RabbitMQ连接类等。
   - 确保这些公共类的代码质量和可维护性，方便后续的扩展和修改。
3. RabbitMQ服务：

   - 确保RabbitMQ服务可以通过Docker快速部署，使用Docker官方的RabbitMQ镜像，并创建一个Dockerfile用于自定义配置文件，配置交换机和队列。
   - 提供一个 `rabbitmq.conf`文件用于配置RabbitMQ服务，包括虚拟主机、用户认证等。确保配置文件中包含交换机和队列的定义。
4. 爬虫Master节点：

   - 作为一个独立的Docker容器，负责从MongoDB读取任务配置，将任务分发到RabbitMQ的任务队列中。
   - 提供一个配置文件，用于指定MongoDB和RabbitMQ的连接信息。
   - 实现一个简单的任务分发算法，将任务均匀地分发到不同的爬虫节点。
5. 爬虫Worker节点：

   - 每个爬虫节点作为一个独立的Docker容器，负责从RabbitMQ获取任务并执行网页抓取。
   - 使用requests实现爬虫逻辑。
   - 创建一个Dockerfile用于构建爬虫环境，并包含自定义的爬虫脚本。
6. 数据处理与存储节点：

   - 作为另一个独立的Docker容器，负责接收爬虫节点发送过来的数据，进行清洗、存储或进一步分析。
   - 支持数据的持久化存储，如MySQL数据库或其他NoSQL数据库。在本项目中，选择MongoDB作为数据存储方案。
   - 提供MongoDB的连接配置文件和数据处理脚本模板，包括如何连接MongoDB、数据清洗逻辑等。
   - 使用Docker官方的MongoDB镜像，并创建一个Dockerfile用于自定义配置文件，配置MongoDB服务。
   - 提供一个 `mongod.conf`文件用于配置MongoDB服务，包括数据目录、端口映射等。
   - 通过volume将MongoDB的数据目录挂载到主机上，确保数据的持久化存储。

请编写Dockerfile和docker-compose.yml文件，以便快速部署整个系统。同时，提供简要说明文档，介绍如何启动和停止各个服务，以及如何向系统中添加新的爬虫节点和数据处理节点。文档中需包含详细的命令行操作指南和注意事项。文档中应包括每个服务的启动命令、停止命令、日志查看命令等，并说明如何调整资源限制和网络设置。

单独在一个文件中编写项目配置，区分开发、测试、上线环境（环境名词应当为dev、test、prod）。例如配置mongo、rabbitmq等组件的连接配置，需要确保能够连接相应的容器


通过uv管理python依赖

优化dockerfile中命令顺序，不要每次修改代码都要进行playwright install

使用多阶段构建，减少容器体积


让docker区分开发环境pip install -e .、生产环境pip install .
