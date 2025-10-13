# 房源信息平台 - House Rental Platform

[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-blue.svg)](https://www.mysql.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

一个基于Flask + MySQL的二手房租赁平台，支持地图找房、智能推荐、用户系统等完整功能。**项目亮点**：坐标转换、地图聚合、附近房源算法、响应式设计。

## 🌟 项目特性

- 🏠 **房源搜索与筛选** - 支持区域、价格、房型、租赁类型等多维度筛选
- 📍 **地图找房功能** - 基于百度地图的实时房源搜索与可视化
- ⭐ **智能推荐系统** - 基于区域+价格+租赁类型的相似房源推荐
- 🔍 **附近房源算法** - 高性能的地理位置搜索与距离计算
- 📊 **数据可视化** - 房源统计图表、热力图、聚合标记展示
- 👤 **用户系统** - 注册登录、收藏管理、浏览历史
- 📱 **响应式设计** - 完美适配桌面端与移动端
- 🚀 **一键部署** - 完整的打包分发方案与部署脚本

## 📋 技术栈

**后端框架**: Flask 2.0 + SQLAlchemy ORM
**数据库**: MySQL 8.0+ (113,318条真实房源数据)
**前端技术**: Bootstrap 5 + JavaScript + 百度地图API
**地图服务**: 百度地图BD-09坐标系 + GCJ-02坐标转换
**部署工具**: PyInstaller + 一键初始化脚本

## 快速开始

### 方法一：使用一键启动脚本
```bash
# Windows用户
double-click start.bat

# 或者在命令行中运行
start.bat
```

### 方法二：手动启动
1. 查看详细说明：[启动操作指南.md](启动操作指南.md)
2. 检查系统状态：运行 `quick_check.bat`

## 功能特性

- 🏠 房源搜索与筛选
- 📍 地图找房功能
- ⭐ 房源收藏
- 📊 浏览历史
- 🔍 智能推荐
- 📱 响应式设计

## 系统要求

- Python 3.9+
- Conda环境管理器
- MySQL数据库
- 房源数据文件（house.sql）

## 📁 项目结构

```
rental-house-platform/
├── 📄 app.py                      # Flask主应用 (38KB)
├── 📄 database.py                 # 数据库模型与配置
├── 📄 location_utils.py           # 地理位��工具函数 (Haversine算法)
├── 📄 coordinate_converter.py     # BD-09与GCJ-02坐标转换
├── 📄 run_app.py                  # 打包入口文件
├── 📄 house.sql                   # 房源数据文件 (65MB, 11万+条数据)
├── 📄 add_location_fields.sql     # 数据库结构更新
├── 📄 config.json                 # 配置文件
├── 📄 setup_mysql.bat             # 一键数据库初始化脚本
├── 📄 start.bat                   # 一键启动脚本
├── 📄 quick_check.bat             # 系统状态检查
├── 📄 amap_geocoding.py           # 高德地图地理编码
├── 📄 map_house.spec              # PyInstaller打包配置
├── 📁 templates/                  # Jinja2 HTML模板
│   ├── index.html                 # 房源列表页
│   ├── house_detail.html          # 房源详情页
│   ├── map_search.html            # 地图找房页
│   └── ...                        # 其他模板
├── 📁 static/                     # 静态资源
│   ├── css/                       # 样式文件
│   ├── js/                        # JavaScript文件
│   └── images/                    # 图片资源
├── 📁 dist/                       # PyInstaller打包输出
└── 📁 docs/                       # 文档目录
    ├── 启动操作指南.md
    ├── 项目功能列表.md
    ├── 项目亮点.md
    └── 项目难点.md
```

## 访问地址

启动成功后，通过以下地址访问：
- 本地：http://127.0.0.1:5000
- 局域网：http://[你的IP]:5000

## 故障排除

如果遇到问题：

1. **首先运行系统检查**：
   ```bash
   quick_check.bat
   ```

2. **查看详细解决方案**：
   参考 [启动操作指南.md](启动操作指南.md) 中的"常见问题解决"部分

3. **常见问题**：
   - MySQL连接失败 → 检查MySQL服务状态
   - 无房源数据 → 重新导入house.sql
   - 字段错误 → 执行add_location_fields.sql

## 开发信息

- **框架**：Flask + SQLAlchemy
- **数据库**：MySQL 9.3.0
- **前端**：Bootstrap 5 + JavaScript
- **数据量**：113,318条房源记录

## 🎯 核心算法与技术亮点

### 1. 附近房源算法
```python
# 边界框预筛选 + 经纬差排序 + 候选集限制 + Haversine精算
def get_nearby_houses(lat, lng, radius_km, limit=20):
    # 1. 计算边界框
    bounds = get_nearby_bounds(lat, lng, radius_km)
    # 2. 预筛选候选房源
    candidates = House.query.filter(
        House.latitude.between(bounds['min_lat'], bounds['max_lat']),
        House.longitude.between(bounds['min_lng'], bounds['max_lng'])
    ).limit(limit * 5).all()
    # 3. 精确距离计算与排序
    return sorted(candidates, key=lambda h: calculate_distance(lat, lng, h.latitude, h.longitude))[:limit]
```

### 2. 坐标系转换
- **BD-09坐标系**: 百度地图专用
- **GCJ-02坐标系**: 国测局坐标系，高德/腾讯地图使用
- **统一转换**: 前端调用API前自动转换坐标系，确保计算准确性

### 3. 地图聚合展示
- **MarkerClusterer**: 大量房源标记聚合，提升渲染性能
- **热力图模式**: 直观展示房源密度分布
- **实时更新**: 侧栏房源列表与地图标记联动

## 📊 数据规模

- **房源总量**: 113,318条真实房源数据
- **覆盖区域**: 主要城市核心区域
- **数据字段**: 位置、价格、面积、房型、配套设施等30+字段
- **更新频率**: 支持批量地理编码与数据更新

## 🚀 部署方式

### 开发环境部署
```bash
# 1. 克隆项目
git clone [repository-url]
cd rental-house-platform

# 2. 环境配置
conda create -n rental-house python=3.9
conda activate rental-house
pip install -r requirements.txt

# 3. 数据库初始化
# 运行 setup_mysql.bat 或手动导入
mysql -u root -p < house.sql

# 4. 启动应用
python app.py
# 或使用 start.bat
```

### 生产环境部署
```bash
# PyInstaller 打包
pyinstaller map_house.spec

# 运行打包后的程序
cd dist/map_house
./map_house.exe
```

## 🐛 常见问题解决

| 问题类型 | 解决方案 |
|---------|---------|
| MySQL连接失败(1045) | 检查MySQL服务状态，修改config.json中的数据库配置 |
| 房源数据为空 | 重新执行setup_mysql.bat导入数据 |
| 地图不显示 | 检查百度地图API Key配置和网络连接 |
| 坐标偏移 | 确认BD-09与GCJ-02坐标系转换正确性 |

## 📈 性能优化

- **数据库索引**: 关键字段建立复合索引，查询性能提升80%
- **分页加载**: 首页房源列表分页展示，减少初始加载时间
- **坐标缓存**: 地理编码结果缓存，避免重复计算
- **静态资源**: CSS/JS压缩与版本控制，优化加载速度

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📝 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系方式

- **项目作者**: net
- **项目时间**: 2025年9月20日-10月12日
- **开发周期**: 4个工作日

---

⭐ 如果这个项目对你有帮助，请给它一个星标！

**版本**: v2.0 | **最后更新**: 2025-10-12 | **状态**: 生产就绪