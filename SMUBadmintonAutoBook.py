from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, json
from datetime import datetime, timedelta

name = "张浩宇"
user = "17820663835"
pwd = "Apple755"
url = "http://campus.hongdekejiwuye.com/?propertycode=30001"

def today_get():
    """获取当前时间，返回字符串格式\"MM月DD日\""""
    today = datetime.today()
    return today.strftime("%m月%d日")

def cal_target_date(date_str):
    """将日期字符串转换为datetime对象 \n
    date_str: 可填"今天"、"明天"、"后天" \n
    """
    today = datetime.today()
    if date_str == "今天":
        return today
    elif date_str == "明天":
        return today + timedelta(days=1)
    elif date_str == "后天":
        return today + timedelta(days=2)
    elif date_str == "大后天":
        return today + timedelta(days=3)
    else:
        raise ValueError("日期输入错误！")

def auto_book(user, pwd, name, tele_num, date, court_num, time_slot, isBook=False):
    """自动抢场函数 \n
    user: 账号名 \n
    pwd: 密码 \n
    name: 预订人姓名 \n
    tele_num: 预订人电话 \n
    date: 预订日期，可填"今天"、"明天"、"后天"、"大后天"。若选择"今天"、"明天"、"后天"，则立即进行抢场；若选择"大后天"，则会定时设置今晚十二点自动抢场 \n
    court_num: 预订场地号，可填1-7的数字(建议4-7) \n
    time_slot: 预订时间段，可填"17:30-19:30"或"19:30-21:30" \n
    isBook: 是否是提前定时预约 \n
    """
    opt = Options()
    opt.add_argument('--allow-running-insecure-content')
    opt.add_argument('--disable-web-security')
    opt.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    driver = webdriver.Chrome(options=opt)
    driver.get(url)

    #login
    driver.find_element("css selector", "body > uni-app > uni-page > uni-page-wrapper > uni-page-body > uni-view > uni-view.content > uni-view.u-form > uni-view:nth-child(1) > uni-view.u-form-item__body > uni-view.u-form-item__body__right > uni-view > uni-view > uni-view > uni-view > uni-view > uni-input > div > input").send_keys(user)
    driver.find_element("css selector", "body > uni-app > uni-page > uni-page-wrapper > uni-page-body > uni-view > uni-view.content > uni-view.u-form > uni-view:nth-child(2) > uni-view.u-form-item__body > uni-view.u-form-item__body__right > uni-view > uni-view > uni-view > uni-view > uni-view > uni-input > div > input").send_keys(pwd)
    time.sleep(1)
    login_btn = driver.find_element("css selector", "body > uni-app > uni-page > uni-page-wrapper > uni-page-body > uni-view > uni-view.content > uni-view.u-button-wrap > uni-view > uni-button")
    driver.execute_script("arguments[0].style.border='3px solid red'", login_btn)  # 高亮
    login_btn.click()

    # go into booking page
    try:
        badminton_btn = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//uni-view[uni-text/span[text()='羽毛球场']]//uni-view[@class='lxbtn']")
            )
        )
    except:
        driver.quit()
        raise Exception("登录失败：账号或密码错误，或页面未正常跳转")
    
    while isBook:
        target_dt = datetime.strptime(cal_target_date("今天").isoformat[:10], '%Y-%m-%d')
        run_time = target_dt.replace(hour=23, minute=59, second=55)
        delta = (run_time - datetime.now()).total_seconds()
        if delta < 0:
            break
        time.sleep(1)

    
    try:
        driver.execute_script("arguments[0].style.border='3px solid red'", badminton_btn)
        driver.execute_script(
            "arguments[0].dispatchEvent(new Event('click', {bubbles:true, cancelable:true}))",
            badminton_btn
        )
    except Exception as e:
        driver.quit()
        raise Exception("无法进入羽毛球场预约页面，网络或页面结构发生变化") from e

    # press "ok" button
    tip_confirm_btn = WebDriverWait(driver, 3).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//uni-text[span[text()='确认']]")
        )
    )
    tip_confirm_btn.click()

    #choose date
    target_date = cal_target_date(date).strftime("%m月%d日")
    try:
        date_btn = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable(
                (By.XPATH, f"//uni-view[uni-text/span[text()='{target_date}']]")
            )
        )
        driver.execute_script("arguments[0].style.border='3px solid red'", date_btn)
        date_btn.click()
    except Exception as e:
        driver.quit()
        raise Exception(f"找不到日期【{target_date}】，可能已被系统隐藏或日期格式变化") from e

    #choose court & time slot
    try:
        title_row = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located(
                (By.XPATH,
                f"//uni-view[uni-text[span[text()='{court_num}号场']]"
                f" and uni-text[span[text()='未满']]]")
            )
        )
    except Exception as e:
        driver.quit()
        raise Exception(f"{court_num}号场已满或不可预约，请更换场地号") from e
    time_block = title_row.find_element(
        By.XPATH,
        "following-sibling::uni-view[1]"
    )
    row = time_block.find_element(
        By.XPATH,
        f".//uni-view[uni-text/span[text()='{time_slot}']]/.."
    )
    try:
        status = row.find_element(
            By.XPATH, ".//uni-text[span[contains(.,'可预约') or contains(.,'已满')]]"
        ).text
        driver.execute_script("arguments[0].style.border='3px solid red'", row)
    except Exception as e:
        driver.quit()
        raise Exception("无法读取该时段状态，页面结构可能已更新，请联系开发者") from e
    print(f"{court_num}号场 {time_slot} -> {status}")
    if "可预约" not in status:
        driver.quit()
        raise Exception("该时间段不可预约！")
    
    driver.execute_script("arguments[0].click()", row)

    # book confirm btn
    confirm_btn = WebDriverWait(driver, 3).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//uni-text[span[text()='确定']]")
        )
    )
    driver.execute_script("arguments[0].style.border='3px solid red'", confirm_btn)
    confirm_btn.click()

    # fill in info
    time.sleep(2)
    driver.find_element("css selector", "body > uni-app > uni-page > uni-page-wrapper > uni-page-body > uni-view > uni-view:nth-child(3) > uni-view:nth-child(1) > uni-view:nth-child(1) > uni-view.u-margin-left-20 > uni-input > div > input").send_keys(name)
    driver.find_element("css selector", "body > uni-app > uni-page > uni-page-wrapper > uni-page-body > uni-view > uni-view:nth-child(3) > uni-view:nth-child(1) > uni-view:nth-child(2) > uni-view.u-margin-left-20 > uni-input > div > input").send_keys(tele_num)

    # final confirm btn
    time.sleep(2)
    final_confirm_btn = WebDriverWait(driver, 1).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//uni-text[span[text()='立即预约']]")
        )
    )
    driver.execute_script("arguments[0].style.border='3px solid red'", final_confirm_btn)
    final_confirm_btn.click()
    final_tip_confirm_btn = driver.find_element("css selector", "body > uni-app > uni-modal > div.uni-modal > div.uni-modal__ft > div.uni-modal__btn.uni-modal__btn_primary")
    driver.execute_script("arguments[0].style.border='3px solid red'", final_tip_confirm_btn)
    final_tip_confirm_btn.click()

    time.sleep(2)
    logs = driver.get_log('browser')
    for log in logs:
        if "22005" in log["message"] and "场馆多次预约被限制" in log["message"]:
            driver.quit()
            raise Exception("场馆多次预约被限制")

    print("预约成功！")
    driver.quit()

if __name__ == "__main__":
    # example
    auto_book(user=user, pwd=pwd, name=name, tele_num=user, date="今天", court_num=6, time_slot="17:30-19:30")