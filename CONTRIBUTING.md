# 贡献指南

感谢您对房源信息平台项目的关注！我们欢迎各种形式的贡献。

## 🤝 如何贡献

### 报告问题
- 使用 [Issues](../../issues) 页面报告 bug 或提出功能建议
- 在报告问题时，请提供详细的描述和复现步骤
- 如果是 bug，请说明您的操作系统、Python版本和相关环境信息

### 提交代码
1. **Fork** 本仓库到您的 GitHub 账户
2. **克隆** 您的 fork 到本地：
   ```bash
   git clone https://github.com/your-username/rental-house-platform.git
   cd rental-house-platform
   ```
3. **创建** 新的分支：
   ```bash
   git checkout -b feature/amazing-feature
   ```
4. **提交** 您的更改：
   ```bash
   git commit -m 'Add some amazing feature'
   ```
5. **推送** 到您的 fork：
   ```bash
   git push origin feature/amazing-feature
   ```
6. **创建** Pull Request

## 📝 代码规范

### Python 代码
- 使用 PEP 8 代码风格
- 函数和类需要添加文档字符串
- 变量和函数名使用下划线命名法
- 类名使用驼峰命名法

### JavaScript 代码
- 使用现代 JavaScript (ES6+) 语法
- 函数和复杂逻辑需要添加注释
- 变量和函数名使用驼峰命名法

### 提交信息格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型 (type)**：
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

**示例**：
```
feat(map): add heatmap visualization for house density

- Add heatmap toggle button
- Implement heatmap data calculation
- Update map sidebar UI

Closes #123
```

## 🧪 测试

在提交代码前，请确保：
1. 代码可以正常运行
2. 没有语法错误
3. 功能经过测试
4. 新增功能需要相应的测试

## 📋 开发环境设置

1. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```

2. **配置数据库**：
   - 确保MySQL服务运行
   - 修改 `config.json` 中的数据库配置
   - 运行 `setup_mysql.bat` 初始化数据库

3. **启动应用**：
   ```bash
   python app.py
   ```

## 🚀 部署指南

### 开发环境
```bash
# 克隆项目
git clone https://github.com/your-username/rental-house-platform.git
cd rental-house-platform

# 安装依赖
pip install -r requirements.txt

# 配置数据库
cp config.json.example config.json
# 编辑 config.json 配置数据库信息

# 初始化数据库
# 运行 setup_mysql.bat

# 启动应用
python app.py
```

### 生产环境
```bash
# 使用 PyInstaller 打包
pyinstaller map_house.spec

# 运行打包后的程序
cd dist/map_house
./map_house.exe
```

## 📞 联系方式

- **项目维护者**: 龙宇旸
- **邮箱**: [your-email@example.com]
- **GitHub**: [your-github-username]

## 📄 许可证

通过贡献代码，您同意您的贡献将在 [MIT](LICENSE) 许可证下发布。