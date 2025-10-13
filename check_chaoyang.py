import pymysql

conn = pymysql.connect(
    host='127.0.0.1',
    port=3306,
    user='root',
    password='',
    database='house',
    charset='utf8mb4'
)
cursor = conn.cursor()

# 检查朝阳区房源
cursor.execute("""
    SELECT COUNT(*)
    FROM house_info
    WHERE region LIKE '%朝阳%'
    AND latitude IS NOT NULL
    AND longitude IS NOT NULL
""")
chaoyang_total = cursor.fetchone()[0]
print(f'朝阳区有经纬度的房源: {chaoyang_total}')

# 查看朝阳区样本数据
cursor.execute("""
    SELECT id, title, address, region, latitude, longitude
    FROM house_info
    WHERE region LIKE '%朝阳%'
    AND latitude IS NOT NULL
    AND longitude IS NOT NULL
    LIMIT 10
""")
samples = cursor.fetchall()
print('\n朝阳区房源样本:')
for row in samples:
    print(f'ID:{row[0]} {row[1][:30]} 区域:{row[3]} 坐标:({row[4]}, {row[5]})')

# 检查北京市中心39.915, 116.404附近5公里的房源
cursor.execute("""
    SELECT COUNT(*)
    FROM house_info
    WHERE latitude IS NOT NULL
    AND longitude IS NOT NULL
    AND latitude BETWEEN 39.870 AND 39.960
    AND longitude BETWEEN 116.359 AND 116.449
""")
center_count = cursor.fetchone()[0]
print(f'\n北京市中心(39.915, 116.404)附近的房源: {center_count}')

cursor.close()
conn.close()
