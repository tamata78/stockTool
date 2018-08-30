# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import os

class SeleniumUtils:

    @staticmethod
    def switch_other_tab(driver, window_handle_len):
        current_handle_len = len(driver.window_handles)
        WebDriverWait(driver, 3).until(lambda driver: current_handle_len > window_handle_len)
        driver.switch_to.window(driver.window_handles[current_handle_len - 1])

        return current_handle_len

    @staticmethod
    def getChromedriver(exec_file):
        exec_file_path = os.path.dirname(os.path.abspath(exec_file))
        return webdriver.Chrome(exec_file_path + "/chromedriver")

