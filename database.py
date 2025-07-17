import aiomysql
import asyncio
import logging
from typing import Optional, Dict, List, Any
from config import MYSQL_CONFIG

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.pool = None
    
    async def connect(self):
        """Создание пула соединений с базой данных"""
        try:
            self.pool = await aiomysql.create_pool(
                minsize=5,
                maxsize=20,
                **MYSQL_CONFIG
            )
            logger.info("Database connection pool created successfully")
            await self.create_tables()
        except Exception as e:
            logger.error(f"Error creating database pool: {e}")
            raise
    
    async def close(self):
        """Закрытие пула соединений"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
    
    async def execute_query(self, query: str, params: tuple = None) -> Optional[Any]:
        """Выполнение SQL запроса"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(query, params)
                    if query.strip().upper().startswith('SELECT'):
                        return await cursor.fetchall()
                    else:
                        await conn.commit()
                        return cursor.rowcount
                except Exception as e:
                    logger.error(f"Database query error: {e}")
                    await conn.rollback()
                    raise
    
    async def execute_fetchone(self, query: str, params: tuple = None) -> Optional[tuple]:
        """Выполнение SQL запроса с получением одной записи"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(query, params)
                    return await cursor.fetchone()
                except Exception as e:
                    logger.error(f"Database fetchone error: {e}")
                    raise
    
    async def create_tables(self):
        """Создание таблиц в базе данных"""
        tables = [
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username VARCHAR(255),
                first_name VARCHAR(255),
                last_name VARCHAR(255),
                is_verified BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                deals_count INT DEFAULT 0,
                successful_deals INT DEFAULT 0,
                rating DECIMAL(3,2) DEFAULT 0.00,
                is_banned BOOLEAN DEFAULT FALSE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS captcha_sessions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT NOT NULL,
                captcha_type VARCHAR(50) NOT NULL,
                correct_answer VARCHAR(255) NOT NULL,
                attempts INT DEFAULT 0,
                is_solved BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                INDEX idx_user_id (user_id),
                INDEX idx_expires_at (expires_at)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS deals (
                id INT AUTO_INCREMENT PRIMARY KEY,
                deal_code VARCHAR(10) UNIQUE NOT NULL,
                creator_id BIGINT NOT NULL,
                participant_id BIGINT,
                creator_role ENUM('buyer', 'seller') NOT NULL,
                amount_usd DECIMAL(10,2) NOT NULL,
                deal_conditions TEXT NOT NULL,
                deal_password VARCHAR(255) NOT NULL,
                status ENUM('created', 'joined', 'payment_pending', 'completed', 'cancelled', 'disputed') DEFAULT 'created',
                payment_method ENUM('TRC20', 'TON'),
                payment_proof TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                completed_at TIMESTAMP NULL,
                expires_at TIMESTAMP NOT NULL,
                INDEX idx_creator_id (creator_id),
                INDEX idx_participant_id (participant_id),
                INDEX idx_deal_code (deal_code),
                INDEX idx_status (status)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS deal_messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                deal_id INT NOT NULL,
                user_id BIGINT NOT NULL,
                message_type ENUM('system', 'user', 'payment_proof') NOT NULL,
                message_text TEXT,
                file_id VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (deal_id) REFERENCES deals(id) ON DELETE CASCADE,
                INDEX idx_deal_id (deal_id),
                INDEX idx_user_id (user_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS user_sessions (
                user_id BIGINT PRIMARY KEY,
                current_action VARCHAR(100),
                session_data JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """
        ]
        
        for table_sql in tables:
            try:
                await self.execute_query(table_sql)
                logger.info("Table created successfully")
            except Exception as e:
                logger.error(f"Error creating table: {e}")
                raise
    
    # User methods
    async def create_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None):
        """Создание нового пользователя"""
        query = """
        INSERT INTO users (user_id, username, first_name, last_name)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        username = VALUES(username),
        first_name = VALUES(first_name),
        last_name = VALUES(last_name),
        updated_at = CURRENT_TIMESTAMP
        """
        return await self.execute_query(query, (user_id, username, first_name, last_name))
    
    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Получение информации о пользователе"""
        query = "SELECT * FROM users WHERE user_id = %s"
        result = await self.execute_fetchone(query, (user_id,))
        if result:
            return {
                'user_id': result[0],
                'username': result[1],
                'first_name': result[2],
                'last_name': result[3],
                'is_verified': result[4],
                'created_at': result[5],
                'updated_at': result[6],
                'deals_count': result[7],
                'successful_deals': result[8],
                'rating': result[9],
                'is_banned': result[10]
            }
        return None
    
    async def verify_user(self, user_id: int):
        """Подтверждение пользователя после прохождения капчи"""
        query = "UPDATE users SET is_verified = TRUE WHERE user_id = %s"
        return await self.execute_query(query, (user_id,))
    
    # Captcha methods
    async def create_captcha_session(self, user_id: int, captcha_type: str, correct_answer: str, expires_at):
        """Создание сессии капчи"""
        query = """
        INSERT INTO captcha_sessions (user_id, captcha_type, correct_answer, expires_at)
        VALUES (%s, %s, %s, %s)
        """
        return await self.execute_query(query, (user_id, captcha_type, correct_answer, expires_at))
    
    async def get_captcha_session(self, user_id: int) -> Optional[Dict]:
        """Получение активной сессии капчи"""
        query = """
        SELECT * FROM captcha_sessions 
        WHERE user_id = %s AND is_solved = FALSE AND expires_at > NOW()
        ORDER BY created_at DESC LIMIT 1
        """
        result = await self.execute_fetchone(query, (user_id,))
        if result:
            return {
                'id': result[0],
                'user_id': result[1],
                'captcha_type': result[2],
                'correct_answer': result[3],
                'attempts': result[4],
                'is_solved': result[5],
                'created_at': result[6],
                'expires_at': result[7]
            }
        return None
    
    async def update_captcha_attempts(self, session_id: int, attempts: int):
        """Обновление количества попыток капчи"""
        query = "UPDATE captcha_sessions SET attempts = %s WHERE id = %s"
        return await self.execute_query(query, (attempts, session_id))
    
    async def solve_captcha(self, session_id: int):
        """Отметка капчи как решенной"""
        query = "UPDATE captcha_sessions SET is_solved = TRUE WHERE id = %s"
        return await self.execute_query(query, (session_id,))
    
    # Deal methods
    async def create_deal(self, creator_id: int, creator_role: str, amount_usd: float, 
                         conditions: str, password: str, deal_code: str, expires_at) -> int:
        """Создание новой сделки"""
        query = """
        INSERT INTO deals (creator_id, creator_role, amount_usd, deal_conditions, 
                          deal_password, deal_code, expires_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        await self.execute_query(query, (creator_id, creator_role, amount_usd, 
                                       conditions, password, deal_code, expires_at))
        
        # Получаем ID созданной сделки
        result = await self.execute_fetchone("SELECT LAST_INSERT_ID()")
        return result[0] if result else None
    
    async def get_deal_by_code(self, deal_code: str) -> Optional[Dict]:
        """Получение сделки по коду"""
        query = "SELECT * FROM deals WHERE deal_code = %s"
        result = await self.execute_fetchone(query, (deal_code,))
        if result:
            return {
                'id': result[0],
                'deal_code': result[1],
                'creator_id': result[2],
                'participant_id': result[3],
                'creator_role': result[4],
                'amount_usd': result[5],
                'deal_conditions': result[6],
                'deal_password': result[7],
                'status': result[8],
                'payment_method': result[9],
                'payment_proof': result[10],
                'created_at': result[11],
                'updated_at': result[12],
                'completed_at': result[13],
                'expires_at': result[14]
            }
        return None
    
    async def join_deal(self, deal_id: int, participant_id: int):
        """Присоединение к сделке"""
        query = "UPDATE deals SET participant_id = %s, status = 'joined' WHERE id = %s"
        return await self.execute_query(query, (participant_id, deal_id))
    
    async def update_deal_status(self, deal_id: int, status: str):
        """Обновление статуса сделки"""
        query = "UPDATE deals SET status = %s WHERE id = %s"
        return await self.execute_query(query, (status, deal_id))
    
    async def set_payment_method(self, deal_id: int, payment_method: str):
        """Установка метода оплаты"""
        query = "UPDATE deals SET payment_method = %s, status = 'payment_pending' WHERE id = %s"
        return await self.execute_query(query, (payment_method, deal_id))
    
    async def get_user_deals(self, user_id: int) -> List[Dict]:
        """Получение всех сделок пользователя"""
        query = """
        SELECT * FROM deals 
        WHERE creator_id = %s OR participant_id = %s 
        ORDER BY created_at DESC
        """
        results = await self.execute_query(query, (user_id, user_id))
        deals = []
        if results:
            for result in results:
                deals.append({
                    'id': result[0],
                    'deal_code': result[1],
                    'creator_id': result[2],
                    'participant_id': result[3],
                    'creator_role': result[4],
                    'amount_usd': result[5],
                    'deal_conditions': result[6],
                    'status': result[8],
                    'created_at': result[11]
                })
        return deals
    
    # Session methods
    async def set_user_session(self, user_id: int, action: str, data: Dict = None):
        """Установка пользовательской сессии"""
        import json
        query = """
        INSERT INTO user_sessions (user_id, current_action, session_data)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
        current_action = VALUES(current_action),
        session_data = VALUES(session_data),
        updated_at = CURRENT_TIMESTAMP
        """
        session_data = json.dumps(data) if data else None
        return await self.execute_query(query, (user_id, action, session_data))
    
    async def get_user_session(self, user_id: int) -> Optional[Dict]:
        """Получение пользовательской сессии"""
        query = "SELECT * FROM user_sessions WHERE user_id = %s"
        result = await self.execute_fetchone(query, (user_id,))
        if result:
            import json
            return {
                'user_id': result[0],
                'current_action': result[1],
                'session_data': json.loads(result[2]) if result[2] else {},
                'created_at': result[3],
                'updated_at': result[4]
            }
        return None
    
    async def clear_user_session(self, user_id: int):
        """Очистка пользовательской сессии"""
        query = "DELETE FROM user_sessions WHERE user_id = %s"
        return await self.execute_query(query, (user_id,))

# Создание глобального экземпляра базы данных
db = Database()