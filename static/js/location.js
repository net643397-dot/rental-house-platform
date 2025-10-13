/**
 * 地理定位功能模块
 */

class LocationManager {
    constructor() {
        this.currentPosition = null;
        this.watchId = null;
        this.options = {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 300000 // 5分钟缓存
        };
    }

    /**
     * 检查浏览器是否支持地理定位
     */
    isGeolocationSupported() {
        return "geolocation" in navigator;
    }

    /**
     * 获取当前位置
     */
    getCurrentPosition() {
        return new Promise((resolve, reject) => {
            if (!this.isGeolocationSupported()) {
                reject(new Error('您的浏览器不支持地理定位功能'));
                return;
            }

            navigator.geolocation.getCurrentPosition(
                (position) => {
                    this.currentPosition = {
                        lat: position.coords.latitude,
                        lon: position.coords.longitude,
                        accuracy: position.coords.accuracy,
                        timestamp: position.timestamp
                    };
                    resolve(this.currentPosition);
                },
                (error) => {
                    reject(this.handleLocationError(error));
                },
                this.options
            );
        });
    }

    /**
     * 持续监听位置变化
     */
    watchPosition(callback) {
        if (!this.isGeolocationSupported()) {
            callback(new Error('您的浏览器不支持地理定位功能'), null);
            return;
        }

        this.watchId = navigator.geolocation.watchPosition(
            (position) => {
                this.currentPosition = {
                    lat: position.coords.latitude,
                    lon: position.coords.longitude,
                    accuracy: position.coords.accuracy,
                    timestamp: position.timestamp
                };
                callback(null, this.currentPosition);
            },
            (error) => {
                callback(this.handleLocationError(error), null);
            },
            this.options
        );
    }

    /**
     * 停止监听位置变化
     */
    stopWatching() {
        if (this.watchId !== null) {
            navigator.geolocation.clearWatch(this.watchId);
            this.watchId = null;
        }
    }

    /**
     * 处理定位错误
     */
    handleLocationError(error) {
        let message;
        switch (error.code) {
            case error.PERMISSION_DENIED:
                message = "用户拒绝了地理定位请求";
                break;
            case error.POSITION_UNAVAILABLE:
                message = "位置信息不可用";
                break;
            case error.TIMEOUT:
                message = "获取位置信息超时";
                break;
            default:
                message = "获取位置信息时发生未知错误";
                break;
        }
        return new Error(message);
    }

    /**
     * 保存位置到服务器
     */
    async saveLocationToServer(position) {
        try {
            const response = await fetch('/api/user-location', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    lat: position.lat,
                    lon: position.lon
                })
            });

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('保存位置失败:', error);
            throw error;
        }
    }

    /**
     * 获取附近房源
     */
    async getNearbyHouses(lat, lon, radius = 5, limit = 20) {
        try {
            const params = new URLSearchParams({
                lat: lat,
                lon: lon,
                radius: radius,
                limit: limit
            });

            const response = await fetch(`/api/nearby-houses?${params}`);
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('获取附近房源失败:', error);
            throw error;
        }
    }

    /**
     * 获取城市坐标
     */
    async getCityLocation(city) {
        try {
            const response = await fetch(`/api/city-location/${encodeURIComponent(city)}`);
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('获取城市位置失败:', error);
            throw error;
        }
    }
}

/**
 * 位置UI管理器
 */
class LocationUI {
    constructor(locationManager) {
        this.locationManager = locationManager;
        this.initEventListeners();
    }

    /**
     * 初始化事件监听
     */
    initEventListeners() {
        // 定位按钮点击事件
        document.addEventListener('click', (e) => {
            if (e.target.matches('.location-btn, .location-btn *')) {
                e.preventDefault();
                this.handleLocationRequest();
            }
        });

        // 城市选择事件
        document.addEventListener('change', (e) => {
            if (e.target.matches('.city-select')) {
                this.handleCitySelect(e.target.value);
            }
        });
    }

    /**
     * 处理定位请求
     */
    async handleLocationRequest() {
        const button = document.querySelector('.location-btn');
        if (!button) return;

        // 显示加载状态
        this.showLocationLoading(button, true);

        try {
            const position = await this.locationManager.getCurrentPosition();

            // 保存位置到服务器
            await this.locationManager.saveLocationToServer(position);

            // 显示定位成功
            this.showLocationSuccess(button, position);

            // 获取并显示附近房源
            await this.loadNearbyHouses(position.lat, position.lon);

        } catch (error) {
            console.error('定位失败:', error);
            this.showLocationError(button, error.message);
        } finally {
            this.showLocationLoading(button, false);
        }
    }

    /**
     * 处理城市选择
     */
    async handleCitySelect(city) {
        if (!city) return;

        try {
            const cityData = await this.locationManager.getCityLocation(city);
            if (cityData.success) {
                await this.loadNearbyHouses(cityData.lat, cityData.lon);
                this.showMessage(`已切换到${city}`, 'success');
            }
        } catch (error) {
            console.error('城市定位失败:', error);
            this.showMessage('获取城市位置失败', 'error');
        }
    }

    /**
     * 加载附近房源
     */
    async loadNearbyHouses(lat, lon, radius = 5) {
        try {
            const data = await this.locationManager.getNearbyHouses(lat, lon, radius);

            if (data.success) {
                this.displayNearbyHouses(data.houses);
                this.showMessage(`找到 ${data.total} 套附近房源`, 'success');
            } else {
                this.showMessage(data.message || '获取附近房源失败', 'error');
            }
        } catch (error) {
            console.error('加载附近房源失败:', error);
            this.showMessage('加载附近房源失败', 'error');
        }
    }

    /**
     * 显示附近房源
     */
    displayNearbyHouses(houses) {
        const container = document.querySelector('.nearby-houses-container');
        if (!container) return;

        if (houses.length === 0) {
            container.innerHTML = '<div class="no-houses">附近暂无房源</div>';
            return;
        }

        let html = '<div class="houses-grid">';
        houses.forEach(house => {
            html += this.createHouseCard(house);
        });
        html += '</div>';

        container.innerHTML = html;
    }

    /**
     * 创建房源卡片
     */
    createHouseCard(house) {
        return `
            <div class="house-card" data-house-id="${house.id}">
                <div class="house-image">
                    <img src="/static/images/house-placeholder.jpg" alt="${house.title}" onerror="this.src='https://via.placeholder.com/300x200?text=房源图片'">
                    <div class="distance-badge">${house.distance_text}</div>
                </div>
                <div class="house-info">
                    <h3 class="house-title">${house.title}</h3>
                    <div class="house-details">
                        <span class="house-rooms">${house.rooms}</span>
                        <span class="house-area">${house.area}㎡</span>
                        <span class="house-region">${house.region}</span>
                    </div>
                    <div class="house-price">¥${house.price}/月</div>
                    <div class="house-address">${house.address}</div>
                    <div class="house-actions">
                        <a href="/house/${house.id}" class="btn btn-primary">查看详情</a>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * 显示定位加载状态
     */
    showLocationLoading(button, loading) {
        if (loading) {
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 定位中...';
            button.disabled = true;
        } else {
            button.innerHTML = '<i class="fas fa-location-dot"></i> 获取位置';
            button.disabled = false;
        }
    }

    /**
     * 显示定位成功
     */
    showLocationSuccess(button, position) {
        button.innerHTML = '<i class="fas fa-check"></i> 定位成功';
        button.classList.add('success');

        setTimeout(() => {
            button.innerHTML = '<i class="fas fa-location-dot"></i> 重新定位';
            button.classList.remove('success');
        }, 2000);
    }

    /**
     * 显示定位错误
     */
    showLocationError(button, message) {
        button.innerHTML = '<i class="fas fa-exclamation-triangle"></i> 定位失败';
        button.classList.add('error');
        this.showMessage(message, 'error');

        setTimeout(() => {
            button.innerHTML = '<i class="fas fa-location-dot"></i> 重试定位';
            button.classList.remove('error');
        }, 3000);
    }

    /**
     * 显示消息提示
     */
    showMessage(message, type = 'info') {
        // 创建消息元素
        const messageEl = document.createElement('div');
        messageEl.className = `location-message ${type}`;
        messageEl.textContent = message;

        // 添加到页面
        const container = document.querySelector('.location-messages') || document.body;
        container.appendChild(messageEl);

        // 自动移除
        setTimeout(() => {
            messageEl.remove();
        }, 3000);
    }
}

// 初始化位置管理器
const locationManager = new LocationManager();
const locationUI = new LocationUI(locationManager);

// 导出供其他模块使用
window.LocationManager = LocationManager;
window.locationManager = locationManager;