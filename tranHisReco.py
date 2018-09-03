# -*- coding: utf-8 -*-
from googleApiUtils import GoogleApiUtils
from fileUtils import FileUtils
from selenium import webdriver
from slacker import Slacker
from slack_bot import Slack
from seleniumUtils import SeleniumUtils
import json

class TranHisReco:
    def __init__(self):
        self.driver = SeleniumUtils.getChromedriver(__file__)
        config = FileUtils.open_file(__file__, "/config.json")
        self.user = config["gmo"]
        self.gc = GoogleApiUtils.getGoogleCred(__file__, 'mypro_sec.json')

    def main(self):
        wks = self.gc.open("treHisReco").sheet1

        wks.update_acell('A1', u'Hello, gspread.')
        print(wks.acell('A1'))

if __name__ == "__main__":
    tranHisReco = TranHisReco()
    tranHisReco.main()

