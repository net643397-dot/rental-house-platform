"""
地理位置处理工具模块
"""
import math
import requests
from typing import Tuple, Optional, Dict

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    使用Haversine公式计算两点间的距离（单位：公里）
    """
    # 将度数转换为弧度
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # 计算差值
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Haversine公式
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    # 地球半径（公里）
    earth_radius = 6371
    distance = earth_radius * c

    return round(distance, 2)

def get_address_coordinates(address: str, api_key: str = None) -> Optional[Tuple[float, float]]:
    """
    通过地址获取经纬度坐标（地理编码）
    这里提供百度地图API的示例，你需要申请API密钥
    """
    if not api_key:
        # 如果没有API密钥，返回None
        return None

    try:
        # 百度地图地理编码API
        url = "http://api.map.baidu.com/geocoding/v3/"
        params = {
            'address': address,
            'output': 'json',
            'ak': api_key
        }

        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        if data['status'] == 0:
            location = data['result']['location']
            return (location['lat'], location['lng'])
        else:
            print(f"地理编码失败: {data.get('message', 'Unknown error')}")
            return None

    except Exception as e:
        print(f"获取坐标失败: {str(e)}")
        return None

def get_coordinates_address(lat: float, lon: float, api_key: str = None) -> Optional[str]:
    """
    通过经纬度获取地址（逆地理编码）
    """
    if not api_key:
        return None

    try:
        # 百度地图逆地理编码API
        url = "http://api.map.baidu.com/reverse_geocoding/v3/"
        params = {
            'lat': lat,
            'lng': lon,
            'output': 'json',
            'ak': api_key
        }

        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        if data['status'] == 0:
            return data['result']['formatted_address']
        else:
            print(f"逆地理编码失败: {data.get('message', 'Unknown error')}")
            return None

    except Exception as e:
        print(f"获取地址失败: {str(e)}")
        return None

def get_nearby_bounds(lat: float, lon: float, radius_km: float = 5.0) -> Dict[str, float]:
    """
    根据中心点和半径计算边界框（用于数据库查询优化）

    Args:
        lat: 中心点纬度
        lon: 中心点经度
        radius_km: 半径（公里）

    Returns:
        包含min_lat, max_lat, min_lon, max_lon的字典
    """
    # 地球半径（公里）
    earth_radius = 6371

    # 计算纬度边界（1度纬度约等于111公里）
    lat_delta = radius_km / 111.0
    min_lat = lat - lat_delta
    max_lat = lat + lat_delta

    # 计算经度边界（经度间距离随纬度变化）
    lon_delta = radius_km / (111.0 * math.cos(math.radians(lat)))
    min_lon = lon - lon_delta
    max_lon = lon + lon_delta

    return {
        'min_lat': min_lat,
        'max_lat': max_lat,
        'min_lon': min_lon,
        'max_lon': max_lon
    }

def format_distance(distance: float) -> str:
    """
    格式化距离显示
    """
    if distance < 1:
        return f"{int(distance * 1000)}米"
    else:
        return f"{distance:.1f}公里"

# 常用城市坐标（用于示例和测试）
CITY_COORDINATES = {
    '北京': (39.9042, 116.4074),
    '上海': (31.2304, 121.4737),
    '广州': (23.1291, 113.2644),
    '深圳': (22.5431, 114.0579),
    '杭州': (30.2741, 120.1551),
    '南京': (32.0603, 118.7969),
    '成都': (30.5728, 104.0668),
    '武汉': (30.5928, 114.3055),
    '西安': (34.3416, 108.9398),
    '重庆': (29.5630, 106.5516)
}