# -*- coding: utf-8 -*-
from fileUtils import FileUtils
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
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
    def getChromedriver(exec_file):
        exec_file_path = os.path.dirname(os.path.abspath(exec_file))
        return webdriver.Chrome(exec_file_path + "/chromedriver")

    @staticmethod
    def getFirefoxdriver(exec_file, isHeadless):
        exec_file_path = os.path.dirname(os.path.abspath(exec_file))
        options = Options()
        options.add_argument("--headless")

        driver = None
        if isHeadless:
            driver = webdriver.Firefox(firefox_options=options)
        else:
            driver = webdriver.Firefox()

        return driver

    @staticmethod
    def waitClickableTgtElement(driver, tgtEleCssSelector):
        WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.CSS_SELECTOR, tgtEleCssSelector)))

    @staticmethod
    def capureRange(driver, url, capRange):
        driver.get(url)
        # driver.screenshot_as_png
        now_d = datetime.datetime.now()
        strNowTime = now_d.strftime("%Y%m%d%H%M%S")
        img_path = "./cap_" + strNowTime + ".png"

        png = driver.find_element_by_id(capRange).screenshot_as_png

        # driver.get_screenshot_as_file(img_path)

        FileUtils.writeFile(img_path, png)

        return img_path
