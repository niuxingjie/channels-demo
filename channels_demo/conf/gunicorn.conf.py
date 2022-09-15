# -*- coding: utf-8 -*-
import multiprocessing

# 后台运行
# daemon = True

# 绑定端口
bind = "0.0.0.0:8000"

# 进程数
workers = multiprocessing.cpu_count() * 2 + 1
threads = 3
proc_name = "data-transfer" # 进程名称
pidfile = "/tmp/blog.pid" # 设置进程文件目录
worker_class = "uvicorn.workers.UvicornWorker" # 工作模式协程
timeout = 30 # 超时
max_requests = 6000 # 最大请求数

# 日志
loglevel = 'warning'
