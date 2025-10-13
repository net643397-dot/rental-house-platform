from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from location_utils import calculate_distance, get_nearby_bounds, format_distance, CITY_COORDINATES
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# MySQL配置
MYSQL_HOST = '127.0.0.1'
MYSQL_PORT = 3306
MYSQL_USER = 'root'
MYSQL_PASSWORD = ''  # 无密码
MYSQL_DATABASE = 'house'

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 添加时间戳转换过滤器
@app.template_filter('timestamp_to_date')
def timestamp_to_date(timestamp):
    """将Unix时间戳转换为可读的日期格式"""
    try:
        if timestamp:
            # 转换时间戳为datetime对象
            dt = datetime.fromtimestamp(int(timestamp))
            now = datetime.now()

            # 计算时间差
            diff = now - dt
            days = diff.days

            if days == 0:
                return "今天发布"
            elif days == 1:
                return "昨天发布"
            elif days < 7:
                return f"{days}天前发布"
            elif days < 30:
                weeks = days // 7
                return f"{weeks}周前发布"
            elif days < 365:
                months = days // 30
                return f"{months}个月前发布"
            else:
                return dt.strftime('%Y年%m月%d日')
        return "未知时间"
    except (ValueError, TypeError):
        return "时间格式错误"

@app.template_filter('timestamp_to_full_date')
def timestamp_to_full_date(timestamp):
    """将Unix时间戳转换为完整日期格式"""
    try:
        if timestamp:
            dt = datetime.fromtimestamp(int(timestamp))
            return dt.strftime('%Y年%m月%d日 %H:%M')
        return "未知时间"
    except (ValueError, TypeError):
        return "时间格式错误"

# 根据现有数据库结构定义模型
class HouseInfo(db.Model):
    __tablename__ = 'house_info'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    rooms = db.Column(db.String(100))
    area = db.Column(db.String(100))
    price = db.Column(db.String(100))
    direction = db.Column(db.String(100))
    rent_type = db.Column(db.String(100))
    region = db.Column(db.String(100))
    block = db.Column(db.String(100))
    address = db.Column(db.String(200))
    traffic = db.Column(db.String(100))
    publish_time = db.Column(db.Integer)
    facilities = db.Column(db.Text)
    highlights = db.Column(db.Text)
    matching = db.Column(db.Text)
    travel = db.Column(db.Text)
    page_views = db.Column(db.Integer)
    landlord = db.Column(db.String(30))
    phone_num = db.Column(db.String(100))
    house_num = db.Column(db.String(100))
    latitude = db.Column(db.Numeric(10, 8))
    longitude = db.Column(db.Numeric(11, 8))

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'rooms': self.rooms,
            'area': self.area,
            'price': self.price,
            'direction': self.direction,
            'rent_type': self.rent_type,
            'region': self.region,
            'block': self.block,
            'address': self.address,
            'traffic': self.traffic,
            'facilities': self.facilities,
            'highlights': self.highlights,
            'matching': self.matching,
            'travel': self.travel,
            'page_views': self.page_views,
            'landlord': self.landlord,
            'phone_num': self.phone_num,
            'latitude': float(self.latitude) if self.latitude else None,
            'longitude': float(self.longitude) if self.longitude else None
        }

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Favorite(db.Model):
    __tablename__ = 'favorites'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)  # 现在使用真实用户ID
    house_id = db.Column(db.Integer, nullable=False)  # 移除外键约束，简化实现
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class BrowseHistory(db.Model):
    __tablename__ = 'browse_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True)  # 可为空，支持匿名浏览
    house_id = db.Column(db.Integer, nullable=False)  # 关联到房源ID
    ip_address = db.Column(db.String(50))  # 存储IP地址，用于匿名用户
    visit_time = db.Column(db.DateTime, default=datetime.utcnow)
    user_agent = db.Column(db.Text)  # 存储浏览器信息

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 20  # 每页显示20条记录

    # 获取搜索参数
    search = request.args.get('search', '')
    region = request.args.get('region', '')
    rent_type = request.args.get('rent_type', '')
    min_price = request.args.get('min_price', type=int)
    max_price = request.args.get('max_price', type=int)
    rooms = request.args.get('rooms', '')

    # 构建查询
    query = HouseInfo.query

    if search:
        query = query.filter(
            HouseInfo.title.like(f'%{search}%') |
            HouseInfo.address.like(f'%{search}%') |
            HouseInfo.block.like(f'%{search}%')
        )

    if region:
        query = query.filter(HouseInfo.region.like(f'%{region}%'))

    if rent_type:
        query = query.filter(HouseInfo.rent_type == rent_type)

    if rooms:
        query = query.filter(HouseInfo.rooms.like(f'%{rooms}%'))

    # 价格筛选（需要处理字符串价格）
    if min_price:
        query = query.filter(db.cast(HouseInfo.price, db.Integer) >= min_price)

    if max_price:
        query = query.filter(db.cast(HouseInfo.price, db.Integer) <= max_price)

    # 分页查询
    houses = query.order_by(HouseInfo.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    # 获取所有区域用于筛选
    regions = db.session.query(HouseInfo.region).distinct().limit(20).all()
    regions = [r[0] for r in regions if r[0]]

    return render_template('index.html',
                         houses=houses,
                         regions=regions,
                         search=search,
                         region=region,
                         rent_type=rent_type,
                         rooms=rooms)

@app.route('/house/<int:house_id>')
def house_detail(house_id):
    house = HouseInfo.query.get_or_404(house_id)

    # 增加浏览次数
    if house.page_views:
        house.page_views += 1
    else:
        house.page_views = 1

    # 记录浏览历史
    try:
        user_id = session.get('user_id')
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')

        # 避免重复记录（同一用户/IP在短时间内的重复访问）
        recent_visit = None
        if user_id:
            # 登录用户：检查最近5分钟是否访问过同一房源
            recent_visit = BrowseHistory.query.filter(
                BrowseHistory.user_id == user_id,
                BrowseHistory.house_id == house_id,
                BrowseHistory.visit_time > datetime.utcnow() - timedelta(minutes=5)
            ).first()
        else:
            # 匿名用户：检查最近5分钟是否从同一IP访问过同一房源
            recent_visit = BrowseHistory.query.filter(
                BrowseHistory.ip_address == ip_address,
                BrowseHistory.house_id == house_id,
                BrowseHistory.visit_time > datetime.utcnow() - timedelta(minutes=5)
            ).first()

        # 如果没有最近访问记录，则添加新记录
        if not recent_visit:
            browse_record = BrowseHistory(
                user_id=user_id,
                house_id=house_id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            db.session.add(browse_record)

        db.session.commit()
    except Exception as e:
        print(f"Error recording browse history: {e}")
        # 即使浏览记录失败，也不影响页面正常显示
        db.session.rollback()
        db.session.commit()  # 只提交浏览次数更新

    # 推荐相似房源（智能推荐算法）
    try:
        house_price = int(house.price) if house.price else 0
        price_range_low = max(0, house_price - 1000)
        price_range_high = house_price + 1000

        # 优先级推荐算法
        # 1. 相同区域 + 相似价格 + 相同租赁类型
        similar_houses_priority1 = HouseInfo.query.filter(
            HouseInfo.region == house.region,
            HouseInfo.rent_type == house.rent_type,
            db.cast(HouseInfo.price, db.Integer).between(price_range_low, price_range_high),
            HouseInfo.id != house.id
        ).limit(4).all()

        # 2. 相同区域 + 相似价格
        similar_houses_priority2 = HouseInfo.query.filter(
            HouseInfo.region == house.region,
            db.cast(HouseInfo.price, db.Integer).between(price_range_low, price_range_high),
            HouseInfo.id != house.id,
            ~HouseInfo.id.in_([h.id for h in similar_houses_priority1])
        ).limit(3).all()

        # 3. 相同区域的其他房源
        similar_houses_priority3 = HouseInfo.query.filter(
            HouseInfo.region == house.region,
            HouseInfo.id != house.id,
            ~HouseInfo.id.in_([h.id for h in similar_houses_priority1 + similar_houses_priority2])
        ).limit(3).all()

        # 4. 如果同区域房源不足，补充相似房型的房源
        existing_ids = [h.id for h in similar_houses_priority1 + similar_houses_priority2 + similar_houses_priority3]
        if len(existing_ids) < 10:
            remaining_count = 10 - len(existing_ids)
            similar_houses_priority4 = HouseInfo.query.filter(
                HouseInfo.rooms == house.rooms,
                HouseInfo.rent_type == house.rent_type,
                HouseInfo.id != house.id,
                ~HouseInfo.id.in_(existing_ids)
            ).limit(remaining_count).all()
        else:
            similar_houses_priority4 = []

        # 合并推荐结果
        similar_houses = similar_houses_priority1 + similar_houses_priority2 + similar_houses_priority3 + similar_houses_priority4

    except Exception as e:
        print(f"Recommendation algorithm error: {e}")
        # 降级到简单推荐
        similar_houses = HouseInfo.query.filter(
            HouseInfo.region == house.region,
            HouseInfo.id != house.id
        ).limit(10).all()

    return render_template('house_detail.html', house=house, similar_houses=similar_houses)

@app.route('/api/houses')
def api_houses():
    """API接口：获取房源列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    houses = HouseInfo.query.paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'houses': [house.to_dict() for house in houses.items],
        'total': houses.total,
        'pages': houses.pages,
        'current_page': houses.page
    })

@app.route('/api/search')
def api_search():
    """API接口：搜索房源"""
    keyword = request.args.get('keyword', '')
    region = request.args.get('region', '')

    query = HouseInfo.query

    if keyword:
        query = query.filter(
            HouseInfo.title.like(f'%{keyword}%') |
            HouseInfo.address.like(f'%{keyword}%')
        )

    if region:
        query = query.filter(HouseInfo.region == region)

    houses = query.limit(50).all()

    return jsonify([house.to_dict() for house in houses])

@app.route('/api/favorites', methods=['POST'])
def add_favorite():
    """添加收藏"""
    data = request.get_json()
    house_id = data.get('house_id')

    if not house_id:
        return jsonify({'success': False, 'message': '房源ID不能为空'})

    # 检查用户是否登录
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})

    user_id = session['user_id']

    # 检查是否已收藏
    existing = Favorite.query.filter_by(user_id=user_id, house_id=house_id).first()
    if existing:
        return jsonify({'success': False, 'message': '该房源已在收藏列表中'})

    # 添加收藏
    favorite = Favorite(user_id=user_id, house_id=house_id)
    db.session.add(favorite)
    db.session.commit()

    return jsonify({'success': True, 'message': '收藏成功'})

@app.route('/api/favorites', methods=['DELETE'])
def remove_favorite():
    """取消收藏"""
    data = request.get_json()
    house_id = data.get('house_id')

    if not house_id:
        return jsonify({'success': False, 'message': '房源ID不能为空'})

    # 检查用户是否登录
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})

    user_id = session['user_id']

    favorite = Favorite.query.filter_by(user_id=user_id, house_id=house_id).first()
    if not favorite:
        return jsonify({'success': False, 'message': '该房源不在收藏列表中'})

    db.session.delete(favorite)
    db.session.commit()

    return jsonify({'success': True, 'message': '取消收藏成功'})

@app.route('/api/favorites', methods=['GET'])
def get_favorites():
    """获取用户收藏列表"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})

    user_id = session['user_id']

    favorites = db.session.query(HouseInfo).join(
        Favorite, HouseInfo.id == Favorite.house_id
    ).filter(Favorite.user_id == user_id).all()

    return jsonify([house.to_dict() for house in favorites])

@app.route('/api/favorites/check/<int:house_id>')
def check_favorite(house_id):
    """检查是否已收藏"""
    if 'user_id' not in session:
        return jsonify({'is_favorite': False})

    user_id = session['user_id']

    favorite = Favorite.query.filter_by(user_id=user_id, house_id=house_id).first()

    return jsonify({'is_favorite': favorite is not None})

@app.route('/favorites')
def favorites_page():
    """收藏页面"""
    if 'user_id' not in session:
        flash('请先登录才能查看收藏', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']

    favorites = db.session.query(HouseInfo).join(
        Favorite, HouseInfo.id == Favorite.house_id
    ).filter(Favorite.user_id == user_id).all()

    return render_template('favorites.html', houses=favorites)

@app.route('/browse-history')
def browse_history_page():
    """浏览记录页面"""
    if 'user_id' not in session:
        flash('请先登录才能查看浏览记录', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # 获取用户的浏览记录，按访问时间倒序排列
    browse_records = db.session.query(BrowseHistory, HouseInfo).join(
        HouseInfo, BrowseHistory.house_id == HouseInfo.id
    ).filter(
        BrowseHistory.user_id == user_id
    ).order_by(BrowseHistory.visit_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template('browse_history.html', browse_records=browse_records)

@app.route('/api/house-analysis/<int:house_id>')
def house_analysis(house_id):
    """房源分析API"""
    try:
        house = HouseInfo.query.get_or_404(house_id)
        house_price = int(house.price) if house.price else 0
        house_area = int(house.area) if house.area else 0

        # 1. 同区域房源价格分析
        region_houses = HouseInfo.query.filter(
            HouseInfo.region == house.region,
            HouseInfo.id != house_id
        ).all()

        region_prices = [int(h.price) for h in region_houses if h.price and h.price.isdigit()]

        if region_prices:
            avg_price = sum(region_prices) / len(region_prices)
            price_comparison = {
                'current': house_price,
                'average': round(avg_price, 0),
                'cheaper_count': len([p for p in region_prices if p < house_price]),
                'total_count': len(region_prices),
                'percentage': round((len([p for p in region_prices if p >= house_price]) / len(region_prices)) * 100, 1)
            }
        else:
            price_comparison = {
                'current': house_price,
                'average': house_price,
                'cheaper_count': 0,
                'total_count': 1,
                'percentage': 50.0
            }

        # 2. 同类型房源分析
        same_type_houses = HouseInfo.query.filter(
            HouseInfo.rooms == house.rooms,
            HouseInfo.rent_type == house.rent_type,
            HouseInfo.id != house_id
        ).all()

        type_analysis = {
            'total': len(same_type_houses),
            'regions': {}
        }

        for h in same_type_houses:
            if h.region not in type_analysis['regions']:
                type_analysis['regions'][h.region] = 0
            type_analysis['regions'][h.region] += 1

        # 3. 性价比分析
        if house_area > 0:
            price_per_sqm = house_price / house_area

            # 同区域同面积范围的房源
            similar_houses = HouseInfo.query.filter(
                HouseInfo.region == house.region,
                HouseInfo.id != house_id
            ).all()

            similar_prices_per_sqm = []
            for h in similar_houses:
                if h.price and h.area and h.price.isdigit() and h.area.isdigit():
                    h_area = int(h.area)
                    h_price = int(h.price)
                    if h_area > 0 and abs(h_area - house_area) <= 20:  # 面积相差不超过20平米
                        similar_prices_per_sqm.append(h_price / h_area)

            if similar_prices_per_sqm:
                avg_price_per_sqm = sum(similar_prices_per_sqm) / len(similar_prices_per_sqm)
                value_score = max(0, min(100, (avg_price_per_sqm - price_per_sqm) / avg_price_per_sqm * 100 + 50))
            else:
                value_score = 50
        else:
            price_per_sqm = 0
            value_score = 50

        value_analysis = {
            'price_per_sqm': round(price_per_sqm, 1),
            'value_score': round(value_score, 1),
            'rating': '优秀' if value_score >= 80 else '良好' if value_score >= 60 else '一般' if value_score >= 40 else '偏高'
        }

        return jsonify({
            'success': True,
            'price_comparison': price_comparison,
            'type_analysis': type_analysis,
            'value_analysis': value_analysis
        })

    except Exception as e:
        print(f"House analysis error: {e}")
        return jsonify({'success': False, 'message': '分析数据获取失败'})

@app.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # 验证输入
        if not username or not email or not password:
            flash('所有字段都是必填的', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('两次输入的密码不一致', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('密码长度至少6位', 'error')
            return render_template('register.html')

        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'error')
            return render_template('register.html')

        # 检查邮箱是否已存在
        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册', 'error')
            return render_template('register.html')

        # 创建新用户
        user = User(username=username, email=email)
        user.set_password(password)

        try:
            db.session.add(user)
            db.session.commit()
            flash('注册成功！请登录', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('注册失败，请稍后重试', 'error')
            return render_template('register.html')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('请输入用户名和密码', 'error')
            return render_template('login.html')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f'欢迎回来，{user.username}！', 'success')

            # 重定向到用户想要访问的页面或首页
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('用户名或密码错误', 'error')
            return render_template('login.html')

    return render_template('login.html')

@app.route('/logout')
def logout():
    """用户登出"""
    session.clear()
    flash('已成功退出登录', 'info')
    return redirect(url_for('index'))

@app.route('/api/price-range')
def get_price_range():
    """获取当前筛选条件下的价格范围"""
    # 获取筛选参数
    search = request.args.get('search', '')
    region = request.args.get('region', '')
    rent_type = request.args.get('rent_type', '')
    rooms = request.args.get('rooms', '')

    # 构建基础查询
    query = HouseInfo.query

    # 应用筛选条件
    if search:
        query = query.filter(
            HouseInfo.title.like(f'%{search}%') |
            HouseInfo.address.like(f'%{search}%') |
            HouseInfo.block.like(f'%{search}%')
        )

    if region:
        query = query.filter(HouseInfo.region.like(f'%{region}%'))

    if rent_type:
        query = query.filter(HouseInfo.rent_type == rent_type)

    if rooms:
        query = query.filter(HouseInfo.rooms.like(f'%{rooms}%'))

    # 获取价格范围（需要转换为数字进行计算）
    try:
        # 使用聚合查询获取最小值和最大值
        price_stats = db.session.query(
            db.func.min(db.cast(HouseInfo.price, db.Integer)).label('min_price'),
            db.func.max(db.cast(HouseInfo.price, db.Integer)).label('max_price'),
            db.func.count(HouseInfo.id).label('count')
        ).filter(
            # 重新应用相同的筛选条件
            *[condition for condition in [
                HouseInfo.title.like(f'%{search}%') | HouseInfo.address.like(f'%{search}%') | HouseInfo.block.like(f'%{search}%') if search else None,
                HouseInfo.region.like(f'%{region}%') if region else None,
                HouseInfo.rent_type == rent_type if rent_type else None,
                HouseInfo.rooms.like(f'%{rooms}%') if rooms else None,
                # 过滤掉无效价格
                db.cast(HouseInfo.price, db.Integer) > 0,
                db.cast(HouseInfo.price, db.Integer) < 100000
            ] if condition is not None]
        ).first()

        min_price = price_stats.min_price or 0
        max_price = price_stats.max_price or 0
        count = price_stats.count or 0

        return jsonify({
            'success': True,
            'min_price': min_price,
            'max_price': max_price,
            'count': count,
            'message': f'当前条件下共 {count} 套房源，价格范围：¥{min_price}-{max_price}/月'
        })

    except Exception as e:
        print(f"Price range query error: {e}")
        return jsonify({
            'success': False,
            'min_price': 0,
            'max_price': 10000,
            'count': 0,
            'message': '价格范围获取失败'
        })

@app.route('/profile')
def profile():
    """用户个人中心"""
    if 'user_id' not in session:
        flash('请先登录', 'warning')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        flash('用户不存在，请重新登录', 'error')
        return redirect(url_for('login'))

    # 获取用户收藏数量
    favorite_count = Favorite.query.filter_by(user_id=user.id).count()

    # 获取用户浏览记录统计
    browse_count = BrowseHistory.query.filter_by(user_id=user.id).count()

    # 获取最近30天的浏览数量
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_browse_count = BrowseHistory.query.filter(
        BrowseHistory.user_id == user.id,
        BrowseHistory.visit_time >= thirty_days_ago
    ).count()

    return render_template('profile.html',
                         user=user,
                         favorite_count=favorite_count,
                         browse_count=browse_count,
                         recent_browse_count=recent_browse_count)

@app.route('/api/nearby-houses')
def nearby_houses():
    """获取附近房源API"""
    try:
        # 获取用户位置参数
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        radius = request.args.get('radius', 5.0, type=float)  # 默认5公里
        limit = request.args.get('limit', 20, type=int)
        try:
            with open('nearby.log', 'a', encoding='utf-8') as f:
                f.write(f"[nearby_houses] lat={lat}, lon={lon}, radius={radius}, limit={limit}, params={dict(request.args)}\n")
        except Exception as log_error:
            print(f"[nearby_houses] log error: {log_error}")

        # 获取筛选参数
        rent_type = request.args.get('rent_type', '')
        min_price = request.args.get('min_price', type=int)
        max_price = request.args.get('max_price', type=int)
        rooms = request.args.get('rooms', '')

        if not lat or not lon:
            return jsonify({'success': False, 'message': '请提供有效的经纬度坐标'})

        if radius > 50:  # 限制最大搜索半径50公里
            radius = 50

        # 计算搜索边界框，优化数据库查询
        bounds = get_nearby_bounds(lat, lon, radius)

        # 查询在边界框内的房源，添加筛选条件
        houses_query = HouseInfo.query.filter(
            HouseInfo.latitude.between(bounds['min_lat'], bounds['max_lat']),
            HouseInfo.longitude.between(bounds['min_lon'], bounds['max_lon']),
            HouseInfo.latitude.isnot(None),
            HouseInfo.longitude.isnot(None)
        )

        # 添加租赁类型筛选
        if rent_type:
            houses_query = houses_query.filter(HouseInfo.rent_type == rent_type)

        # 添加价格范围筛选
        if min_price is not None:
            houses_query = houses_query.filter(db.cast(HouseInfo.price, db.Integer) >= min_price)
        if max_price is not None:
            houses_query = houses_query.filter(db.cast(HouseInfo.price, db.Integer) <= max_price)

        # 添加房间数筛选
        if rooms:
            houses_query = houses_query.filter(HouseInfo.rooms.like(f'%{rooms}%'))

        # 按照与中心点的经纬差排序，尽量先获取更接近的房源
        proximity_order = db.func.abs(HouseInfo.latitude - lat) + db.func.abs(HouseInfo.longitude - lon)
        houses = houses_query.order_by(proximity_order).limit(limit * 5).all()  # 获取更多候选数据用于精确计算
        try:
            with open('nearby.log', 'a', encoding='utf-8') as f:
                f.write(f"[nearby_houses] candidate_count={len(houses)}\n")
        except Exception:
            pass

        # 计算精确距离并排序
        nearby_houses = []
        for house in houses:
            if house.latitude and house.longitude:
                distance = calculate_distance(lat, lon, float(house.latitude), float(house.longitude))
                if distance <= radius:
                    house_dict = house.to_dict()
                    house_dict['distance'] = distance
                    house_dict['distance_text'] = format_distance(distance)
                    nearby_houses.append(house_dict)

        # 按距离排序并限制结果数量
        nearby_houses.sort(key=lambda x: x['distance'])
        nearby_houses = nearby_houses[:limit]

        return jsonify({
            'success': True,
            'houses': nearby_houses,
            'total': len(nearby_houses),
            'center': {'lat': lat, 'lon': lon},
            'radius': radius
        })

    except Exception as e:
        print(f"Nearby houses API error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': '获取附近房源失败'})

@app.route('/api/user-location', methods=['POST'])
def save_user_location():
    """保存用户位置信息"""
    try:
        data = request.get_json()
        lat = data.get('lat')
        lon = data.get('lon')

        if not lat or not lon:
            return jsonify({'success': False, 'message': '位置信息不完整'})

        # 将位置信息保存到session中
        session['user_lat'] = lat
        session['user_lon'] = lon
        session['location_updated'] = datetime.utcnow().isoformat()

        return jsonify({
            'success': True,
            'message': '位置信息已保存',
            'location': {'lat': lat, 'lon': lon}
        })

    except Exception as e:
        print(f"Save location error: {e}")
        return jsonify({'success': False, 'message': '保存位置失败'})

@app.route('/api/city-location/<city>')
def get_city_location(city):
    """获取城市坐标"""
    try:
        if city in CITY_COORDINATES:
            lat, lon = CITY_COORDINATES[city]
            return jsonify({
                'success': True,
                'city': city,
                'lat': lat,
                'lon': lon
            })
        else:
            return jsonify({'success': False, 'message': f'未找到城市 {city} 的坐标信息'})

    except Exception as e:
        print(f"Get city location error: {e}")
        return jsonify({'success': False, 'message': '获取城市位置失败'})

@app.route('/map-search')
@app.route('/map_search')
def map_search_page():
    """地图找房页面"""
    return render_template('map_search.html')

# 附近房源页面已删除 - 功能已整合到地图找房

@app.route('/api/house-charts/<int:house_id>')
def house_charts(house_id):
    """房源详情页图表数据API"""
    try:
        house = HouseInfo.query.get_or_404(house_id)

        # 1. 区域房源户型分布（饼图数据）
        room_distribution = db.session.query(
            HouseInfo.rooms,
            db.func.count(HouseInfo.id).label('count')
        ).filter(
            HouseInfo.region == house.region,
            HouseInfo.rooms.isnot(None),
            HouseInfo.rooms != ''
        ).group_by(HouseInfo.rooms).order_by(db.desc('count')).limit(8).all()

        pie_data = [
            {'value': count, 'name': rooms or '未知户型'}
            for rooms, count in room_distribution
        ]

        # 2. 单价对比（条形图数据）
        # 计算当前房源单价
        current_price = int(house.price) if house.price and house.price.isdigit() else 0
        current_area = int(house.area) if house.area and house.area.isdigit() else 0
        current_unit_price = round(current_price / current_area, 2) if current_area > 0 else 0

        # 计算同区域平均单价
        region_houses = db.session.query(
            HouseInfo.price,
            HouseInfo.area
        ).filter(
            HouseInfo.region == house.region,
            HouseInfo.price.regexp_match('^[0-9]+$'),
            HouseInfo.area.regexp_match('^[0-9]+$'),
            HouseInfo.id != house_id
        ).all()

        valid_unit_prices = []
        for price, area in region_houses:
            try:
                p = int(price)
                a = int(area)
                if a > 0 and p < 100000:  # 过滤异常值
                    valid_unit_prices.append(p / a)
            except:
                continue

        region_avg_unit_price = round(sum(valid_unit_prices) / len(valid_unit_prices), 2) if valid_unit_prices else 0

        # 计算全市平均单价
        city_houses = db.session.query(
            HouseInfo.price,
            HouseInfo.area
        ).filter(
            HouseInfo.price.regexp_match('^[0-9]+$'),
            HouseInfo.area.regexp_match('^[0-9]+$')
        ).limit(5000).all()  # 限制查询数量

        city_valid_prices = []
        for price, area in city_houses:
            try:
                p = int(price)
                a = int(area)
                if a > 0 and p < 100000:
                    city_valid_prices.append(p / a)
            except:
                continue

        city_avg_unit_price = round(sum(city_valid_prices) / len(city_valid_prices), 2) if city_valid_prices else 0

        bar_data = {
            'categories': ['当前房源', f'{house.region}平均', '全市平均'],
            'values': [current_unit_price, region_avg_unit_price, city_avg_unit_price]
        }

        # 3. 朝向分布数据（玫瑰图）
        direction_distribution = db.session.query(
            HouseInfo.direction,
            db.func.count(HouseInfo.id).label('count')
        ).filter(
            HouseInfo.region == house.region,
            HouseInfo.direction.isnot(None),
            HouseInfo.direction != ''
        ).group_by(HouseInfo.direction).order_by(db.desc('count')).limit(8).all()

        rose_data = [
            {'value': count, 'name': direction or '未知朝向'}
            for direction, count in direction_distribution
        ]

        # 4. 价格分布数据（直方图）
        # 获取同区域所有房源价格
        region_prices_query = db.session.query(
            HouseInfo.price
        ).filter(
            HouseInfo.region == house.region,
            HouseInfo.price.regexp_match('^[0-9]+$')
        ).all()

        prices_list = []
        for (price_str,) in region_prices_query:
            try:
                p = int(price_str)
                if p < 100000:  # 过滤异常值
                    prices_list.append(p)
            except:
                continue

        # 按价格区间分组
        price_ranges = {
            '< 2000': 0,
            '2000-4000': 0,
            '4000-6000': 0,
            '6000-8000': 0,
            '8000-10000': 0,
            '10000-15000': 0,
            '>= 15000': 0
        }

        for p in prices_list:
            if p < 2000:
                price_ranges['< 2000'] += 1
            elif p < 4000:
                price_ranges['2000-4000'] += 1
            elif p < 6000:
                price_ranges['4000-6000'] += 1
            elif p < 8000:
                price_ranges['6000-8000'] += 1
            elif p < 10000:
                price_ranges['8000-10000'] += 1
            elif p < 15000:
                price_ranges['10000-15000'] += 1
            else:
                price_ranges['>= 15000'] += 1

        histogram_data = {
            'categories': list(price_ranges.keys()),
            'values': list(price_ranges.values()),
            'current_price': current_price
        }

        # 5. 面积-价格散点图数据
        scatter_houses = db.session.query(
            HouseInfo.area,
            HouseInfo.price,
            HouseInfo.rooms
        ).filter(
            HouseInfo.region == house.region,
            HouseInfo.price.regexp_match('^[0-9]+$'),
            HouseInfo.area.regexp_match('^[0-9]+$'),
            HouseInfo.id != house_id
        ).limit(200).all()  # 限制200个点，避免过于密集

        scatter_data = []
        for area, price, rooms in scatter_houses:
            try:
                a = int(area)
                p = int(price)
                if a > 0 and a < 300 and p > 0 and p < 50000:  # 过滤异常值
                    scatter_data.append({
                        'area': a,
                        'price': p,
                        'rooms': rooms or '未知'
                    })
            except:
                continue

        return jsonify({
            'success': True,
            'pie_data': pie_data,
            'bar_data': bar_data,
            'rose_data': rose_data,
            'histogram_data': histogram_data,
            'scatter_data': scatter_data,
            'current_house': {
                'price': current_price,
                'area': current_area,
                'unit_price': current_unit_price,
                'region': house.region,
                'rooms': house.rooms,
                'direction': house.direction
            }
        })

    except Exception as e:
        print(f"Chart data error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)})

def init_db():
    """初始化数据库表"""
    with app.app_context():
        db.create_all()
        print("数据库表创建成功")

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
