#!/usr/bin/env python3
"""
简化版启动脚本
集成了前端和后端，单端口运行
"""

import os
import socket
from flask import send_from_directory

# 导入后端 API
from backend_api import app

# 添加前端路由
@app.route('/')
def index():
    """返回前端首页"""
    return send_from_directory('frontend_simple', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    """返回静态文件"""
    return send_from_directory('frontend_simple', path)

def get_ip():
    """获取本机IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return 'localhost'

if __name__ == '__main__':
    port = 9123
    host = '0.0.0.0'
    ip = get_ip()
    
    print("="*60)
    print("🚀 心理咨询对话生成系统 - 简化版")
    print("="*60)
    print(f"\n📱 访问地址：")
    print(f"\n  本地访问: http://localhost:{port}")
    print(f"  远程访问: http://{ip}:{port}")
    print(f"\n  SSH 端口转发: ssh -L {port}:localhost:{port} user@{ip}")
    print("\n" + "="*60)
    print("按 Ctrl+C 停止服务")
    print("="*60 + "\n")
    
    app.run(host=host, port=port, debug=True)