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

def run_job():
    log('时间到，启动主程序抢场...')
    subprocess.Popen([os.path.abspath('SMUBooker.exe'), '--auto'])
    finished = True

def start_countdown():
    data = load_cfg()
    target_dt = datetime.strptime(data['_target_iso'][:10], '%Y-%m-%d')
    run_time = target_dt.replace(hour=23, minute=59, second=30)
    now = datetime.now()
    delta = (run_time - now).total_seconds()

    # 已过点立即执行
    if delta <= 0:
        log('已到达或错过 23:59:30，立即执行')
        run_job()
        return

    # 注册每天 23:59:55 任务
    schedule.every().day.at("23:59:30").do(run_job)
    log(f'后台倒计时已启动，将于 {run_time} 抢场')
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