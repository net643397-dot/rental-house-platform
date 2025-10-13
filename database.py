"""
数据库连接和操作模块
"""
import pymysql
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional

class DatabaseManager:
    def __init__(self):
        self.config = {
            'host': '127.0.0.1',
            'port': 3306,
            'user': 'root',
            'password': '',
            'database': 'house',
            'charset': 'utf8mb4'
        }

    def get_connection(self):
        """获取数据库连接"""
        return pymysql.connect(**self.config)

    def get_houses(self,
                   search: str = '',
                   region: str = '',
                   rent_type: str = '',
                   rooms: str = '',
                   min_price: Optional[int] = None,
                   max_price: Optional[int] = None,
                   limit: int = 50,
                   offset: int = 0) -> pd.DataFrame:
        """
        获取房源列表
        """
        conn = self.get_connection()
        try:
            # 构建查询条件
            conditions = []
            params = []

            if search:
                conditions.append("(title LIKE %s OR address LIKE %s OR block LIKE %s)")
                search_pattern = f'%{search}%'
                params.extend([search_pattern, search_pattern, search_pattern])

            if region:
                conditions.append("region LIKE %s")
                params.append(f'%{region}%')

            if rent_type:
                conditions.append("rent_type = %s")
                params.append(rent_type)

            if rooms:
                conditions.append("rooms LIKE %s")
                params.append(f'%{rooms}%')

            if min_price:
                conditions.append("CAST(price AS UNSIGNED) >= %s")
                params.append(min_price)

            if max_price:
                conditions.append("CAST(price AS UNSIGNED) <= %s")
                params.append(max_price)

            # 构建SQL查询
            base_query = """
                SELECT id, title, rooms, area, price, direction, rent_type,
                       region, block, address, traffic, facilities, highlights,
                       page_views, landlord, phone_num
                FROM house_info
            """

            if conditions:
                base_query += " WHERE " + " AND ".join(conditions)

            base_query += " ORDER BY id DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            # 执行查询
            df = pd.read_sql(base_query, conn, params=params)
            return df

        finally:
            conn.close()

    def get_house_detail(self, house_id: int) -> Dict:
        """获取房源详情"""
        conn = self.get_connection()
        try:
            query = "SELECT * FROM house_info WHERE id = %s"
            df = pd.read_sql(query, conn, params=[house_id])

            if len(df) > 0:
                # 更新浏览次数
                update_query = """
                    UPDATE house_info
                    SET page_views = COALESCE(page_views, 0) + 1
                    WHERE id = %s
                """
                with conn.cursor() as cursor:
                    cursor.execute(update_query, [house_id])
                    conn.commit()

                return df.iloc[0].to_dict()
            return {}

        finally:
            conn.close()

    def get_regions(self) -> List[str]:
        """获取所有区域"""
        conn = self.get_connection()
        try:
            query = "SELECT DISTINCT region FROM house_info WHERE region IS NOT NULL AND region != '' ORDER BY region"
            df = pd.read_sql(query, conn)
            return df['region'].tolist()
        finally:
            conn.close()

    def get_total_count(self, **filters) -> int:
        """获取符合条件的房源总数"""
        conn = self.get_connection()
        try:
            conditions = []
            params = []

            # 复用get_houses的筛选逻辑
            if filters.get('search'):
                conditions.append("(title LIKE %s OR address LIKE %s OR block LIKE %s)")
                search_pattern = f'%{filters["search"]}%'
                params.extend([search_pattern, search_pattern, search_pattern])

            if filters.get('region'):
                conditions.append("region LIKE %s")
                params.append(f'%{filters["region"]}%')

            if filters.get('rent_type'):
                conditions.append("rent_type = %s")
                params.append(filters['rent_type'])

            if filters.get('rooms'):
                conditions.append("rooms LIKE %s")
                params.append(f'%{filters["rooms"]}%')

            if filters.get('min_price'):
                conditions.append("CAST(price AS UNSIGNED) >= %s")
                params.append(filters['min_price'])

            if filters.get('max_price'):
                conditions.append("CAST(price AS UNSIGNED) <= %s")
                params.append(filters['max_price'])

            query = "SELECT COUNT(*) as count FROM house_info"
            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            df = pd.read_sql(query, conn, params=params)
            return df.iloc[0]['count']
        finally:
            conn.close()

    def add_favorite(self, user_id: str, house_id: int) -> bool:
        """添加收藏"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                # 检查是否已收藏
                check_query = "SELECT id FROM favorites WHERE user_id = %s AND house_id = %s"
                cursor.execute(check_query, [user_id, house_id])
                if cursor.fetchone():
                    return False  # 已收藏

                # 添加收藏
                insert_query = """
                    INSERT INTO favorites (user_id, house_id, created_at)
                    VALUES (%s, %s, %s)
                """
                cursor.execute(insert_query, [user_id, house_id, datetime.now()])
                conn.commit()
                return True
        finally:
            conn.close()

    def remove_favorite(self, user_id: str, house_id: int) -> bool:
        """取消收藏"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                delete_query = "DELETE FROM favorites WHERE user_id = %s AND house_id = %s"
                result = cursor.execute(delete_query, [user_id, house_id])
                conn.commit()
                return result > 0
        finally:
            conn.close()

    def get_favorites(self, user_id: str) -> pd.DataFrame:
        """获取用户收藏列表"""
        conn = self.get_connection()
        try:
            query = """
                SELECT h.id, h.title, h.rooms, h.area, h.price, h.direction,
                       h.rent_type, h.region, h.address, h.page_views
                FROM house_info h
                INNER JOIN favorites f ON h.id = f.house_id
                WHERE f.user_id = %s
                ORDER BY f.created_at DESC
            """
            df = pd.read_sql(query, conn, params=[user_id])
            return df
        finally:
            conn.close()

    def is_favorite(self, user_id: str, house_id: int) -> bool:
        """检查是否已收藏"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                query = "SELECT id FROM favorites WHERE user_id = %s AND house_id = %s"
                cursor.execute(query, [user_id, house_id])
                return cursor.fetchone() is not None
        finally:
            conn.close()

# 创建全局数据库管理器实例
db_manager = DatabaseManager()