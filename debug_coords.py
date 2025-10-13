from app import app, HouseInfo, db

with app.app_context():
    # 检查总数
    total = HouseInfo.query.filter(
        HouseInfo.latitude.isnot(None),
        HouseInfo.longitude.isnot(None)
    ).count()
    print(f'Total houses with coords: {total}')

    # 查看经纬度范围
    houses = HouseInfo.query.filter(
        HouseInfo.latitude.isnot(None),
        HouseInfo.longitude.isnot(None)
    ).limit(20).all()

    print('\nSample coordinates:')
    for house in houses:
        print(f'ID:{house.id} Region:{house.region} ({float(house.latitude):.6f}, {float(house.longitude):.6f})')

    # 检查北京市中心附近
    from location_utils import get_nearby_bounds
    bounds = get_nearby_bounds(39.915, 116.404, 5)
    print(f'\nSearch bounds for (39.915, 116.404) radius 5km:')
    print(f'  Lat: {bounds["min_lat"]:.6f} - {bounds["max_lat"]:.6f}')
    print(f'  Lon: {bounds["min_lon"]:.6f} - {bounds["max_lon"]:.6f}')

    # 测试查询
    test_houses = HouseInfo.query.filter(
        HouseInfo.latitude.between(bounds['min_lat'], bounds['max_lat']),
        HouseInfo.longitude.between(bounds['min_lon'], bounds['max_lon']),
        HouseInfo.latitude.isnot(None),
        HouseInfo.longitude.isnot(None)
    ).limit(10).all()

    print(f'\nHouses in bounds: {len(test_houses)}')
    for house in test_houses:
        print(f'  ID:{house.id} ({float(house.latitude):.6f}, {float(house.longitude):.6f})')
