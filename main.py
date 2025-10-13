import wx
from SMUBadmintonAutoBook import auto_book
from SMUBadmintonAutoBook import today_get
from SMUBadmintonAutoBook import cal_target_date
import threading
from datetime import datetime, timedelta
import time, json, subprocess, os, sys
import base64, os, json
from cryptography.fernet import Fernet
from check_driver_gui import CheckDriverFrame

isBooking = False  # 全局变量，防止重复点击

KEY_FILE = '.key'
CFG_FILE = 'user_profile.json'
LOG = 'booking.log'

def log(msg):
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(f'{datetime.now():%Y-%m-%d %H:%M:%S}  {msg}\n')

def _get_key():
        """简易本地密钥：没有就生成一个"""
        if os.path.exists(KEY_FILE):
            with open(KEY_FILE, 'rb') as f:
                return f.read()
        key = Fernet.generate_key()
        with open(KEY_FILE, 'wb') as f:
            f.write(key)
        return key

_cipher = Fernet(_get_key())

def encrypt(txt: str) -> str:
    return _cipher.encrypt(txt.encode()).decode()

def decrypt(txt: str) -> str:
    return _cipher.decrypt(txt.encode()).decode()

class BadmintonFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="SMU 羽毛球自动预约 by CompNebula", size=(600, 800))
        
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        # 信息
        vbox.Add(wx.StaticText(panel, label="欢迎使用SMU 羽毛球自动预约程序！"), flag=wx.TOP | wx.LEFT, border=10)
        vbox.Add(wx.StaticText(panel, label="本程序依赖chrome（谷歌浏览器）运行，如果没有，请前往官网/镜像网站下载"), flag=wx.TOP | wx.LEFT, border=10)

        #修复chromedriver
        vbox.Add(wx.StaticText(panel, label="本程序依赖chromedriver.exe运行，如果出现报错\"Unable to obtain driver for chrome\"，"),flag=wx.TOP | wx.LEFT, border=10)
        vbox.Add(wx.StaticText(panel, label="请点击下方按钮修复"),
                        flag=wx.TOP | wx.LEFT, border=10)
        fix_btn = wx.Button(panel, label="点击修复")
        fix_btn.Bind(wx.EVT_BUTTON, self.on_fix_driver)
        vbox.Add(fix_btn, flag=wx.LEFT, border=10)
        
        # 用self.date_label保存日期控件
        self.date_label = wx.StaticText(panel, label=f"今天日期：{today_get()}")
        vbox.Add(self.date_label, flag=wx.TOP | wx.LEFT, border=10)
        # 账户
        vbox.Add(wx.StaticText(panel, label="账户"), flag=wx.TOP | wx.LEFT, border=10)
        self.user_choice = wx.ComboBox(panel, style=wx.CB_DROPDOWN)
        vbox.Add(self.user_choice, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)
        self.pwd = wx.TextCtrl(panel, style=wx.TE_PASSWORD)
        vbox.Add(wx.StaticText(panel, label="密码"), flag=wx.TOP | wx.LEFT, border=10)
        vbox.Add(self.pwd, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)

        # 记住我 & 清除账号（提前到这里！）
        self.remember_chk = wx.CheckBox(panel, label="记住账号密码")
        self.clear_btn   = wx.Button(panel, label="清除保存")
        remember_box = wx.BoxSizer(wx.HORIZONTAL)
        remember_box.Add(self.remember_chk, 0, wx.ALL, 5)
        remember_box.Add(self.clear_btn,   0, wx.ALL, 5)
        vbox.Add(remember_box, 0, wx.LEFT, 10)

        # 自动填充账号列表
        profiles = self.load_profiles()
        self.user_choice.Set([u for u, _ in profiles])
        if profiles:
            self.user_choice.SetValue(profiles[0][0])
            self.pwd.SetValue(profiles[0][1])
            self.remember_chk.SetValue(True)

        # 选择账号时自动填充密码
        def on_user_choice(evt):
            user = self.user_choice.GetValue()
            for u, p in self.load_profiles():
                if u == user:
                    self.pwd.SetValue(p)
                    break
        self.user_choice.Bind(wx.EVT_COMBOBOX, on_user_choice)

        # 事件绑定
        self.clear_btn.Bind(wx.EVT_BUTTON, self.on_clear_save)

        # 姓名
        vbox.Add(wx.StaticText(panel, label="姓名"), flag=wx.TOP | wx.LEFT, border=10)
        self.name = wx.TextCtrl(panel)
        vbox.Add(self.name, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)

        # 日期
        vbox.Add(wx.StaticText(panel, label="日期"), flag=wx.TOP | wx.LEFT, border=10)
        vbox.Add(wx.StaticText(panel, label="说明：若选择大后天，则自动设置定时今晚零点准时启动；若选择其它，则立即抢场"), flag=wx.TOP | wx.LEFT, border=10)
        # 用self.date_info_label保存四个日期的控件
        self.date_info_label = wx.StaticText(panel, label="")
        vbox.Add(self.date_info_label, flag=wx.TOP | wx.LEFT, border=10)
        self.refresh_date_label()  # 初始化时刷新一次

        self.date = wx.Choice(panel, choices=["今天", "明天", "后天", "大后天（不可用）"])
        self.date.SetSelection(1)  # 默认明天
        vbox.Add(self.date, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)

        # 场地号
        vbox.Add(wx.StaticText(panel, label="场地号 (1-7)"), flag=wx.TOP | wx.LEFT, border=10)
        self.court_num = wx.SpinCtrl(panel, min=1, max=7, initial=6)
        vbox.Add(self.court_num, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)

        # 时间段
        vbox.Add(wx.StaticText(panel, label="时间段"), flag=wx.TOP | wx.LEFT, border=10)
        self.time_slot = wx.Choice(panel, choices=["17:30-19:30", "19:30-21:30"])
        self.time_slot.SetSelection(0)
        vbox.Add(self.time_slot, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)

        # 预约按钮
        btn = wx.Button(panel, label="确定")
        btn.Bind(wx.EVT_BUTTON, self.on_run)

        #取消定时预约
        self.cancel_btn = wx.Button(panel, label="取消定时")
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_cancel_timer)

        btn_box = wx.BoxSizer(wx.HORIZONTAL)
        btn_box.Add(btn, proportion=0, flag=wx.LEFT, border=0)
        btn_box.Add((30, 0))  
        btn_box.Add(self.cancel_btn, proportion=0, flag=wx.RIGHT, border=0)
        vbox.Add(btn_box, flag=wx.ALIGN_CENTER | wx.ALL, border=15)

        # self.cancel_btn = wx.Button(panel, label="测试后台运行状态")
        # self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_test)
        # vbox.Add(self.cancel_btn, flag=wx.ALL | wx.CENTER, border=5)

        # 日志
        vbox.Add(wx.StaticText(panel, label="预约日志"), flag=wx.TOP | wx.LEFT, border=10)
        self.log = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(-1, 100))
        vbox.Add(self.log, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)

        panel.SetSizer(vbox)

        # 自动填充
        saved_user, saved_pwd = self.load_profile()
        if saved_user:
            self.user_choice.SetValue(saved_user)
            self.pwd.SetValue(saved_pwd)
            self.remember_chk.SetValue(True)

        # 定时刷新日期
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)
        self.timer.Start(1000)

        # 初始化时也刷新一次
        self.refresh_date_label()

    def on_fix_driver(self, event):
        # 独立窗口跑下载逻辑，不阻塞主界面
        frame = CheckDriverFrame(self)   # 把 self 传进去当 parent，这样窗口会居中主界面
        frame.Show()

    def refresh_date_label(self):
        self.date_label.SetLabel(f"今天日期：{today_get()}\n")
        # 同步刷新四个日期
        self.date_info_label.SetLabel(
            f"今天：{cal_target_date('今天').strftime('%m月%d日')} "
            f"明天：{cal_target_date('明天').strftime('%m月%d日')} \n"
            f"后天：{cal_target_date('后天').strftime('%m月%d日')} "
            f"大后天：{cal_target_date('大后天').strftime('%m月%d日')}"
        )

    def on_timer(self, event):
        self.refresh_date_label()

    def on_test(self, e):
        wx.MessageBox(f"后台存在：{self._is_daemon_running()}", "调试")

    # ------ 存/取 ------
    def save_profile(self, user: str, pwd: str):
        # 读取已有账号列表
        profiles = []
        if os.path.exists(CFG_FILE):
            with open(CFG_FILE, 'r', encoding='utf-8') as f:
                try:
                    profiles = json.load(f)
                except Exception:
                    profiles = []
        # 检查是否已存在，存在则更新密码，否则追加
        for acc in profiles:
            if decrypt(acc['user']) == user:
                acc['pwd'] = encrypt(pwd)
                break
        else:
            profiles.append({'user': encrypt(user), 'pwd': encrypt(pwd)})
        with open(CFG_FILE, 'w', encoding='utf-8') as f:
            json.dump(profiles, f, ensure_ascii=False, indent=2)

    def load_profile(self) -> tuple[str, str]:
        if not os.path.exists(CFG_FILE):
            return '', ''
        with open(CFG_FILE, 'r', encoding='utf-8') as f:
            profiles = json.load(f)
        if isinstance(profiles, list) and profiles:
            return decrypt(profiles[0]['user']), decrypt(profiles[0]['pwd'])
        return '', ''

    def load_profiles(self):
        if not os.path.exists(CFG_FILE):
            return []
        with open(CFG_FILE, 'r', encoding='utf-8') as f:
            try:
                profiles = json.load(f)
                return [
                    (decrypt(acc['user']), decrypt(acc['pwd']))
                    for acc in profiles
                ]
            except Exception:
                return []

    def clear_profile(self):
        for f in [CFG_FILE, KEY_FILE]:
            if os.path.exists(f):
                os.remove(f)

    def on_clear_save(self, e):
        self.clear_profile()
        self.user_choice.SetValue('')
        self.pwd.SetValue('')
        self.remember_chk.SetValue(False)
        wx.MessageBox("已清除本地保存的账号密码", "提示", wx.OK | wx.ICON_INFORMATION)


    def _is_daemon_running(self):
        try:
            out = subprocess.check_output(
                'tasklist /FI "IMAGENAME eq booking_daemon.exe"',
                shell=True, stderr=subprocess.STDOUT
            ).decode('utf-8', errors='ignore')

            # ****** 调试：把原始输出写文件 ******
            with open('tasklist_debug.log','w',encoding='utf-8') as f:
                f.write(out)
            # ****** 调试结束 ******

            return 'booking_daemon.exe' in out.lower()
        except Exception as e:
            with open('daemon_check.log','a',encoding='utf-8') as f:
                f.write(f'{datetime.now()} 检测异常：{e}\n')
            return False
    
    def on_cancel_timer(self, e):
        if self._is_daemon_running():          # → 当前有定时，执行取消
            subprocess.run('taskkill /F /IM booking_daemon.exe', shell=True)
            if os.path.exists('booking_cfg.json'):
                os.remove('booking_cfg.json')
            wx.MessageBox("已取消后台定时抢场", "提示", wx.OK | wx.ICON_INFORMATION)
        else:
            wx.CallAfter(self.log.AppendText, f"[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] 未设置定时预约，无法取消\n")
            wx.CallAfter(wx.MessageBox, f"未设置定时预约，无法取消", "结果", wx.OK | wx.ICON_ERROR)
            

    def _collect_data(self):
        return {
            "user": self.user_choice.GetValue().strip(),
            "pwd": self.pwd.GetValue().strip(),
            "name": self.name.GetValue().strip(),
            "date": self.date.GetString(self.date.GetSelection()),
            "court_num": self.court_num.GetValue(),
            "time_slot": self.time_slot.GetString(self.time_slot.GetSelection()),
            "tele_num": self.user_choice.GetValue().strip(),
        }

    def on_run(self, e):
        # 收集参数
        global isBooking
        if isBooking:
            wx.MessageBox("正在预约中，请勿重复点击", "提示", wx.OK | wx.ICON_WARNING)
            return
        data = self._collect_data()
        if not all(data.values()):
            wx.MessageBox("请填写完整信息", "提示", wx.OK | wx.ICON_WARNING)
            return
        try:
            if self.remember_chk.IsChecked():
                self.save_profile(data['user'], data['pwd'])
            else:
                self.clear_profile()   # 立即清除
        except Exception as e:
            wx.CallAfter(self.log.AppendText, f"[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] 预约失败：{e}\n")
        # 后台线程跑脚本，避免界面卡死
        self.log.AppendText(f"[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] 开始预约...\n")
        threading.Thread(target=self._run_booking, args=(data,), daemon=True).start()

    def _run_booking(self, data):
        try:
            global isBooking
            isBooking = True
            if data["date"] != "大后天":
                auto_book(**data)
                wx.CallAfter(self.log.AppendText, f"[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] 预约成功！\n")
                wx.CallAfter(wx.MessageBox, "预约成功！", "结果", wx.OK | wx.ICON_INFORMATION)
            else: #加个定时功能，等到半夜十二点的时候用"后天"预订
                try:
                    target_dt = cal_target_date('今天')
                    data['_target_iso'] = target_dt.isoformat()   # 给后台用
                    data["date"] = "后天"  # 大后天变后天
                    # 把参数写进json
                    with open('booking_cfg.json','w',encoding='utf-8') as f:
                        json.dump(data, f)
                    # 启动后台进程（不阻塞）
                    subprocess.Popen(['booking_daemon.exe'],          # 同目录下的打包后后台程序
                                    creationflags=subprocess.DETACHED_PROCESS
                                    if os.name == 'nt' else 0)
                    wx.MessageBox('计时已在后台运行，到点将自动抢场\n本界面可安全关闭',
                                '提示', wx.OK | wx.ICON_INFORMATION)
                    # 可选：直接退出主程序
                    # self.Close(True)
                except Exception as e:
                    wx.CallAfter(self.log.AppendText, f"[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] 预约失败：{e}\n")
                    wx.CallAfter(wx.MessageBox, f"预约失败：{e}", "结果", wx.OK | wx.ICON_ERROR)
        except Exception as e:
            wx.CallAfter(self.log.AppendText, f"[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] 预约失败：{e}\n")
            wx.CallAfter(wx.MessageBox, f"预约失败：{e}", "结果", wx.OK | wx.ICON_ERROR)
        finally:
            isBooking = False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        data = json.load(open('booking_cfg.json', encoding='utf-8'))
        if cmd == '--login-only':
            data['stop_at_main'] = True
            auto_book(**data)          # 只登录，不退出
            input("已登录并停在主界面，按任意键退出...")  #
            sys.exit(0)
        elif cmd == '--auto':
            data.pop('stop_at_main', None)
            auto_book(**data)          # 真正抢场
            sys.exit(0)

    # 正常图形界面
    app = wx.App(False)
    BadmintonFrame().Show()
    app.MainLoop()