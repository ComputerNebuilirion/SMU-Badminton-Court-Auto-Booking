# booking_daemon.py
import sys, json, time, schedule, subprocess, os, traceback
from datetime import datetime
exe_dir = os.path.dirname(sys.executable)          # exe 所在目录
os.chdir(exe_dir)                                  # 切换过去

CFG = 'booking_cfg.json'          # 主程序退出前把参数写进来
LOG = 'booking_daemon.log'        # 后台日志

def log(msg):
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(f'{datetime.now():%Y-%m-%d %H:%M:%S}  {msg}\n')

def load_cfg():
    with open(CFG, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_job():
    log('时间到，启动主程序抢场...')
    # 重新打开主界面并自动抢场
    # 用同目录下的主exe（打包后名字）
    subprocess.Popen([os.path.abspath('SMUBooker.exe'), '--auto'])

def start_countdown():
    data = load_cfg()
    target_dt = datetime.strptime(data['_target_iso'][:10], '%Y-%m-%d')
    run_time = target_dt.replace(hour=23, minute=59, second=0)
    delta = (run_time - datetime.now()).total_seconds()
    if delta <= 0:
        log('错过时机，后台退出')
        return
    # 每天 23:59:55 检查一次（防止电脑休眠错过）
    schedule.every().day.at("23:59:55").do(run_job)
    log(f'后台倒计时已启动，将于 {run_time} 抢场')
    while True:
        schedule.run_pending()
        time.sleep(1)

def main():
    try:
        start_countdown()
    except Exception as e:
        with open('daemon_error.log','a',encoding='utf-8') as f:
            f.write(f'{datetime.now()} 崩溃：\n{traceback.format_exc()}\n')

if __name__ == '__main__':
    main()