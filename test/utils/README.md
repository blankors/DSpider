# MongoDB测试数据操作工具

本工具提供了一套便捷的功能，用于管理MongoDB中的测试数据，支持数据的创建、查询、更新和清理操作。该工具既可以作为模块导入使用，也可以通过命令行直接调用。

## 目录结构

```
test/
├── utils/
│   ├── mongodb_test_utils.py  # 核心工具类
│   └── README.md              # 本文档
```

## 功能特性

- 连接管理：安全连接和断开MongoDB
- 测试数据设置：批量插入测试数据
- 测试数据清理：按条件或全部清理数据
- 测试数据查询：灵活的查询功能
- 数据导入导出：支持JSON格式的数据导入导出
- 数据更新：便捷地更新测试数据
- 命令行接口：支持通过命令行进行操作

## 作为模块使用

### 基本用法

```python
from test.utils.mongodb_test_utils import MongoDBTestUtils

# 初始化工具实例
utils = MongoDBTestUtils()

# 连接到MongoDB
if utils.connect():
    # 设置测试数据
    test_data = [
        {'name': 'test1', 'status': 'active'},
        {'name': 'test2', 'status': 'inactive'}
    ]
    ids = utils.setup_test_data('test_collection', test_data)
    print(f"插入了 {len(ids)} 条测试数据")
    
    # 查询测试数据
    data = utils.find_test_data('test_collection', {'status': 'active'})
    print(f"找到 {len(data)} 条活跃数据")
    
    # 清理测试数据
    count = utils.clear_test_data('test_collection')
    print(f"清理了 {count} 条测试数据")

# 断开连接
utils.disconnect()
```

### 使用配置文件

```python
# 使用自定义配置文件
utils = MongoDBTestUtils(config_path='path/to/config.json')
```

### 从JSON文件加载测试数据

```python
# 从JSON文件加载测试数据
test_data = utils.load_test_data_from_json('path/to/test_data.json')
utils.setup_test_data('test_collection', test_data)
```

### 导出测试数据

```python
# 导出测试数据到JSON文件
utils.export_test_data('test_collection', 'path/to/export.json')

# 导出满足条件的数据
utils.export_test_data('test_collection', 'path/to/active_data.json', {'status': 'active'})
```

## 命令行使用

### 查看帮助

```bash
python -m test.utils.mongodb_test_utils -h
```

### 设置测试数据

#### 从JSON文件导入

```bash
python -m test.utils.mongodb_test_utils setup --collection test_collection --json path/to/test_data.json
```

#### 直接提供JSON数据

```bash
python -m test.utils.mongodb_test_utils setup --collection test_collection --data '{"name": "test", "status": "active"}'
```

### 清理测试数据

#### 清理整个集合

```bash
python -m test.utils.mongodb_test_utils clear --collection test_collection
```

#### 按条件清理

```bash
python -m test.utils.mongodb_test_utils clear --collection test_collection --query '{"status": "inactive"}'
```

### 查询测试数据

#### 查询所有数据（限制数量）

```bash
python -m test.utils.mongodb_test_utils find --collection test_collection --limit 20
```

#### 按条件查询

```bash
python -m test.utils.mongodb_test_utils find --collection test_collection --query '{"status": "active"}'
```

### 导出测试数据

```bash
python -m test.utils.mongodb_test_utils export --collection test_collection --output path/to/export.json
```

### 更新测试数据

```bash
python -m test.utils.mongodb_test_utils update --collection test_collection --query '{"name": "test"}' --update '{"status": "updated"}'
```

## 配置文件格式

配置文件采用JSON格式，示例：

```json
{
  "mongodb": {
    "host": "localhost",
    "port": 27017,
    "username": "",
    "password": "",
    "db_name": "spider_db"
  }
}
```

## 在测试中使用

### 示例：在pytest中使用

```python
import pytest
from test.utils.mongodb_test_utils import MongoDBTestUtils

@pytest.fixture
def mongodb_utils():
    """提供MongoDB测试工具的fixture"""
    utils = MongoDBTestUtils()
    utils.connect()
    # 测试前清理数据
    utils.clear_test_data('test_collection')
    yield utils
    # 测试后清理数据
    utils.clear_test_data('test_collection')
    utils.disconnect()

def test_something(mongodb_utils):
    """测试示例"""
    # 设置测试数据
    test_data = {'name': 'test', 'status': 'active'}
    mongodb_utils.setup_test_data('test_collection', [test_data])
    
    # 执行测试逻辑
    # ...
    
    # 验证结果
    result = mongodb_utils.find_test_data('test_collection')
    assert len(result) == 1
    assert result[0]['name'] == 'test'
```

## 注意事项

1. 请确保MongoDB服务已启动且可访问
2. 在生产环境使用时请谨慎操作，避免误删数据
3. 对于大规模数据操作，建议分批处理
4. 命令行操作时请注意JSON格式的正确性