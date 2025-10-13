"""
坐标系转换工具
支持GCJ-02（高德/谷歌中国）和BD-09（百度）之间的转换
"""
import math

# 常量定义
X_PI = math.pi * 3000.0 / 180.0
PI = math.pi
A = 6378245.0  # 长半轴
EE = 0.00669342162296594323  # 偏心率平方


def gcj02_to_bd09(lng, lat):
    """
    GCJ-02（火星坐标系）转换为BD-09（百度坐标系）

    Args:
        lng: GCJ-02经度
        lat: GCJ-02纬度

    Returns:
        (bd_lng, bd_lat): 百度坐标系的经纬度
    """
    if lng is None or lat is None:
        return None, None

    z = math.sqrt(lng * lng + lat * lat) + 0.00002 * math.sin(lat * X_PI)
    theta = math.atan2(lat, lng) + 0.000003 * math.cos(lng * X_PI)
    bd_lng = z * math.cos(theta) + 0.0065
    bd_lat = z * math.sin(theta) + 0.006

    return bd_lng, bd_lat


def bd09_to_gcj02(bd_lng, bd_lat):
    """
    BD-09（百度坐标系）转换为GCJ-02（火星坐标系）

    Args:
        bd_lng: 百度坐标系经度
        bd_lat: 百度坐标系纬度

    Returns:
        (lng, lat): GCJ-02坐标系的经纬度
    """
    if bd_lng is None or bd_lat is None:
        return None, None

    x = bd_lng - 0.0065
    y = bd_lat - 0.006
    z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * X_PI)
    theta = math.atan2(y, x) - 0.000003 * math.cos(x * X_PI)
    lng = z * math.cos(theta)
    lat = z * math.sin(theta)

    return lng, lat


def wgs84_to_gcj02(lng, lat):
    """
    WGS-84转GCJ-02（火星坐标系）
    """
    if lng is None or lat is None:
        return None, None

    if out_of_china(lng, lat):
        return lng, lat

    dlat = _transformlat(lng - 105.0, lat - 35.0)
    dlng = _transformlng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * PI
    magic = math.sin(radlat)
    magic = 1 - EE * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((A * (1 - EE)) / (magic * sqrtmagic) * PI)
    dlng = (dlng * 180.0) / (A / sqrtmagic * math.cos(radlat) * PI)
    mglat = lat + dlat
    mglng = lng + dlng

    return mglng, mglat


def gcj02_to_wgs84(lng, lat):
    """
    GCJ-02（火星坐标系）转WGS-84
    """
    if lng is None or lat is None:
        return None, None

    if out_of_china(lng, lat):
        return lng, lat

    dlat = _transformlat(lng - 105.0, lat - 35.0)
    dlng = _transformlng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * PI
    magic = math.sin(radlat)
    magic = 1 - EE * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((A * (1 - EE)) / (magic * sqrtmagic) * PI)
    dlng = (dlng * 180.0) / (A / sqrtmagic * math.cos(radlat) * PI)
    mglat = lat + dlat
    mglng = lng + dlng

    return lng * 2 - mglng, lat * 2 - mglat


def bd09_to_wgs84(bd_lng, bd_lat):
    """
    BD-09（百度坐标系）转WGS-84
    """
    lng, lat = bd09_to_gcj02(bd_lng, bd_lat)
    return gcj02_to_wgs84(lng, lat)


def wgs84_to_bd09(lng, lat):
    """
    WGS-84转BD-09（百度坐标系）
    """
    lng, lat = wgs84_to_gcj02(lng, lat)
    return gcj02_to_bd09(lng, lat)


def _transformlat(lng, lat):
    """纬度转换辅助函数"""
    ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + \
          0.1 * lng * lat + 0.2 * math.sqrt(abs(lng))
    ret += (20.0 * math.sin(6.0 * lng * PI) + 20.0 *
            math.sin(2.0 * lng * PI)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lat * PI) + 40.0 *
            math.sin(lat / 3.0 * PI)) * 2.0 / 3.0
    ret += (160.0 * math.sin(lat / 12.0 * PI) + 320 *
            math.sin(lat * PI / 30.0)) * 2.0 / 3.0
    return ret


def _transformlng(lng, lat):
    """经度转换辅助函数"""
    ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + \
          0.1 * lng * lat + 0.1 * math.sqrt(abs(lng))
    ret += (20.0 * math.sin(6.0 * lng * PI) + 20.0 *
            math.sin(2.0 * lng * PI)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lng * PI) + 40.0 *
            math.sin(lng / 3.0 * PI)) * 2.0 / 3.0
    ret += (150.0 * math.sin(lng / 12.0 * PI) + 300.0 *
            math.sin(lng / 30.0 * PI)) * 2.0 / 3.0
    return ret


def out_of_china(lng, lat):
    """判断坐标是否在中国境外"""
    return not (73.66 < lng < 135.05 and 3.86 < lat < 53.55)


if __name__ == '__main__':
    # 测试代码
    print("=== 坐标转换测试 ===")

    # GCJ-02坐标（高德地图，北京天安门）
    gcj_lng, gcj_lat = 116.404, 39.915
    print(f"\nGCJ-02坐标（高德）: {gcj_lng}, {gcj_lat}")

    # 转换为百度坐标
    bd_lng, bd_lat = gcj02_to_bd09(gcj_lng, gcj_lat)
    print(f"BD-09坐标（百度）: {bd_lng:.6f}, {bd_lat:.6f}")

    # 转换回来验证
    back_lng, back_lat = bd09_to_gcj02(bd_lng, bd_lat)
    print(f"转换回GCJ-02: {back_lng:.6f}, {back_lat:.6f}")

    print(f"\n偏差: 经度 {abs(gcj_lng - back_lng):.8f}, 纬度 {abs(gcj_lat - back_lat):.8f}")
