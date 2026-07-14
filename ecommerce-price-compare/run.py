"""
统一入口文件
电商商品价格自动化采集与对比工具
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'web':
        from web.app import app
        print("🌐 启动网页服务...")
        print("   访问地址: http://localhost:5000")
        print("   按 Ctrl+C 停止服务")
        print()
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        from cli.main import main as cli_main
        cli_main()


if __name__ == '__main__':
    main()
