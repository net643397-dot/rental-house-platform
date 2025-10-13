from app import app


if __name__ == "__main__":
    # 直接运行 Flask 应用，方便 PyInstaller 打包后的入口
    app.run(host="0.0.0.0", port=5000)
