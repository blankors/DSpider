import logging
import pymysql
import time
from typing import Optional, List, Dict, Any, Tuple, Generator, ContextManager
from contextlib import contextmanager
from common.load_config import config

# 尝试导入连接池支持
CONNECTION_POOL_AVAILABLE = False
try:
    from DBUtils.PooledDB import PooledDB
    CONNECTION_POOL_AVAILABLE = True
except ImportError:
    logging.warning("DBUtils.PooledDB 未安装，将不支持连接池功能")

logger = logging.getLogger(__name__)


class MySQLService:
    """MySQL连接管理类，支持连接池"""
    
    def __init__(self, host: str = 'localhost', port: int = 3306, 
                 username: str = 'root', password: str = '', 
                 db_name: str = '', charset: str = 'utf8mb4',
                 # 连接池相关参数
                 use_pool: bool = True,
                 mincached: int = 5,
                 maxcached: int = 20,
                 maxconnections: int = 100,
                 blocking: bool = True,
                 maxusage: Optional[int] = None,
                 setsession: Optional[List[str]] = None,
                 reset: bool = True):
        """初始化MySQL连接对象
        
        Args:
            host: MySQL主机地址
            port: MySQL端口
            username: MySQL用户名
            password: MySQL密码
            db_name: 数据库名称
            charset: 字符集
            use_pool: 是否使用连接池
            mincached: 连接池中的最小空闲连接数
            maxcached: 连接池中的最大空闲连接数
            maxconnections: 连接池允许的最大连接数
            blocking: 当连接池耗尽时是否阻塞等待
            maxusage: 单个连接的最大使用次数，None表示不限制
            setsession: 会话设置命令列表
            reset: 连接返回到池中时是否重置
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.db_name = db_name
        self.charset = charset
        
        # 连接池配置
        self.use_pool = use_pool and CONNECTION_POOL_AVAILABLE
        self.mincached = mincached
        self.maxcached = maxcached
        self.maxconnections = maxconnections
        self.blocking = blocking
        self.maxusage = maxusage
        self.setsession = setsession or []
        self.reset = reset
        
        # 连接状态
        self.connection: Optional[pymysql.connections.Connection] = None
        self.pool: Optional[PooledDB] = None
    
    def connect(self, max_retries: int = 3, retry_delay: int = 2) -> bool:
        """连接到MySQL，支持连接池
        
        Args:
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            
        Returns:
            bool: 是否连接成功
        """
        for attempt in range(max_retries):
            try:
                if self.use_pool:
                    # 初始化连接池
                    self.pool = PooledDB(
                        creator=pymysql,  # 使用的数据库驱动
                        host=self.host,
                        port=self.port,
                        user=self.username,
                        password=self.password,
                        db=self.db_name,
                        charset='utf8mb4',
                        cursorclass=pymysql.cursors.DictCursor,
                        mincached=self.mincached,
                        maxcached=self.maxcached,
                        maxconnections=self.maxconnections,
                        blocking=self.blocking,
                        maxusage=self.maxusage,
                        setsession=self.setsession,
                        reset=self.reset
                    )
                    logger.info(f"成功初始化MySQL连接池: {self.host}:{self.port}/{self.db_name}")
                    logger.info(f"连接池配置: mincached={self.mincached}, maxcached={self.maxcached}, maxconnections={self.maxconnections}")
                else:
                    # 使用单连接模式
                    self.connection = pymysql.connect(
                        host=self.host,
                        port=self.port,
                        user=self.username,
                        password=self.password,
                        db=self.db_name,
                        charset='utf8mb4',
                        cursorclass=pymysql.cursors.DictCursor
                    )
                    logger.info(f"成功连接到MySQL: {self.host}:{self.port}/{self.db_name} (单连接模式)")
                return True
            except Exception as e:
                logger.error(f"连接MySQL失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        return False
    
    def disconnect(self):
        """断开MySQL连接或关闭连接池"""
        if self.use_pool and self.pool:
            # 关闭连接池
            self.pool.close()
            self.pool = None
            logger.info("已关闭MySQL连接池")
        elif self.connection:
            # 关闭单连接
            self.connection.close()
            self.connection = None
            logger.info("已断开MySQL连接")
    
    @contextmanager
    def get_cursor(self, commit: bool = False) -> Generator[pymysql.cursors.DictCursor, None, None]:
        """获取数据库游标，支持连接池
        
        Args:
            commit: 是否自动提交
            
        Yields:
            DictCursor: 数据库游标对象
        """
        connection = None
        cursor = None
        
        try:
            # 根据模式获取连接
            if self.use_pool:
                if not self.pool:
                    logger.error("MySQL连接池未初始化")
                    yield None
                    return
                connection = self.pool.connection()
            else:
                if not self.connection:
                    logger.error("MySQL未连接")
                    yield None
                    return
                connection = self.connection
            
            # 创建游标
            cursor = connection.cursor()
            yield cursor
            
            # 提交事务
            if commit:
                connection.commit()
                logger.info("事务已提交")
                
        except Exception as e:
            logger.error(f"游标操作失败: {str(e)}")
            if commit and connection:
                connection.rollback()
                logger.info("事务已回滚")
            raise
        finally:
            # 关闭游标
            if cursor:
                cursor.close()
            
            # 在连接池模式下，连接会自动归还到池中
            # 单连接模式下不需要关闭连接，因为它是共享的
            if self.use_pool and connection:
                # 注意：DBUtils会自动处理连接的归还
                pass
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> Optional[List[Dict[str, Any]]]:
        """执行查询语句（SELECT操作）
        
        Args:
            query: SQL查询语句
            params: SQL参数
            
        Returns:
            List[Dict]: 查询结果列表
        """
        try:
            with self.get_cursor() as cursor:
                if cursor:
                    cursor.execute(query, params or ())
                    result = cursor.fetchall()
                    logger.info(f"查询成功，返回 {len(result)} 条记录")
                    return result
        except Exception as e:
            logger.error(f"执行查询失败: {str(e)}")
            logger.error(f"查询SQL: {query}, 参数: {params}")
            return None
    
    def execute_update(self, query: str, params: Optional[Tuple] = None) -> int:
        """执行更新语句（INSERT, UPDATE, DELETE等）
        
        Args:
            query: SQL更新语句
            params: SQL参数
            
        Returns:
            int: 影响的行数
        """
        try:
            with self.get_cursor(commit=True) as cursor:
                if cursor:
                    affected_rows = cursor.execute(query, params or ())
                    logger.info(f"更新成功，影响 {affected_rows} 行")
                    return affected_rows
        except Exception as e:
            logger.error(f"执行更新失败: {str(e)}")
            logger.error(f"更新SQL: {query}, 参数: {params}")
            return 0
    
    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """插入单条记录
        
        Args:
            table: 表名
            data: 要插入的数据字典
            
        Returns:
            int: 影响的行数
        """
        fields = ', '.join([f'`{col}`' for col in data.keys()])
        placeholders = ', '.join(['%s'] * len(data))
        query = f"INSERT INTO {table} ({fields}) VALUES ({placeholders})"
        return self.execute_update(query, tuple(data.values()))
    
    def insert_many(self, table: str, data_list: List[Dict[str, Any]]) -> int:
        """批量插入记录
        
        Args:
            table: 表名
            data_list: 要插入的数据列表
            
        Returns:
            int: 影响的行数
        """
        if not data_list:
            return 0
            
        columns = ', '.join([f'`{col}`' for col in data_list[0].keys()])
        placeholders = ', '.join(['%s'] * len(data_list[0]))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        # 准备参数列表
        params_list = [tuple(data.values()) for data in data_list]
        
        try:
            with self.get_cursor(commit=True) as cursor:
                if cursor:
                    affected_rows = cursor.executemany(query, params_list)
                    logger.info(f"批量插入成功，插入 {affected_rows} 条记录")
                    return affected_rows
        except Exception as e:
            logger.error(f"批量插入失败: {str(e)}")
            logger.error(f"批量插入SQL: {query}")
        return 0
    
    def find_one(self, table: str, condition: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """查询单条记录
        
        Args:
            table: 表名
            condition: 查询条件
            
        Returns:
            Dict: 查询结果字典
        """
        columns = '*'
        query = f"SELECT {columns} FROM {table}"
        params = ()
        
        if condition:
            where_clause = ' AND '.join([f"`{k}` = %s" for k in condition.keys()])
            query += f" WHERE {where_clause}"
            params = tuple(condition.values())
            
        query += " LIMIT 1"
        
        results = self.execute_query(query, params)
        return results[0] if results else None
    
    def find_all(self, table: str, condition: Optional[Dict[str, Any]] = None, limit: int = 1000, offset: int = 0) -> List[Dict[str, Any]]:
        """查询多条记录
        
        Args:
            table: 表名
            condition: 查询条件
            limit: 限制返回的记录数
            offset: 偏移量
            
        Returns:
            List[Dict]: 查询结果列表
        """
        columns = '*'
        query = f"SELECT {columns} FROM {table}"
        params = ()
        
        if condition:
            where_clause = ' AND '.join([f"`{k}` = %s" for k in condition.keys()])
            query += f" WHERE {where_clause}"
            params = tuple(condition.values())
            
        query += f" LIMIT {limit} OFFSET {offset}"
        
        results = self.execute_query(query, params)
        return results if results else []
    
    def update(self, table: str, data: Dict[str, Any], condition: Dict[str, Any]) -> int:
        """更新记录
        
        Args:
            table: 表名
            data: 要更新的数据字典
            condition: 更新条件
            
        Returns:
            int: 影响的行数
        """
        set_clause = ', '.join([f"`{k}` = %s" for k in data.keys()])
        where_clause = ' AND '.join([f"`{k}` = %s" for k in condition.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        
        params = tuple(data.values()) + tuple(condition.values())
        return self.execute_update(query, params)
    
    def delete(self, table: str, condition: Dict[str, Any]) -> int:
        """删除记录
        
        Args:
            table: 表名
            condition: 删除条件
            
        Returns:
            int: 影响的行数
        """
        where_clause = ' AND '.join([f"`{k}` = %s" for k in condition.keys()])
        query = f"DELETE FROM {table} WHERE {where_clause}"
        
        return self.execute_update(query, tuple(condition.values()))
    
    def get_last_insert_id(self) -> int:
        """获取最后插入的ID
        
        Returns:
            int: 最后插入的ID
        """
        try:
            with self.get_cursor() as cursor:
                if cursor:
                    cursor.execute("SELECT LAST_INSERT_ID()")
                    result = cursor.fetchone()
                    return result.get('LAST_INSERT_ID()', 0)
        except Exception as e:
            logger.error(f"获取最后插入ID失败: {str(e)}")
        return 0
    
    def table_exists(self, table: str) -> bool:
        """检查表是否存在
        
        Args:
            table: 表名
            
        Returns:
            bool: 表是否存在
        """
        query = """SELECT 1 FROM information_schema.TABLES 
                  WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s"""
        
        try:
            result = self.execute_query(query, (self.db_name, table))
            return len(result) > 0 if result else False
        except Exception as e:
            logger.error(f"检查表是否存在失败: {str(e)}")
        return False
    
    def create_table(self, statement: str) -> bool:
        """创建表
        
        Args:
            statement: 创建表的SQL语句
            
        Returns:
            bool: 是否创建成功
        """
        try:
            self.execute_update(statement)
            return True
        except Exception as e:
            logger.error(f"创建表失败: {str(e)}")
        return False
