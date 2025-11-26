import argparse
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from common.mongodb_client import MongoDBConnection

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MongoDBTestUtils:
    """MongoDB测试数据工具类"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化MongoDB测试工具
        
        Args:
            config_path: 配置文件路径，如果不提供则使用默认配置
        """
        self.config = self._load_config(config_path)
        self.mongo_client = MongoDBConnection(
            host=self.config['mongodb']['host'],
            port=self.config['mongodb']['port'],
            username=self.config['mongodb']['username'],
            password=self.config['mongodb']['password'],
            db_name=self.config['mongodb']['db_name']
        )
        self.connected = False
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Dict: 配置字典
        """
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # 返回默认配置
        return {
            'mongodb': {
                'host': 'localhost',
                'port': 27017,
                'username': '',
                'password': '',
                'db_name': 'spider_db'
            }
        }
    
    def connect(self) -> bool:
        """连接到MongoDB
        
        Returns:
            bool: 是否连接成功
        """
        if not self.connected:
            self.connected = self.mongo_client.connect()
        return self.connected
    
    def disconnect(self):
        """断开MongoDB连接"""
        if self.connected:
            self.mongo_client.disconnect()
            self.connected = False
    
    def setup_test_data(self, collection_name: str, data: List[Dict[str, Any]]) -> List[str]:
        """设置测试数据
        
        Args:
            collection_name: 集合名称
            data: 测试数据列表
            
        Returns:
            List[str]: 插入的文档ID列表
        """
        if not self.connect():
            logger.error("无法连接到MongoDB")
            return []
        
        return self.mongo_client.insert_many(collection_name, data)
    
    def clear_test_data(self, collection_name: str, query: Optional[Dict[str, Any]] = None) -> int:
        """清理测试数据
        
        Args:
            collection_name: 集合名称
            query: 过滤条件，如果为None则清理整个集合
            
        Returns:
            int: 删除的文档数量
        """
        if not self.connect():
            logger.error("无法连接到MongoDB")
            return 0
        
        try:
            collection = self.mongo_client.get_collection(collection_name)
            if collection:
                if query is None:
                    result = collection.delete_many({})
                else:
                    result = collection.delete_many(query)
                logger.info(f"清理 {result.deleted_count} 条测试数据")
                return result.deleted_count
        except Exception as e:
            logger.error(f"清理测试数据失败: {str(e)}")
        return 0
    
    def find_test_data(self, collection_name: str, query: Optional[Dict[str, Any]] = None,
                      limit: int = 10) -> List[Dict[str, Any]]:
        """查询测试数据
        
        Args:
            collection_name: 集合名称
            query: 查询条件
            limit: 返回数量限制
            
        Returns:
            List[Dict]: 查询结果
        """
        if not self.connect():
            logger.error("无法连接到MongoDB")
            return []
        
        return self.mongo_client.find(collection_name, query or {}, limit=limit)
    
    def load_test_data_from_json(self, json_path: str) -> List[Dict[str, Any]]:
        """从JSON文件加载测试数据
        
        Args:
            json_path: JSON文件路径
            
        Returns:
            List[Dict]: 测试数据列表
        """
        if not os.path.exists(json_path):
            logger.error(f"测试数据文件不存在: {json_path}")
            return []
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # 确保返回的是列表
            if isinstance(data, dict):
                return [data]
            return data
        except Exception as e:
            logger.error(f"加载测试数据文件失败: {str(e)}")
            return []
    
    def export_test_data(self, collection_name: str, output_path: str,
                        query: Optional[Dict[str, Any]] = None) -> bool:
        """导出测试数据到JSON文件
        
        Args:
            collection_name: 集合名称
            output_path: 输出文件路径
            query: 查询条件
            
        Returns:
            bool: 是否导出成功
        """
        data = self.find_test_data(collection_name, query, limit=0)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"成功导出 {len(data)} 条数据到 {output_path}")
            return True
        except Exception as e:
            logger.error(f"导出测试数据失败: {str(e)}")
            return False
    
    def update_test_data(self, collection_name: str, query: Dict[str, Any],
                        update: Dict[str, Any]) -> bool:
        """更新测试数据
        
        Args:
            collection_name: 集合名称
            query: 查询条件
            update: 更新内容
            
        Returns:
            bool: 是否更新成功
        """
        if not self.connect():
            logger.error("无法连接到MongoDB")
            return False
        
        # 确保update包含$操作符
        if not any(k.startswith('$') for k in update.keys()):
            update = {'$set': update}
        
        return self.mongo_client.update_one(collection_name, query, update)


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='MongoDB测试数据管理工具')
    parser.add_argument('--config', help='配置文件路径')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # setup命令
    setup_parser = subparsers.add_parser('setup', help='设置测试数据')
    setup_parser.add_argument('--collection', required=True, help='集合名称')
    setup_parser.add_argument('--json', help='JSON数据文件路径')
    setup_parser.add_argument('--data', help='JSON格式的测试数据字符串')
    
    # clear命令
    clear_parser = subparsers.add_parser('clear', help='清理测试数据')
    clear_parser.add_argument('--collection', required=True, help='集合名称')
    clear_parser.add_argument('--query', help='JSON格式的过滤条件')
    
    # find命令
    find_parser = subparsers.add_parser('find', help='查询测试数据')
    find_parser.add_argument('--collection', required=True, help='集合名称')
    find_parser.add_argument('--query', help='JSON格式的查询条件')
    find_parser.add_argument('--limit', type=int, default=10, help='返回数量限制')
    
    # export命令
    export_parser = subparsers.add_parser('export', help='导出测试数据')
    export_parser.add_argument('--collection', required=True, help='集合名称')
    export_parser.add_argument('--output', required=True, help='输出文件路径')
    export_parser.add_argument('--query', help='JSON格式的查询条件')
    
    # update命令
    update_parser = subparsers.add_parser('update', help='更新测试数据')
    update_parser.add_argument('--collection', required=True, help='集合名称')
    update_parser.add_argument('--query', required=True, help='JSON格式的查询条件')
    update_parser.add_argument('--update', required=True, help='JSON格式的更新内容')
    
    return parser.parse_args()


def cmdline():
    """主函数"""
    args = parse_arguments()
    
    if not args.command:
        print("请指定命令，使用 -h 查看帮助")
        return
    
    # 创建工具实例
    utils = MongoDBTestUtils(args.config)
    
    try:
        if args.command == 'setup':
            # 设置测试数据
            if args.json:
                data = utils.load_test_data_from_json(args.json)
            elif args.data:
                data = json.loads(args.data)
                if isinstance(data, dict):
                    data = [data]
            else:
                print("请提供 --json 或 --data 参数")
                return
            
            ids = utils.setup_test_data(args.collection, data)
            print(f"成功插入 {len(ids)} 条测试数据")
            
        elif args.command == 'clear':
            # 清理测试数据
            query = json.loads(args.query) if args.query else None
            count = utils.clear_test_data(args.collection, query)
            print(f"成功清理 {count} 条测试数据")
            
        elif args.command == 'find':
            # 查询测试数据
            query = json.loads(args.query) if args.query else None
            data = utils.find_test_data(args.collection, query, args.limit)
            print(json.dumps(data, ensure_ascii=False, indent=2))
            
        elif args.command == 'export':
            # 导出测试数据
            query = json.loads(args.query) if args.query else None
            success = utils.export_test_data(args.collection, args.output, query)
            if success:
                print(f"成功导出数据到 {args.output}")
            else:
                print("导出数据失败")
            
        elif args.command == 'update':
            # 更新测试数据
            query = json.loads(args.query)
            update = json.loads(args.update)
            success = utils.update_test_data(args.collection, query, update)
            if success:
                print("数据更新成功")
            else:
                print("数据更新失败")
                
    except json.JSONDecodeError:
        print("JSON格式错误，请检查输入的数据")
    except Exception as e:
        print(f"错误: {str(e)}")
    finally:
        utils.disconnect()

def run_script_operations(operations: List[Dict[str, Any]], config_path: Optional[str] = None):
    """直接通过脚本方式批量操作 MongoDB，无需命令行参数
    
    Args:
        operations: 操作列表，每个元素是一个字典，格式如下：
            {
                'action': 'setup' | 'clear' | 'find' | 'export' | 'update',
                'collection': str,          # 集合名称，必填
                'data'?: List[Dict],        # setup 时使用
                'json'?: str,               # setup 时 JSON 文件路径
                'query'?: Dict,              # clear / find / export / update 时使用
                'limit'?: int,               # find 时使用，默认 10
                'output'?: str,              # export 时使用，输出文件路径
                'update'?: Dict              # update 时使用，更新内容
            }
        config_path: 配置文件路径，可选
    
    Returns:
        List[Any]: 每个操作对应的结果列表
    """
    utils = MongoDBTestUtils(config_path)
    results = []

    try:
        for op in operations:
            action = op.get('action')
            collection = op.get('collection')
            if not collection:
                logger.error("缺少 collection 参数")
                results.append(None)
                continue

            if action == 'setup':
                data = op.get('data')
                json_path = op.get('json')
                if json_path:
                    data = utils.load_test_data_from_json(json_path)
                elif isinstance(data, str):
                    data = json.loads(data)
                if isinstance(data, dict):
                    data = [data]
                ids = utils.setup_test_data(collection, data or [])
                results.append(ids)

            elif action == 'clear':
                query = op.get('query')
                count = utils.clear_test_data(collection, query)
                results.append(count)

            elif action == 'find':
                query = op.get('query')
                limit = op.get('limit', 10)
                data = utils.find_test_data(collection, query, limit)
                results.append(data)

            elif action == 'export':
                query = op.get('query')
                output = op.get('output')
                if not output:
                    logger.error("export 操作缺少 output 参数")
                    results.append(False)
                    continue
                success = utils.export_test_data(collection, output, query)
                results.append(success)

            elif action == 'update':
                query = op.get('query')
                update = op.get('update')
                if not query or not update:
                    logger.error("update 操作缺少 query 或 update 参数")
                    results.append(False)
                    continue
                success = utils.update_test_data(collection, query, update)
                results.append(success)

            else:
                logger.error(f"未知操作: {action}")
                results.append(None)

    except Exception as e:
        logger.error(f"脚本执行失败: {str(e)}")
        raise
    finally:
        utils.disconnect()

    return results


if __name__ == '__main__':
    run_script_operations([
        {
            'action': 'setup',
            'collection': 'test_collection',
            'data': [
                {
                    "id": "1",
                    "jump_from_url": "",
                    "hr_index_url": "",
                    'url': 'https://zhaopin.jd.com/web/job/job_info_list/3',
                    'api_url': '',
                    'need_headers': False,
                    'request_params': {
                        'url': "https://zhaopin.jd.com/web/job/job_list",
                        'headers': {
                            "referer": "https://zhaopin.jd.com/web/job/job_info_list/3",
                        },
                        'cookies': {
                            "JSESSIONID": "0D9E36EE88A43018AA117ECA03FAF083.s1"
                        },
                        'data': {
                            "pageIndex": "2",
                            "pageSize": "10",
                            "workCityJson": "[]",
                            "jobTypeJson": "[]",
                            "jobSearch": ""
                        }
                    },
                    'parse_rule': {
                        'url_rule'
                    }
                }
            ]
        },
    ])