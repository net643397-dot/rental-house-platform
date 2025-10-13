/**
 * 地图搜索管理器
 */
class MapSearchManager {
    constructor() {
        this.map = null;
        this.markers = [];
        this.currentPosition = null; // GCJ-02 坐标，用于向后端查询
        this.currentPositionBd = null; // BD-09 坐标，用于地图展示
        this.selectedHouse = null;
        this.searchService = null;
        this.geocoder = null;
        this.heatmap = null;
        this.isHeatmapVisible = false;
        this.searchRadiusCircle = null;
        this.markerCluster = null;

        // 北京市中心坐标
        this.beijingCenter = new BMap.Point(116.404, 39.915);

        // 绑定方法上下文
        this.onMapClick = this.onMapClick.bind(this);
        this.onMarkerClick = this.onMarkerClick.bind(this);
    }

    /**
     * GCJ-02坐标转BD-09坐标（高德转百度）
     */
    gcj02ToBd09(lng, lat) {
        const X_PI = Math.PI * 3000.0 / 180.0;
        const z = Math.sqrt(lng * lng + lat * lat) + 0.00002 * Math.sin(lat * X_PI);
        const theta = Math.atan2(lat, lng) + 0.000003 * Math.cos(lng * X_PI);
        const bd_lng = z * Math.cos(theta) + 0.0065;
        const bd_lat = z * Math.sin(theta) + 0.006;
        return { lng: bd_lng, lat: bd_lat };
    }

    /**
     * BD-09坐标转GCJ-02坐标（百度转高德）
     */
    bd09ToGcj02(bd_lng, bd_lat) {
        const X_PI = Math.PI * 3000.0 / 180.0;
        const x = bd_lng - 0.0065;
        const y = bd_lat - 0.006;
        const z = Math.sqrt(x * x + y * y) - 0.00002 * Math.sin(y * X_PI);
        const theta = Math.atan2(y, x) - 0.000003 * Math.cos(x * X_PI);
        const lng = z * Math.cos(theta);
        const lat = z * Math.sin(theta);
        return { lng: lng, lat: lat };
    }

    /**
     */
    wgs84ToGcj02(lng, lat) {
        if (this.outOfChina(lng, lat)) {
            return { lng, lat };
        }
        const a = 6378245.0;
        const ee = 0.00669342162296594323;
        let dLat = this.transformLat(lng - 105.0, lat - 35.0);
        let dLng = this.transformLng(lng - 105.0, lat - 35.0);
        const radLat = lat / 180.0 * Math.PI;
        let magic = Math.sin(radLat);
        magic = 1 - ee * magic * magic;
        const sqrtMagic = Math.sqrt(magic);
        dLat = (dLat * 180.0) / ((a * (1 - ee)) / (magic * sqrtMagic) * Math.PI);
        dLng = (dLng * 180.0) / ((a / sqrtMagic) * Math.cos(radLat) * Math.PI);
        const mgLat = lat + dLat;
        const mgLng = lng + dLng;
        return { lng: mgLng, lat: mgLat };
    }

    outOfChina(lng, lat) {
        return lng < 72.004 || lng > 137.8347 || lat < 0.8293 || lat > 55.8271;
    }

    transformLat(lng, lat) {
        let ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + 0.1 * lng * lat + 0.2 * Math.sqrt(Math.abs(lng));
        ret += (20.0 * Math.sin(6.0 * lng * Math.PI) + 20.0 * Math.sin(2.0 * lng * Math.PI)) * 2.0 / 3.0;
        ret += (20.0 * Math.sin(lat * Math.PI) + 40.0 * Math.sin(lat / 3.0 * Math.PI)) * 2.0 / 3.0;
        ret += (160.0 * Math.sin(lat / 12.0 * Math.PI) + 320 * Math.sin(lat * Math.PI / 30.0)) * 2.0 / 3.0;
        return ret;
    }

    transformLng(lng, lat) {
        let ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + 0.1 * lng * lat + 0.1 * Math.sqrt(Math.abs(lng));
        ret += (20.0 * Math.sin(6.0 * lng * Math.PI) + 20.0 * Math.sin(2.0 * lng * Math.PI)) * 2.0 / 3.0;
        ret += (20.0 * Math.sin(lng * Math.PI) + 40.0 * Math.sin(lng / 3.0 * Math.PI)) * 2.0 / 3.0;
        ret += (150.0 * Math.sin(lng / 12.0 * Math.PI) + 300.0 * Math.sin(lng / 30.0 * Math.PI)) * 2.0 / 3.0;
        return ret;
    }

    /**
     * 初始化地图
     */
    init() {
        try {
            // 创建地图实例
            this.map = new BMap.Map("baiduMap");

            // 设置地图中心点和缩放级别
            this.map.centerAndZoom(this.beijingCenter, 11);

            // 启用滚轮缩放
            this.map.enableScrollWheelZoom(true);

            // 添加地图控件
            this.addMapControls();

            // 初始化服务
            this.searchService = new BMap.LocalSearch(this.map, {
                renderOptions: { map: this.map, autoViewport: false }
            });
            this.geocoder = new BMap.Geocoder();

            // 绑定事件
            this.bindEvents();

            // 隐藏加载状态
            document.getElementById('mapLoading').style.display = 'none';

            // 设置全局实例
            window.mapSearchInstance = this;

            // 初始化距离范围筛选器（默认5公里已选中，启用次级筛选）
            const distanceValue = document.getElementById('mapDistanceRange').value;
            if (distanceValue) {
                const secondaryFilters = document.querySelectorAll('.secondary-filter');
                secondaryFilters.forEach(filter => {
                    filter.disabled = false;
                });
            }

            console.log('地图初始化成功');

        } catch (error) {
            console.error('地图初始化失败:', error);
            this.showError('地图初始化失败，请刷新页面重试');
        }
    }

    /**
     * 添加地图控件
     */
    addMapControls() {
        // 添加缩放控件
        this.map.addControl(new BMap.NavigationControl({
            anchor: BMAP_ANCHOR_BOTTOM_RIGHT,
            type: BMAP_NAVIGATION_CONTROL_SMALL
        }));

        // 添加比例尺控件
        this.map.addControl(new BMap.ScaleControl({
            anchor: BMAP_ANCHOR_BOTTOM_LEFT
        }));
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        // 地图点击事件
        this.map.addEventListener('click', this.onMapClick);

        // 搜索按钮事件
        document.getElementById('mapSearchBtn').addEventListener('click', () => {
            const query = document.getElementById('mapSearchInput').value.trim();
            if (query) {
                this.searchLocation(query);
            }
        });

        // 回车搜索
        document.getElementById('mapSearchInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const query = e.target.value.trim();
                if (query) {
                    this.searchLocation(query);
                }
            }
        });

        // 我的位置按钮
        document.getElementById('showMyLocation').addEventListener('click', () => {
            this.getCurrentLocation();
        });

        // 清除标记按钮
        document.getElementById('clearMarkers').addEventListener('click', () => {
            this.clearAllMarkers();
        });

        // 热力图切换
        document.getElementById('toggleHeatmap').addEventListener('click', () => {
            this.toggleHeatmap();
        });

        // 地图工具栏按钮

        document.getElementById('fullscreenBtn').addEventListener('click', () => {
            this.toggleFullscreen();
        });

        document.getElementById('centerMapBtn').addEventListener('click', () => {
            this.map.centerAndZoom(this.beijingCenter, 11);
            this.updateLocationText('北京市中心');
        });

        // 距离范围筛选变化（主筛选项）
        document.getElementById('mapDistanceRange').addEventListener('change', () => {
            const distanceValue = document.getElementById('mapDistanceRange').value;
            const secondaryFilters = document.querySelectorAll('.secondary-filter');

            if (distanceValue) {
                // 启用次级筛选项
                secondaryFilters.forEach(filter => {
                    filter.disabled = false;
                });

                // 如果有当前位置，重新搜索房源
                if (this.currentPosition) {
                    this.searchNearbyHouses(this.currentPosition.lat, this.currentPosition.lng);
                }
            } else {
                // 禁用次级筛选项并重置值
                secondaryFilters.forEach(filter => {
                    filter.disabled = true;
                    filter.value = '';
                });

                this.clearRadiusCircle();
                // 清空房源列表
                this.clearHouseList();
            }
        });

        // 次级筛选条件变化
        ['mapRentType', 'mapPriceRange', 'mapRoomType'].forEach(id => {
            document.getElementById(id).addEventListener('change', () => {
                const distanceValue = document.getElementById('mapDistanceRange').value;
                if (this.currentPosition && distanceValue) {
                    this.searchNearbyHouses(this.currentPosition.lat, this.currentPosition.lng);
                }
            });
        });

        // 排序变化
        document.getElementById('sortOrder').addEventListener('change', () => {
            this.sortHouseList();
        });

        // 弹窗关闭
        document.querySelector('.modal-close').addEventListener('click', () => {
            this.closeModal();
        });

        // 点击弹窗外部关闭
        document.getElementById('houseModal').addEventListener('click', (e) => {
            if (e.target.id === 'houseModal') {
                this.closeModal();
            }
        });
    }

    /**
     * 地图点击事件处理
     */
    onMapClick(e) {
        const point = e.point;
        this.setCurrentPosition(point.lng, point.lat);

        // 反向地理编码获取地址
        this.geocoder.getLocation(point, (result) => {
            if (result) {
                this.updateLocationText(result.address);
            }
        });

        if (this.currentPosition) {
            console.log(`地图点击 - 百度坐标: (${point.lng}, ${point.lat})`);
            console.log(`使用当前位置 (GCJ-02): (${this.currentPosition.lng}, ${this.currentPosition.lat})`);
            // 使用转换后的坐标搜索附近房源
            this.searchNearbyHouses(this.currentPosition.lat, this.currentPosition.lng);
        }
    }

    /**
     * 搜索位置
     */
    searchLocation(query) {
        console.log('搜索位置:', query);

        this.searchService.search(query);

        // 使用地理编码获取精确坐标
        this.geocoder.getPoint(query, (point) => {
            if (point) {
                this.map.centerAndZoom(point, 14);
                this.setCurrentPosition(point.lng, point.lat);
                this.updateLocationText(query);
                if (this.currentPosition) {
                    this.searchNearbyHouses(this.currentPosition.lat, this.currentPosition.lng);
                }
            } else {
                this.showMessage('未找到该地点，请尝试其他关键词', 'error');
            }
        });
    }

    /**
     * 设置当前位置
     */
    setCurrentPosition(lng, lat) {
        this.currentPositionBd = { lng, lat };
        const gcjCoord = this.bd09ToGcj02(lng, lat);
        this.currentPosition = { lng: gcjCoord.lng, lat: gcjCoord.lat };

        console.log(`Set current position (BD-09): (${lng}, ${lat})`);
        console.log(`Converted to GCJ-02: (${this.currentPosition.lng}, ${this.currentPosition.lat})`);

        // 清除之前的位置标记
        this.clearLocationMarker();

        // 添加新的位置标记
        const point = new BMap.Point(lng, lat);
        const marker = new BMap.Marker(point);

        // 使用自定义定位图标，和房源标记区分开
        const locationIcon = new BMap.Icon(
            '/static/images/location-marker.svg',
            new BMap.Size(40, 40),
            {
                anchor: new BMap.Size(20, 38),
                imageSize: new BMap.Size(40, 40)
            }
        );
        marker.setIcon(locationIcon);

        // 添加标签
        const label = new BMap.Label('📍 搜索中心', {
            offset: new BMap.Size(-28, -50)
        });
        label.setStyle({
            backgroundColor: '#2c3e50',
            color: 'white',
            border: '2px solid white',
            borderRadius: '6px',
            padding: '4px 8px',
            fontSize: '13px',
            fontWeight: 'bold',
            boxShadow: '0 2px 6px rgba(0,0,0,0.3)'
        });
        marker.setLabel(label);

        this.map.addOverlay(marker);
        this.locationMarker = marker;

        // 添加信息窗口
        const infoWindowContent = `
            <div style="padding: 10px; color: #333; text-align: center;">
                <div style="font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 5px;">
                    📍 当前搜索位置
                </div>
                <div style="font-size: 12px; color: #666;">
                    坐标: ${lat.toFixed(6)}, ${lng.toFixed(6)}
                </div>
            </div>
        `;
        const infoWindow = new BMap.InfoWindow(infoWindowContent, {
            width: 220,
            height: 80
        });
        marker.addEventListener('click', () => {
            this.map.openInfoWindow(infoWindow, point);
        });
    }

    /**
     * 获取当前地理位置
     */
    getCurrentLocation() {
        if (navigator.geolocation) {
            const btn = document.getElementById('showMyLocation');
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 定位中...';
            btn.disabled = true;

            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const wgsLat = position.coords.latitude;
                    const wgsLng = position.coords.longitude;

                    // Convert WGS84 (GPS) -> GCJ-02 -> BD-09 for display
                    const gcjCoord = this.wgs84ToGcj02(wgsLng, wgsLat);
                    const bdCoord = this.gcj02ToBd09(gcjCoord.lng, gcjCoord.lat);
                    const bdPoint = new BMap.Point(bdCoord.lng, bdCoord.lat);

                    this.map.centerAndZoom(bdPoint, 15);
                    this.setCurrentPosition(bdCoord.lng, bdCoord.lat);
                    this.updateLocationText('当前位置');
                    if (this.currentPosition) {
                        this.searchNearbyHouses(this.currentPosition.lat, this.currentPosition.lng);
                    }

                    btn.innerHTML = '<i class="fas fa-crosshairs"></i> 我的位置';
                    btn.disabled = false;
                },
                (error) => {
                    console.error('定位失败:', error);
                    this.showMessage('定位失败，请检查浏览器权限设置', 'error');
                    btn.innerHTML = '<i class="fas fa-crosshairs"></i> 我的位置';
                    btn.disabled = false;
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 300000
                }
            );
        } else {
            this.showMessage('您的浏览器不支持地理定位', 'error');
        }
    }

    /**
     * 搜索附近房源
     */
    async searchNearbyHouses(lat, lng, radius = 5) {
        try {
            console.log(`Searching houses near (${lat}, ${lng}) ...`);

            const filters = this.getFilters();
            if (!filters) {
                console.log('Distance range not selected, skip search.');
                this.clearRadiusCircle();
                this.displayHouses([]);
                this.updateHouseCount(0);
                return;
            }

            const searchRadius = filters.max_distance || radius;
            this.updateSearchRadiusCircle(lat, lng, searchRadius);

            const requestFilters = { ...filters };
            delete requestFilters.max_distance;

            const params = new URLSearchParams({
                lat,
                lon: lng,
                radius: searchRadius,
                limit: 50,
                ...requestFilters
            });

            console.log('Nearby houses params:', params.toString());

            const response = await fetch(`/api/nearby-houses?${params}`);
            const data = await response.json();

            console.log('Nearby houses response:', data);

            if (data.success) {
                this.displayHouses(data.houses);
                this.addHouseMarkers(data.houses);
                this.updateHouseCount(data.total);

                if (data.houses.length > 0) {
                    this.showMessage(`找到 ${data.total} 套附近房源`, 'success');
                } else {
                    this.showMessage('该位置附近暂无房源', 'info');
                }
            } else {
                console.error('Nearby houses API failed:', data.message);
                this.showMessage(data.message || '获取房源失败', 'error');
                this.clearRadiusCircle();
                this.displayHouses([]);
                this.updateHouseCount(0);
            }
        } catch (error) {
            console.error('搜索房源失败:', error);
            this.showMessage('搜索房源失败，请稍后重试', 'error');
            this.clearRadiusCircle();
            this.displayHouses([]);
            this.updateHouseCount(0);
        }
    }

    /**
     * 获取筛选条件
     */
    getFilters() {
        const filters = {};

        // 距离范围筛选（必选项）
        const distanceRange = document.getElementById('mapDistanceRange').value;
        if (distanceRange) {
            filters.max_distance = parseFloat(distanceRange);
        } else {
            // 如果没有选择距离范围，返回空对象，不进行搜索
            return null;
        }

        const rentType = document.getElementById('mapRentType').value;
        if (rentType) filters.rent_type = rentType;

        const priceRange = document.getElementById('mapPriceRange').value;
        if (priceRange) {
            const [min, max] = priceRange.split('-');
            filters.min_price = parseInt(min);
            filters.max_price = parseInt(max);
        }

        const roomType = document.getElementById('mapRoomType').value;
        if (roomType) filters.rooms = roomType;

        return filters;
    }

    /**
     * 添加房源标记
     */
    addHouseMarkers(houses) {
        // 清除之前的房源标记
        this.clearHouseMarkers();

        const markers = [];

        houses.forEach(house => {
            const lat = parseFloat(house.latitude);
            const lng = parseFloat(house.longitude);
            if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
                return;
            }

            const bdCoord = this.gcj02ToBd09(lng, lat);
            house.bd_lat = bdCoord.lat;
            house.bd_lng = bdCoord.lng;
            const point = new BMap.Point(bdCoord.lng, bdCoord.lat);
            const marker = new BMap.Marker(point);

            const label = new BMap.Label(`🏠 ¥${house.price}`, {
                offset: new BMap.Size(10, -10)
            });
            label.setStyle({
                backgroundColor: '#ff4757',
                color: 'white',
                border: '2px solid white',
                borderRadius: '6px',
                padding: '4px 8px',
                fontSize: '13px',
                fontWeight: 'bold',
                boxShadow: '0 2px 6px rgba(0,0,0,0.3)',
                cursor: 'pointer'
            });
            marker.setLabel(label);

            marker.houseData = {
                ...house,
                bd_lat: bdCoord.lat,
                bd_lng: bdCoord.lng
            };
            marker.addEventListener('click', () => this.onMarkerClick(marker));

            markers.push(marker);
        });

        if (markers.length === 0) {
            this.markers = [];
            this.updateHeatmapData([]);
            return;
        }

        const canCluster = typeof BMapLib !== 'undefined' && typeof BMapLib.MarkerClusterer === 'function';
        if (canCluster) {
            this.markerCluster = new BMapLib.MarkerClusterer(this.map, {
                markers,
                gridSize: 60,
                maxZoom: 16
            });
        } else {
            markers.forEach(marker => this.map.addOverlay(marker));
        }

        this.markers = markers;

        console.log(`Added ${markers.length} house markers to the map`);

        // 更新热力图数据
        this.updateHeatmapData(houses);
    }

    /**
     * 标记点击事件
     */
    onMarkerClick(marker) {
        const house = marker.houseData;
        this.selectedHouse = house;

        // 高亮对应的房源列表项
        this.highlightHouseItem(house.id);

        // 显示详情弹窗
        this.showHouseModal(house);
    }

    /**
     * 显示房源列表
     */
    displayHouses(houses) {
        const container = document.getElementById('mapHouseList');

        if (houses.length === 0) {
            container.innerHTML = `
                <div class="no-houses">
                    <div class="no-houses-icon">
                        <i class="fas fa-search-location"></i>
                    </div>
                    <h4>未找到房源</h4>
                    <p>该位置附近暂无符合条件的房源<br>请尝试扩大搜索范围或调整筛选条件</p>
                </div>
            `;
            return;
        }

        let html = '';
        houses.forEach(house => {
            html += this.createHouseItem(house);
        });

        container.innerHTML = html;

        // 绑定点击事件
        container.querySelectorAll('.house-item').forEach(item => {
            item.addEventListener('click', () => {
                const houseId = parseInt(item.dataset.houseId);
                const house = houses.find(h => h.id === houseId);
                if (house) {
                    this.selectHouse(house);
                }
            });
        });

        // 应用排序
        this.sortHouseList();
    }

    /**
     * 创建房源列表项
     */
    createHouseItem(house) {
        return `
            <div class="house-item" data-house-id="${house.id}">
                <div class="house-title">${house.title}</div>
                <div class="house-meta">
                    <span>${house.rooms}</span>
                    <span>${house.area}㎡</span>
                    <span>${house.region}</span>
                </div>
                <div class="house-price">¥${house.price}/月</div>
                <div class="house-distance">
                    <i class="fas fa-map-marker-alt"></i>
                    距离 ${house.distance_text}
                </div>
            </div>
        `;
    }

    /**
     * 选择房源
     */
    selectHouse(house) {
        this.selectedHouse = house;

        // 地图中心移动到房源位置
        if (house.latitude && house.longitude) {
            const lat = parseFloat(house.latitude);
            const lng = parseFloat(house.longitude);
            if (Number.isFinite(lat) && Number.isFinite(lng)) {
                const bdCoord = house.bd_lat && house.bd_lng ? { lat: house.bd_lat, lng: house.bd_lng } : this.gcj02ToBd09(lng, lat);
                const point = new BMap.Point(bdCoord.lng, bdCoord.lat);
                this.map.centerAndZoom(point, 16);
            }
        }

        // 高亮标记
        this.highlightMarker(house.id);

        // 高亮列表项
        this.highlightHouseItem(house.id);

        // 显示详情
        this.showHouseModal(house);
    }

    /**
     * 高亮地图标记
     */
    highlightMarker(houseId) {
        this.markers.forEach(marker => {
            if (marker.houseData && marker.houseData.id === houseId) {
                // 高亮效果
                marker.setAnimation(BMAP_ANIMATION_BOUNCE);
                setTimeout(() => {
                    marker.setAnimation(null);
                }, 1500);
            }
        });
    }

    /**
     * 高亮房源列表项
     */
    highlightHouseItem(houseId) {
        document.querySelectorAll('.house-item').forEach(item => {
            item.classList.remove('active');
            if (parseInt(item.dataset.houseId) === houseId) {
                item.classList.add('active');
                item.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        });
    }

    /**
     * 显示房源详情弹窗
     */
    showHouseModal(house) {
        document.getElementById('modalTitle').textContent = house.title;

        const modalBody = document.getElementById('modalBody');
        modalBody.innerHTML = `
            <div class="house-detail">
                <div class="house-image">
                    <img src="/static/images/house-placeholder.jpg" alt="${house.title}" style="width: 100%; height: 200px; object-fit: cover; border-radius: 8px;">
                </div>
                <div class="house-info">
                    <div class="price-section">
                        <span class="price">¥${house.price}/月</span>
                        <span class="distance">${house.distance_text}</span>
                    </div>
                    <div class="basic-info">
                        <div class="info-row">
                            <span class="label">房型：</span>
                            <span class="value">${house.rooms}</span>
                        </div>
                        <div class="info-row">
                            <span class="label">面积：</span>
                            <span class="value">${house.area}㎡</span>
                        </div>
                        <div class="info-row">
                            <span class="label">朝向：</span>
                            <span class="value">${house.direction || '未知'}</span>
                        </div>
                        <div class="info-row">
                            <span class="label">类型：</span>
                            <span class="value">${house.rent_type}</span>
                        </div>
                        <div class="info-row">
                            <span class="label">位置：</span>
                            <span class="value">${house.region} ${house.block}</span>
                        </div>
                        <div class="info-row">
                            <span class="label">地址：</span>
                            <span class="value">${house.address}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 设置按钮事件
        document.getElementById('viewDetails').onclick = () => {
            window.open(`/house/${house.id}`, '_blank');
        };

        document.getElementById('addToFavorite').onclick = () => {
            this.addToFavorite(house.id);
        };

        document.getElementById('houseModal').style.display = 'flex';
    }

    /**
     * 关闭弹窗
     */
    closeModal() {
        document.getElementById('houseModal').style.display = 'none';
    }

    /**
     * 添加到收藏
     */
    async addToFavorite(houseId) {
        try {
            const response = await fetch('/api/favorites', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ house_id: houseId })
            });

            const data = await response.json();

            if (data.success) {
                this.showMessage('添加收藏成功', 'success');
            } else {
                this.showMessage(data.message || '添加收藏失败', 'error');
            }
        } catch (error) {
            console.error('添加收藏失败:', error);
            this.showMessage('添加收藏失败', 'error');
        }
    }

    /**
     * 房源列表排序
     */
    sortHouseList() {
        const container = document.getElementById('mapHouseList');
        const items = Array.from(container.querySelectorAll('.house-item'));
        const sortType = document.getElementById('sortOrder').value;

        items.sort((a, b) => {
            const houseA = this.getHouseFromElement(a);
            const houseB = this.getHouseFromElement(b);

            switch (sortType) {
                case 'distance':
                    return houseA.distance - houseB.distance;
                case 'price_asc':
                    return parseInt(houseA.price) - parseInt(houseB.price);
                case 'price_desc':
                    return parseInt(houseB.price) - parseInt(houseA.price);
                case 'area_desc':
                    return parseInt(houseB.area) - parseInt(houseA.area);
                default:
                    return 0;
            }
        });

        // 重新排列DOM元素
        items.forEach(item => container.appendChild(item));
    }

    /**
     * 从DOM元素获取房源数据
     */
    getHouseFromElement(element) {
        const price = element.querySelector('.house-price').textContent.replace(/[^\d]/g, '');
        const area = element.querySelector('.house-meta span:nth-child(2)').textContent.replace(/[^\d]/g, '');
        const distanceText = element.querySelector('.house-distance').textContent;
        const distance = parseFloat(distanceText.replace(/[^\d.]/g, ''));

        return {
            price: price,
            area: area,
            distance: distance
        };
    }

    /**
     * 切换热力图
     */
    toggleHeatmap() {
        const btn = document.getElementById('toggleHeatmap');

        if (this.isHeatmapVisible) {
            if (this.heatmap) {
                this.map.removeOverlay(this.heatmap);
            }
            btn.innerHTML = '<i class="fas fa-fire"></i> 热力图';
            this.isHeatmapVisible = false;
        } else {
            this.showHeatmap();
            btn.innerHTML = '<i class="fas fa-fire-flame-curved"></i> 关闭热力图';
            this.isHeatmapVisible = true;
        }
    }

    /**
     * 显示热力图
     */
    showHeatmap() {
        if (!this.heatmapData || this.heatmapData.length === 0) {
            this.showMessage('暂无热力图数据', 'info');
            return;
        }

        this.heatmap = new BMapLib.HeatmapOverlay({
            radius: 20,
            opacity: 0.6
        });

        this.map.addOverlay(this.heatmap);
        this.heatmap.setDataSet({ data: this.heatmapData, max: 10000 });
    }

    /**
     * 更新热力图数据
     */
    updateHeatmapData(houses) {
        this.heatmapData = houses
            .map(house => {
                const lat = parseFloat(house.latitude);
                const lng = parseFloat(house.longitude);
                if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
                    return null;
                }
                const bdCoord = this.gcj02ToBd09(lng, lat);
                const price = parseInt(house.price, 10);
                const weight = Number.isFinite(price) ? Math.max(1, price / 100) : 1;
                return {
                    lng: bdCoord.lng,
                    lat: bdCoord.lat,
                    count: weight
                };
            })
            .filter(Boolean);
    }


    /**
     * 切换全屏
     */
    toggleFullscreen() {
        const mapWrapper = document.querySelector('.map-wrapper');

        if (!document.fullscreenElement) {
            mapWrapper.requestFullscreen().then(() => {
                this.map.getViewport();
            });
        } else {
            document.exitFullscreen();
        }
    }

    /**
     * 清除房源列表
     */
    clearHouseList() {
        this.displayHouses([]);
        this.updateHouseCount(0);
        this.clearHouseMarkers();
    }

    /**
     * 清除所有标记
     */
    clearAllMarkers() {
        this.clearHouseMarkers();
        this.clearLocationMarker();
        this.clearRadiusCircle();
        this.displayHouses([]);
        this.updateHouseCount(0);
        this.updateLocationText('点击地图或搜索位置开始找房');
    }

    /**
     * 清除房源标记
     */
    clearHouseMarkers() {
        if (this.markerCluster) {
            this.markerCluster.clearMarkers();
            this.markerCluster = null;
        } else {
            this.markers.forEach(marker => {
                this.map.removeOverlay(marker);
            });
        }
        this.markers = [];
    }

    /**
     * 清除位置标记
     */
    clearLocationMarker() {
        if (this.locationMarker) {
            this.map.removeOverlay(this.locationMarker);
            this.locationMarker = null;
        }
    }

    /**
     * 更新/绘制搜索半径圆
     */
    updateSearchRadiusCircle(lat, lng, radiusKm) {
        if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
            return;
        }

        const bdCoord = this.gcj02ToBd09(lng, lat);
        const center = new BMap.Point(bdCoord.lng, bdCoord.lat);
        const radiusMeters = radiusKm * 1000;

        this.clearRadiusCircle();

        this.searchRadiusCircle = new BMap.Circle(center, radiusMeters, {
            strokeColor: '#1f78ff',
            strokeWeight: 2,
            strokeOpacity: 0.5,
            fillColor: '#1f78ff',
            fillOpacity: 0.12,
            enableClicking: false
        });

        this.map.addOverlay(this.searchRadiusCircle);
    }

    clearRadiusCircle() {
        if (this.searchRadiusCircle) {
            this.map.removeOverlay(this.searchRadiusCircle);
            this.searchRadiusCircle = null;
        }
    }

    /**
     * 更新位置文本
     */
    updateLocationText(text) {
        document.getElementById('currentLocationText').textContent = text;
    }

    /**
     * 更新房源数量
     */
    updateHouseCount(count) {
        document.getElementById('totalHouses').textContent = count;
    }

    /**
     * 显示消息
     */
    showMessage(message, type = 'info') {
        // 创建消息元素
        const messageEl = document.createElement('div');
        messageEl.className = `map-message ${type}`;
        messageEl.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        `;

        // 添加样式
        Object.assign(messageEl.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '12px 16px',
            borderRadius: '8px',
            color: 'white',
            fontSize: '14px',
            fontWeight: '500',
            zIndex: '2000',
            animation: 'slideInRight 0.3s ease',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            maxWidth: '300px',
            backgroundColor: type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#17a2b8'
        });

        document.body.appendChild(messageEl);

        // 自动移除
        setTimeout(() => {
            messageEl.remove();
        }, 3000);
    }

    /**
     * 显示错误
     */
    showError(message) {
        document.getElementById('mapLoading').innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>加载失败</h3>
                <p>${message}</p>
                <button onclick="location.reload()" class="btn btn-primary">重新加载</button>
            </div>
        `;
    }

    /**
     * 设置地图中心
     */
    setCenter(point, name) {
        this.map.centerAndZoom(point, 14);
        this.setCurrentPosition(point.lng, point.lat);
        this.updateLocationText(name);
        if (this.currentPosition) {
            this.searchNearbyHouses(this.currentPosition.lat, this.currentPosition.lng);
        }
    }
}

// CSS动画
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    .house-detail .price-section {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid #e9ecef;
    }

    .house-detail .price {
        font-size: 1.5rem;
        font-weight: 700;
        color: #dc3545;
    }

    .house-detail .distance {
        background: #28a745;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
    }

    .house-detail .info-row {
        display: flex;
        margin-bottom: 0.5rem;
    }

    .house-detail .label {
        min-width: 60px;
        color: #6c757d;
        font-weight: 500;
    }

    .house-detail .value {
        color: #343a40;
    }
`;
document.head.appendChild(style);

// 导出供全局使用
window.MapSearchManager = MapSearchManager;
