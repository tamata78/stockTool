# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.chrome.options import Options
import os
import datetime


class SeleniumUtils:

    @staticmethod
    def switch_other_tab(driver, switch_page_ope_xpath):
        current_handle_len = len(driver.window_handles)
        WebDriverWait(driver, 15).until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[current_handle_len - 1])
        if switch_page_ope_xpath:
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, switch_page_ope_xpath)))

        return current_handle_len

    @staticmethod
    def getChromedriver(exec_file, isHeadless=False):
        driver = None
        exec_file_path = os.path.dirname(os.path.abspath(exec_file))

        if isHeadless:
            options = Options()
            options.add_argument("--headless")
            driver = webdriver.Chrome(executable_path=exec_file_path + "/chromedriver", chrome_options=options)
        else:
            driver = webdriver.Chrome(executable_path=exec_file_path + "/chromedriver")

        return driver

    @staticmethod
    def getFirefoxdriver(exec_file, isHeadless):
        driver = None

        if isHeadless:
            options = Options()
            options.add_argument("--headless")
            driver = webdriver.Firefox(firefox_options=options)
        else:
            driver = webdriver.Firefox()

        return driver

    @staticmethod
    def waitClickableTgtElement(driver, tgtEleCssSelector):
        WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.CSS_SELECTOR, tgtEleCssSelector)))

    @staticmethod
    def capureRange(driver, url):
        driver.get(url)

        # create img_path
        now_d = datetime.datetime.now()
        strNowTime = now_d.strftime("%Y%m%d%H%M%S")
        img_path = "./cap_" + strNowTime + ".png"

        # set window size and zoom
        page_width = driver.execute_script('return document.body.scrollWidth')
        # page_height = driver.execute_script('return document.body.scrollHeight')
        print(page_width)
        driver.set_window_size(page_width, 200)
        driver.execute_script("document.body.style.zoom='90%'")
        #driver.save_screenshot(img_path)

        return img_path
