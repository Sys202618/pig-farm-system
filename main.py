# -*- coding: utf-8 -*-
"""猪场管理系统打包入口"""
import sys, os
# Add bundled support dirs
sys.path.insert(0, os.path.dirname(sys.executable))

from backend.app import app

if __name__ == '__main__':
    data_dir = os.path.join(os.path.dirname(sys.executable), 'data')
    os.makedirs(data_dir, exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=False)
