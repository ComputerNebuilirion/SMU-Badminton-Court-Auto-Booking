from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import logging, sys
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')

opt = Options()
opt.add_argument('--disable-gpu')
try:
    driver = webdriver.Chrome(options=opt)
    print('Chrome 启动成功，版本：', driver.capabilities['chrome']['chromedriverVersion'])
    driver.quit()
except Exception as e:
    print('失败详情：', e, file=sys.stderr)

finally:
    input('按回车键退出...')