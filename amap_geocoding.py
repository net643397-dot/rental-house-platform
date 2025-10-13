#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高德地图API地理编码脚本
100万次/天免费配额，替代百度地图API
"""

import requests
import time
import json
import mysql.connector
from datetime import datetime, date
import logging
import os
import random

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'amap_geocoding_{date.today().strftime("%Y%m%d")}.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class AmapGeocoder:
    def __init__(self, api_key):
        """初始化高德地图地理编码器"""
        self.api_key = api_key
        self.base_url = "https://restapi.amap.com/v3/geocode/geo"
        self.session = requests.Session()

        # 处理配置 - 高德地图配额更高，可以更快处理
        self.daily_quota = 1000000  # 100万次/天
        self.requests_per_second = 10  # 10次/秒
        self.delay = 1.0 / self.requests_per_second

        # 重试配置
        self.max_retries = 3
        self.retry_delay = 2
        self.concurrent_error_delay = 5

        # 统计信息
        self.today_processed = 0
        self.success_count = 0
        self.fail_count = 0
        self.retry_count = 0
        self.start_time = datetime.now()

    def load_progress(self):
        """加载今日处理进度"""
        progress_file = f"amap_progress_{date.today().strftime('%Y%m%d')}.json"
        if os.path.exists(progress_file):
            try:
                with open(progress_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.today_processed = data.get('processed', 0)
                    self.success_count = data.get('success', 0)
                    self.fail_count = data.get('failed', 0)
                    self.retry_count = data.get('retries', 0)
                    logging.info(f"加载今日进度: 已处理 {self.today_processed} 条")
            except Exception as e:
                logging.warning(f"进度文件加载失败: {e}")

    def save_progress(self):
        """保存今日处理进度"""
        progress_file = f"amap_progress_{date.today().strftime('%Y%m%d')}.json"
        progress_data = {
            'date': date.today().isoformat(),
            'processed': self.today_processed,
            'success': self.success_count,
            'failed': self.fail_count,
            'retries': self.retry_count,
            'remaining_quota': self.daily_quota - self.today_processed,
            'last_update': datetime.now().isoformat(),
            'success_rate': round((self.success_count/max(1,self.today_processed))*100, 2)
        }

        try:
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"进度保存失败: {e}")

    def get_db_connection(self):
        """获取数据库连接"""
        return mysql.connector.connect(
            host='127.0.0.1',
            port=3306,
            user='root',
            password='',
            database='house',
            charset='utf8mb4'
        )

    def get_addresses_batch(self, offset=0, limit=1000):
        """批量获取待处理地址"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            sql = """
                SELECT id, address, region
                FROM house_info
                WHERE (latitude IS NULL OR longitude IS NULL)
                AND address IS NOT NULL
                AND address != ''
                ORDER BY id
                LIMIT %s OFFSET %s
            """

            cursor.execute(sql, (limit, offset))
            results = cursor.fetchall()

            cursor.close()
            conn.close()

            return results

        except Exception as e:
            logging.error(f"数据库查询失败: {e}")
            return []

    def clean_address(self, address, region):
        """清理地址格式"""
        if not address or address.strip() == '':
            return region if region else ""

        cleaned = address.strip()

        # 如果地址太短，补充区域信息
        if len(cleaned) < 8 and region:
            cleaned = f"{region} {cleaned}"

        # 添加城市前缀
        if "北京" not in cleaned and "天津" not in cleaned and "上海" not in cleaned:
            cleaned = f"北京市{cleaned}"

        return cleaned

    def geocode_address_with_retry(self, address):
        """带重试机制的地理编码"""
        if self.today_processed >= self.daily_quota:
            logging.warning("今日配额已用完，请明天继续处理")
            return None, None

        for retry in range(self.max_retries + 1):
            try:
                params = {
                    'address': address,
                    'output': 'json',
                    'key': self.api_key
                }

                response = self.session.get(self.base_url, params=params, timeout=15)
                self.today_processed += 1

                if response.status_code == 200:
                    data = response.json()

                    if data.get('status') == '1':
                        geocodes = data.get('geocodes', [])
                        if geocodes and len(geocodes) > 0:
                            location = geocodes[0].get('location', '')
                            if location and ',' in location:
                                lng, lat = location.split(',')
                                self.success_count += 1
                                return float(lat), float(lng)

                    elif data.get('status') == '0':
                        error_info = data.get('info', '未知错误')
                        if '配额' in error_info or 'QUOTA' in error_info.upper():
                            logging.error("高德地图天配额超限，停止处理")
                            return "QUOTA_EXCEEDED", "QUOTA_EXCEEDED"
                        elif 'QPS' in error_info.upper() or '并发' in error_info:
                            if retry < self.max_retries:
                                self.retry_count += 1
                                wait_time = self.retry_delay + self.concurrent_error_delay + random.uniform(1, 3)
                                logging.warning(f"QPS限制，{wait_time:.1f}秒后重试 ({retry+1}/{self.max_retries}): {address}")
                                time.sleep(wait_time)
                                continue
                            else:
                                logging.warning(f"QPS限制重试失败: {address}")
                        else:
                            logging.warning(f"高德API错误: {address} - {error_info}")
                        break
                    else:
                        logging.warning(f"高德API未知状态: {address} - {data}")
                        break
                else:
                    logging.error(f"HTTP错误: {response.status_code}")
                    if retry < self.max_retries:
                        time.sleep(self.retry_delay)
                        continue
                    break

            except Exception as e:
                logging.error(f"请求异常: {address} - {e}")
                if retry < self.max_retries:
                    time.sleep(self.retry_delay)
                    continue
                break

        self.fail_count += 1
        return None, None

    def update_coordinates(self, house_id, latitude, longitude):
        """更新数据库坐标"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            sql = "UPDATE house_info SET latitude = %s, longitude = %s WHERE id = %s"
            cursor.execute(sql, (latitude, longitude, house_id))
            conn.commit()

            cursor.close()
            conn.close()
            return True

        except Exception as e:
            logging.error(f"数据库更新失败: ID={house_id}, error: {e}")
            return False

    def get_remaining_count(self):
        """获取剩余待处理数量"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM house_info WHERE latitude IS NULL OR longitude IS NULL")
            count = cursor.fetchone()[0]

            cursor.close()
            conn.close()

            return count
        except:
            return 0

    def process_geocoding(self):
        """执行地理编码处理任务"""
        # 加载进度
        self.load_progress()

        logging.info("=" * 60)
        logging.info(f"开始高德地图地理编码处理 - {date.today()}")
        logging.info(f"优化特性: 高配额(100万/天), 智能重试, 稳定处理")
        logging.info(f"今日配额: {self.daily_quota:,} 次")
        logging.info(f"已使用: {self.today_processed:,} 次")
        logging.info(f"剩余配额: {self.daily_quota - self.today_processed:,} 次")
        logging.info("=" * 60)

        if self.today_processed >= self.daily_quota:
            logging.info("今日配额已用完，请明天继续")
            return

        # 获取待处理总数
        total_remaining = self.get_remaining_count()
        logging.info(f"数据库中剩余待处理记录: {total_remaining:,} 条")

        # 处理参数
        batch_size = 1000
        processed_today = 0
        offset = 0
        consecutive_quota_errors = 0

        try:
            while (self.today_processed < self.daily_quota and
                   processed_today < self.daily_quota - self.today_processed):

                # 获取本批数据
                batch_addresses = self.get_addresses_batch(offset, batch_size)

                if not batch_addresses:
                    logging.info("所有记录处理完成！")
                    break

                logging.info(f"处理批次: offset={offset}, 获取到 {len(batch_addresses)} 条记录")

                # 处理本批数据
                for i, (house_id, address, region) in enumerate(batch_addresses):
                    if self.today_processed >= self.daily_quota:
                        logging.warning("达到今日配额限制")
                        break

                    # 清理地址
                    clean_addr = self.clean_address(address, region)

                    # 地理编码（带重试）
                    lat, lng = self.geocode_address_with_retry(clean_addr)

                    if lat == "QUOTA_EXCEEDED":
                        logging.error("遇到配额超限，停止处理")
                        consecutive_quota_errors += 1
                        if consecutive_quota_errors >= 3:
                            break
                        continue

                    consecutive_quota_errors = 0

                    if lat and lng:
                        # 更新数据库
                        if self.update_coordinates(house_id, lat, lng):
                            logging.info(f"✅ ID:{house_id} {clean_addr} -> ({lat:.6f}, {lng:.6f})")
                        else:
                            logging.error(f"❌ 数据库更新失败: ID={house_id}")
                    else:
                        logging.warning(f"⚠️  地理编码失败: ID={house_id} {clean_addr}")

                    processed_today += 1

                    # 控制请求频率
                    time.sleep(self.delay)

                    # 每处理100条保存一次进度
                    if processed_today % 100 == 0:
                        self.save_progress()
                        remaining = self.daily_quota - self.today_processed
                        success_rate = (self.success_count/max(1,self.today_processed))*100
                        logging.info(f"进度: 今日已处理 {self.today_processed:,}/{self.daily_quota:,}, "
                                   f"成功 {self.success_count}, 失败 {self.fail_count}, "
                                   f"重试 {self.retry_count}, 成功率 {success_rate:.1f}%, "
                                   f"剩余配额 {remaining:,}")

                if consecutive_quota_errors >= 3:
                    logging.error("连续遇到配额错误，停止处理")
                    break

                offset += batch_size

            # 最终保存进度
            self.save_progress()

            # 输出今日统计
            elapsed = datetime.now() - self.start_time
            success_rate = (self.success_count/max(1,self.today_processed))*100

            logging.info("=" * 60)
            logging.info(f"高德地图处理完成！")
            logging.info(f"处理时间: {elapsed}")
            logging.info(f"今日使用配额: {self.today_processed:,}/{self.daily_quota:,}")
            logging.info(f"成功处理: {self.success_count:,} 条")
            logging.info(f"失败记录: {self.fail_count:,} 条")
            logging.info(f"重试次数: {self.retry_count:,} 次")
            logging.info(f"成功率: {success_rate:.2f}%")

            # 检查是否还有未处理记录
            remaining_total = self.get_remaining_count()
            if remaining_total > 0:
                logging.info(f"数据库剩余: {remaining_total:,} 条记录")
                if self.success_count > 0:
                    estimated_days = remaining_total / self.success_count
                    logging.info(f"预计还需 {estimated_days:.1f} 天完成")
            else:
                logging.info("🎉 全部记录处理完成！")
            logging.info("=" * 60)

        except KeyboardInterrupt:
            logging.info("用户中断处理...")
            self.save_progress()
        except Exception as e:
            logging.error(f"处理过程发生异常: {e}")
            self.save_progress()

def main():
    """主函数"""
    print("高德地图API地理编码工具")
    print("=" * 50)

    # API密钥配置
    AMAP_API_KEY = "8ee0ac34b1d87ea07958b4ad595742a2"  # 高德地图API密钥

    if AMAP_API_KEY == "YOUR_AMAP_API_KEY":
        print("❌ 请先设置高德地图API密钥！")
        print("修改脚本中的 AMAP_API_KEY 变量")
        return

    # 创建处理器
    geocoder = AmapGeocoder(AMAP_API_KEY)

    print(f"📅 今日: {date.today()}")
    print(f"📊 日配额: {geocoder.daily_quota:,} 次 (高德地图)")
    print(f"⏱️  处理速度: {geocoder.requests_per_second} 次/秒")
    print(f"🔄 最大重试: {geocoder.max_retries} 次")
    print(f"⏳ 预计时间: {geocoder.daily_quota/geocoder.requests_per_second/3600:.1f} 小时 (满配额)")
    print()

    print("🚀 自动开始地理编码处理...")
    geocoder.process_geocoding()

if __name__ == "__main__":
    main()