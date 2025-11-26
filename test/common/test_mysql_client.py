import unittest 
import logging

from context import common
from common.mysql_client import MySQLConnection, mysql_conn

logger = logging.getLogger(__name__)

class TestMySQLClient(unittest.TestCase):
    """MySQL客户端测试类"""
    
    TEST_TABLE = "test_mysql_client"
    
    @classmethod
    def setUpClass(cls):
        """测试前的准备工作"""
        logger.info("开始设置测试环境...")
        # 确保使用全局连接实例
        cls.client = mysql_conn
        
        # 尝试连接数据库
        connected = cls.client.connect()
        if not connected:
            logger.error("无法连接到MySQL数据库，请检查配置!")
            return
        
        # 创建测试表
        cls._create_test_table()
        logger.info("测试环境设置完成")
    
    @classmethod
    def tearDownClass(cls):
        """测试后的清理工作"""
        if cls.client.connection or cls.client.pool:
            # 删除测试表
            cls._drop_test_table()
            # 断开连接
            cls.client.disconnect()
            logger.info("测试环境已清理")
    
    @classmethod
    def _create_test_table(cls):
        """创建测试表"""
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {cls.TEST_TABLE} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(50) NOT NULL,
            age INT,
            email VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        
        try:
            with cls.client.get_cursor(commit=True) as cursor:
                if cursor:
                    cursor.execute(create_table_sql)
                    logger.info(f"成功创建测试表: {cls.TEST_TABLE}")
        except Exception as e:
            logger.error(f"创建测试表失败: {str(e)}")
    
    @classmethod
    def _drop_test_table(cls):
        """删除测试表"""
        drop_table_sql = f"DROP TABLE IF EXISTS {cls.TEST_TABLE}"
        
        try:
            with cls.client.get_cursor(commit=True) as cursor:
                if cursor:
                    cursor.execute(drop_table_sql)
                    logger.info(f"成功删除测试表: {cls.TEST_TABLE}")
        except Exception as e:
            logger.error(f"删除测试表失败: {str(e)}")
    
    def setUp(self):
        """每个测试方法执行前的准备"""
        # 清空测试表
        truncate_sql = f"TRUNCATE TABLE {self.TEST_TABLE}"
        try:
            with self.client.get_cursor(commit=True) as cursor:
                if cursor:
                    cursor.execute(truncate_sql)
        except Exception as e:
            logger.error(f"清空测试表失败: {str(e)}")
    
    def test_connect_disconnect(self):
        """测试连接和断开功能"""
        # 测试连接是否成功
        self.assertTrue(self.client.connection is not None or self.client.pool is not None)
        
        # 如果不是使用连接池，测试断开再连接
        if not self.client.use_pool:
            self.client.disconnect()
            self.assertIsNone(self.client.connection)
            
            connected = self.client.connect(max_retries=1)
            self.assertTrue(connected)
            self.assertIsNotNone(self.client.connection)
    
    def test_table_exists(self):
        """测试表是否存在功能"""
        # 测试存在的表
        exists = self.client.table_exists(self.TEST_TABLE)
        self.assertTrue(exists)
        
        # 测试不存在的表
        not_exists = self.client.table_exists("non_existent_table")
        self.assertFalse(not_exists)
    
    def test_insert_single(self):
        """测试单条插入功能"""
        # 准备测试数据
        test_data = {
            "name": "张三",
            "age": 25,
            "email": "zhangsan@example.com"
        }
        
        # 执行插入
        affected_rows = self.client.insert(self.TEST_TABLE, test_data)
        self.assertEqual(affected_rows, 1)
        
        # 验证插入结果
        result = self.client.find_one(self.TEST_TABLE, {"name": "张三"})
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "张三")
        self.assertEqual(result["age"], 25)
        self.assertEqual(result["email"], "zhangsan@example.com")
    
    def test_insert_many(self):
        """测试批量插入功能"""
        # 准备测试数据
        test_data_list = [
            {"name": "李四", "age": 28, "email": "lisi@example.com"},
            {"name": "王五", "age": 30, "email": "wangwu@example.com"},
            {"name": "赵六", "age": 35, "email": "zhaoliu@example.com"}
        ]
        
        # 执行批量插入
        affected_rows = self.client.insert_many(self.TEST_TABLE, test_data_list)
        self.assertEqual(affected_rows, 3)
        
        # 验证插入结果
        results = self.client.find_all(self.TEST_TABLE, limit=10)
        self.assertEqual(len(results), 3)
        
        # 检查是否所有数据都被正确插入
        names = [row["name"] for row in results]
        self.assertIn("李四", names)
        self.assertIn("王五", names)
        self.assertIn("赵六", names)
    
    def test_find_one(self):
        """测试查询单条记录功能"""
        # 先插入测试数据
        test_data = {"name": "测试用户", "age": 22, "email": "test@example.com"}
        self.client.insert(self.TEST_TABLE, test_data)
        
        # 测试精确查询
        result = self.client.find_one(self.TEST_TABLE, {"name": "测试用户"})
        self.assertIsNotNone(result)
        self.assertEqual(result["age"], 22)
        
        # 测试不存在的记录
        not_found = self.client.find_one(self.TEST_TABLE, {"name": "不存在的用户"})
        self.assertIsNone(not_found)
    
    def test_find_all(self):
        """测试查询多条记录功能"""
        # 插入多条测试数据
        for i in range(5):
            test_data = {"name": f"用户{i}", "age": 20 + i, "email": f"user{i}@example.com"}
            self.client.insert(self.TEST_TABLE, test_data)
        
        # 测试查询所有记录
        results = self.client.find_all(self.TEST_TABLE)
        self.assertEqual(len(results), 5)
        
        # 测试带条件的查询
        age_condition = {"age": 22}
        conditional_results = self.client.find_all(self.TEST_TABLE, age_condition)
        self.assertEqual(len(conditional_results), 1)
        self.assertEqual(conditional_results[0]["name"], "用户2")
        
        # 测试分页查询
        page1 = self.client.find_all(self.TEST_TABLE, limit=2, offset=0)
        page2 = self.client.find_all(self.TEST_TABLE, limit=2, offset=2)
        
        self.assertEqual(len(page1), 2)
        self.assertEqual(len(page2), 2)
        self.assertEqual(page1[0]["name"], "用户0")
        self.assertEqual(page2[0]["name"], "用户2")
    
    def test_update(self):
        """测试更新功能"""
        # 先插入测试数据
        test_data = {"name": "待更新用户", "age": 40, "email": "update@example.com"}
        self.client.insert(self.TEST_TABLE, test_data)
        
        # 执行更新
        update_data = {"age": 41, "email": "updated@example.com"}
        condition = {"name": "待更新用户"}
        affected_rows = self.client.update(self.TEST_TABLE, update_data, condition)
        self.assertEqual(affected_rows, 1)
        
        # 验证更新结果
        result = self.client.find_one(self.TEST_TABLE, condition)
        self.assertIsNotNone(result)
        self.assertEqual(result["age"], 41)
        self.assertEqual(result["email"], "updated@example.com")
    
    def test_delete(self):
        """测试删除功能"""
        # 插入测试数据
        test_data1 = {"name": "待删除用户1", "age": 25, "email": "delete1@example.com"}
        test_data2 = {"name": "待删除用户2", "age": 26, "email": "delete2@example.com"}
        self.client.insert(self.TEST_TABLE, test_data1)
        self.client.insert(self.TEST_TABLE, test_data2)
        
        # 执行删除
        condition = {"name": "待删除用户1"}
        affected_rows = self.client.delete(self.TEST_TABLE, condition)
        self.assertEqual(affected_rows, 1)
        
        # 验证删除结果
        deleted_result = self.client.find_one(self.TEST_TABLE, condition)
        self.assertIsNone(deleted_result)
        
        # 检查另一个用户是否存在
        other_result = self.client.find_one(self.TEST_TABLE, {"name": "待删除用户2"})
        self.assertIsNotNone(other_result)
    
    def test_execute_query(self):
        """测试执行原始查询功能"""
        # 插入测试数据
        for i in range(3):
            self.client.insert(self.TEST_TABLE, {"name": f"查询用户{i}", "age": 18 + i})
        
        # 执行原始查询
        query = f"SELECT * FROM {self.TEST_TABLE} WHERE age > %s"
        params = (19,)
        results = self.client.execute_query(query, params)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["age"], 20)
        self.assertEqual(results[0]["name"], "查询用户2")
    
    def test_execute_update(self):
        """测试执行原始更新功能"""
        # 插入测试数据
        self.client.insert(self.TEST_TABLE, {"name": "原始更新用户", "age": 50})
        
        # 执行原始更新
        query = f"UPDATE {self.TEST_TABLE} SET age = %s WHERE name = %s"
        params = (51, "原始更新用户")
        affected_rows = self.client.execute_update(query, params)
        
        self.assertEqual(affected_rows, 1)
        
        # 验证更新结果
        result = self.client.find_one(self.TEST_TABLE, {"name": "原始更新用户"})
        self.assertEqual(result["age"], 51)
    
    def test_get_last_insert_id(self):
        """测试获取最后插入ID功能"""
        # 插入数据
        self.client.insert(self.TEST_TABLE, {"name": "测试ID", "age": 25})
        last_id = self.client.get_last_insert_id()
        
        # 验证ID
        result = self.client.find_one(self.TEST_TABLE, {"id": last_id})
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "测试ID")


def run_test():
    """运行测试函数"""
    logger.info("开始运行MySQL客户端测试...")
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMySQLClient)
    unittest.TextTestRunner(verbosity=2).run(suite)
    logger.info("MySQL客户端测试完成")

if __name__ == '__main__':
    # 创建表
    # mysql_conn.create_table("""
    # CREATE TABLE IF NOT EXISTS test_table (
    #     id INT AUTO_INCREMENT PRIMARY KEY,
    #     name VARCHAR(255),
    #     age INT
    # )
    # """)
    # # 插入数据
    # mysql_conn.insert("test_table", {"name": "Alice", "age": 30})
    # 查询数据
    result = mysql_conn.execute_query("SELECT * FROM test_table")
    print(result)
    # 删除表
    # mysql_conn.execute_update("DROP TABLE IF EXISTS test_table")
