# DSpider 测试说明

本目录包含DSpider项目的自动化测试代码。

## 测试结构

- `conftest.py`: 测试夹具和共享配置
- `test_mongodb_client.py`: MongoDB客户端测试
- `test_rabbitmq_client.py`: RabbitMQ客户端测试
- `test_logger_config.py`: 日志配置测试
- `test_master.py`: Master节点测试
- `test_worker.py`: Worker节点测试
- `test_processor.py`: Processor节点测试

## 运行测试

### 安装依赖

确保已安装测试所需的依赖：

```bash
pip install pytest pytest-mock
```

### 运行所有测试

在项目根目录下运行：

```bash
pytest
```

### 运行特定测试文件

```bash
pytest test/test_master.py
```

### 运行特定测试用例

```bash
pytest test/test_master.py::TestMasterNode::test_initialize_success
```

### 查看详细输出

```bash
pytest -v
```

### 生成测试覆盖率报告

```bash
pytest --cov=.
```

## 测试注意事项

1. 测试使用mock来模拟外部依赖（MongoDB、RabbitMQ等），不需要实际的服务连接
2. 所有测试都是单元测试，独立运行互不影响
3. 测试覆盖了主要功能和异常情况