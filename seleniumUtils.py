# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os


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
