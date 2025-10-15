#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为数据库添加测试经纬度数据
用于快速演示地图找房功能
"""

import mysql.connector
import random
import time

# 北京主要区域的坐标范围
BEIJING_REGIONS = {
    '朝阳区': {
        'center': (39.9386, 116.4515),
        'lat_range': (39.8500, 39.9900),
        'lng_range': (116.4000, 116.5500)
    },
    '海淀区': {
        'center': (39.9598, 116.2982),
        'lat_range': (39.8800, 40.0200),
        'lng_range': (116.2000, 116.4000)
    },
    '丰台区': {
        'center': (39.8585, 116.2863),
        'lat_range': (39.7800, 39.9200),
        'lng_range': (116.1800, 116.3500)
    },
    '西城区': {
        'center': (39.9122, 116.3659),
        'lat_range': (39.8800, 39.9500),
        'lng_range': (116.3300, 116.4200)
    },
    '东城区': {
        'center': (39.9285, 116.4160),
        'lat_range': (39.8900, 39.9700),
        'lng_range': (116.3800, 116.4500)
    },
    '石景山区': {
        'center': (39.9066, 116.2223),
        'lat_range': (39.8400, 39.9700),
        'lng_range': (116.1500, 116.2800)
    }
}

def get_db_connection():
    """获取数据库连接"""
    return mysql.connector.connect(
        host='127.0.0.1',
        port=3306,
        user='root',
        password='',
        database='house',
        charset='utf8mb4'
    )

def generate_coordinates(region):
    """根据区域生成坐标"""
    if region in BEIJING_REGIONS:
        region_data = BEIJING_REGIONS[region]
        lat = random.uniform(*region_data['lat_range'])
        lng = random.uniform(*region_data['lng_range'])
        return lat, lng
    else:
        # 默认北京坐标
        return random.uniform(39.8, 40.1), random.uniform(116.2, 116.6)

def add_test_coordinates(limit=1000):
    """添加测试坐标数据"""
    print("开始添加测试经纬度数据...")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 获取没有坐标的记录
        sql = """
            SELECT id, region, address
            FROM house_info
            WHERE (latitude IS NULL OR longitude IS NULL)
            AND region IS NOT NULL
            LIMIT %s
        """
        cursor.execute(sql, (limit,))
        records = cursor.fetchall()

        print(f"找到 {len(records)} 条需要添加坐标的记录")

        updated_count = 0
        for record in records:
            house_id, region, address = record

            # 生成坐标
            lat, lng = generate_coordinates(region)

            # 更新数据库
            update_sql = """
                UPDATE house_info
                SET latitude = %s, longitude = %s
                WHERE id = %s
            """
            cursor.execute(update_sql, (lat, lng, house_id))

            updated_count += 1
            if updated_count % 100 == 0:
                print(f"已更新 {updated_count} 条记录...")

        conn.commit()
        cursor.close()
        conn.close()

        print(f"✅ 成功更新了 {updated_count} 条记录的经纬度数据！")

        # 验证更新结果
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM house_info WHERE latitude IS NOT NULL AND longitude IS NOT NULL")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        print(f"📊 现在数据库中有 {count} 条记录包含经纬度数据")

    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    print("=== 测试经纬度数据添加工具 ===")
    print("为北京区域的房源添加模拟经纬度数据")
    print("用于快速演示地图找房功能")
    print()

    # 添加1000条测试数据
    add_test_coordinates(1000)

    print("\n🎉 现在可以测试地图找房功能了！")
    print("访问: http://127.0.0.1:5000/map_search")