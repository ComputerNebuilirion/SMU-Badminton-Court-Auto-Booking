# booking_daemon.py
import sys
import json
import time
import schedule
import subprocess
import os
import traceback
from datetime import datetime

CFG = 'booking_cfg.json'
LOG = 'booking_daemon.log'

RUN_ONCE = True          # 只抢一次
finished = False         # 是否已执行

def log(msg):
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(f'{datetime.now():%Y-%m-%d %H:%M:%S}  {msg}\n')

def load_cfg():
    with open(CFG, 'r', encoding='utf-8') as f:
        return json.load(f)

RUN_ONCE = True          # 只抢一次
finished = False         # 是否已执行

def run_login():
    """23:59:30 仅登录并停在主界面"""
    data = load_cfg()
    data['stop_at_main'] = True
    subprocess.Popen([os.path.abspath('SMUBooker.exe'), '--login-only'])
    log('23:59:30 已启动登录，停在主界面')

def run_job():
    """00:00:00 真正抢场"""
    data = load_cfg()
    data.pop('stop_at_main', None)   # 去掉标志
    subprocess.Popen([os.path.abspath('SMUBooker.exe'), '--auto'])
    global finished
    finished = True

def start_countdown():
    today = datetime.now().date()
    login_time = datetime.combine(today, datetime.min.time()).replace(hour=23, minute=59, second=30)
    job_time   = datetime.combine(today, datetime.min.time()).replace(hour=0, minute=0, second=0)

    now = datetime.now()

    # 1. 23:59:30 提前登录
    if now >= login_time:
        run_login()
    else:
        schedule.every().day.at("23:59:30").do(run_login)

    # 2. 00:00:00 准点抢场
    if now >= job_time:
        run_job()
        return
    else:
        schedule.every().day.at("00:00:00").do(run_job)

    while True:
        schedule.run_pending()
        if finished:
            log('任务完成，后台守护退出')
            break
        time.sleep(1)

def main():
    try:
        start_countdown()
    except Exception as e:
        with open('daemon_error.log', 'a', encoding='utf-8') as f:
            f.write(f'{datetime.now()} 崩溃：\n{traceback.format_exc()}\n')

if __name__ == '__main__':
    main()