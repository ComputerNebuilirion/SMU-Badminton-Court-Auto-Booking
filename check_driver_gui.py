# check_driver_gui.py
import wx, os, subprocess, re, urllib.request, zipfile, sys, json, shutil, threading

class CheckDriverFrame(wx.Frame):
    def __init__(self, parent=None):
        super().__init__(parent, title="ChromeDriver 检测与下载", size=(400, 200))
        self.downloading = False
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.info = wx.StaticText(panel, label="正在检测...")
        vbox.Add(self.info, 0, wx.ALL, 10)
        self.log = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(-1, 80))
        vbox.Add(self.log, 1, wx.EXPAND | wx.ALL, 10)
        btn = wx.Button(panel, label="立即下载/修复")
        btn.Bind(wx.EVT_BUTTON, self.on_download)
        vbox.Add(btn, 0, wx.ALL | wx.CENTER, 10)
        panel.SetSizer(vbox)
        self.Center()
        wx.CallAfter(self.detect)

    def detect(self):
        chrome_ver = self.get_chrome_ver()
        if not chrome_ver:
            self.log.AppendText("❌ 未找到 Chrome 安装\n")
            return
        self.log.AppendText(f"✔ Chrome 主版本：{chrome_ver}\n")
        target = os.path.join(os.getcwd(), 'chromedriver.exe')
        if os.path.exists(target):
            driver_ver = self.get_driver_ver(target)
            if driver_ver == chrome_ver:
                self.log.AppendText("✔ 本地 chromedriver 已匹配，无需下载\n")
                self.info.SetLabel("驱动已就绪，可直接运行主程序")
            else:
                self.log.AppendText(f"⚠ 本地版本 {driver_ver} 不匹配，建议重新下载\n")
        else:
            self.log.AppendText("❌ 未找到 chromedriver.exe\n")

    def get_chrome_ver(self):
        try:
            out = subprocess.check_output(
                r'reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version',
                shell=True, stderr=subprocess.STDOUT
            ).decode()
            return re.search(r'(\d+)\.\d+\.\d+\.\d+', out).group(1)
        except:
            return None

    def get_driver_ver(self, exe):
        try:
            out = subprocess.check_output([exe, '--version'], stderr=subprocess.STDOUT).decode()
            return re.search(r'(\d+)\.\d+\.\d+\.\d+', out).group(1)
        except:
            return None

    def on_download(self, e):
        if self.downloading:                       # 运行检测
            wx.MessageBox("下载已在进行中，请稍候", "提示", wx.OK | wx.ICON_INFORMATION)
            return
        self.downloading = True
        threading.Thread(target=self._download_worker, daemon=True).start()

    def _download_worker(self):
        try:
            ver = self.get_chrome_ver()
            if not ver:
                wx.CallAfter(wx.MessageBox, "无法获取 Chrome 版本", "错误", wx.OK | wx.ICON_ERROR)
                return

            wx.CallAfter(self.log.AppendText, f"→ 开始下载 chromedriver {ver}...\n")
            wx.CallAfter(self.log.AppendText, f"→ 正在读取最新补丁号...\n")
            latest = json.load(urllib.request.urlopen(
                f"https://registry.npmmirror.com/-/binary/chrome-for-testing/"
            ))
            for item in latest:
                name = item.get('name', '').strip('/')
                if name.startswith(ver + '.'):
                    latest = name
                    down_url_plat = item['url']
                    wx.CallAfter(self.log.AppendText, f"✔ 最新版本：{latest}\n")
                    break
            down = json.load(urllib.request.urlopen(down_url_plat))
            for item in down:
                if 'win64' in item.get('name', ''):
                    info_url = item['url']
                    break
            info = json.load(urllib.request.urlopen(info_url))
            for item in info:
                if item.get('name', '') == 'chromedriver-win64.zip':
                    down_url = item['url']
                    break
            wx.CallAfter(self.log.AppendText, f"✔ 下载地址：{down_url}\n")
            wx.CallAfter(self.log.AppendText, f"→ 正在开始下载...\n")
            zip_path = 'chromedriver-win64.zip'
            urllib.request.urlretrieve(down_url, zip_path)
            wx.CallAfter(self.log.AppendText, f"→ 正在解压...\n")
            with zipfile.ZipFile(zip_path, 'r') as z:
                z.extractall()
                shutil.move('chromedriver-win64/chromedriver.exe', 'chromedriver.exe')
                shutil.rmtree('chromedriver-win64')
            os.remove(zip_path)
            wx.CallAfter(self.log.AppendText, "✔ 下载并解压完成\n")
            wx.CallAfter(self.detect)
        except Exception as e:
            wx.CallAfter(self.log.AppendText, f"✘ 下载失败：{e}\n")
        finally:
            self.downloading = False   # 释放标志
            


if __name__ == '__main__':
    app = wx.App(False)
    CheckDriverFrame().Show()
    app.MainLoop()