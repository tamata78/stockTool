# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
from slacker import Slacker
from slack_bot import Slack
from operator import itemgetter
import datetime
import json
import pdb
import os

class SettlementNotice():
    def __init__(self):
        exec_file_path = os.path.dirname(os.path.abspath(__file__))
        self.driver = webdriver.Chrome(exec_file_path + "/chromedriver")

        # user
        f = open(exec_file_path + "/config.json", 'r')
        json_data = json.load(f)
        f.close()
        self.user = json_data["stocks_pf"]

    def get_stockInfoList(self):
        # portfolio HP
        driver = self.driver
        driver.get("http://woodbook.kir.jp/pf/userpf.php?usid=" + self.user["uid"])

        START_INDEX = 6
        stockInfoList = []
        pfStockList = driver.find_elements_by_xpath("/html/body/table/tbody/tr")
        END_INDEX = (len(pfStockList) - 1) - 1

        # From stock data start index To end index.
        for stockIndex in range(START_INDEX, END_INDEX):
            stockInfo = {}
            pfStockEl = pfStockList[stockIndex]
            elTds = pfStockEl.find_elements_by_tag_name("td")

            stockInfo["stockCd"] = elTds[0].text
            stockInfo["stockNm"] = elTds[1].text

            stockInfoList.append(stockInfo)

        # holdings stock
        return stockInfoList

    def set_kabtan_stockInfo(self, stockInfoList):
        driver = self.driver
        for stockInfo in stockInfoList:
            stockCd = stockInfo["stockCd"]
            finance_url = "https://kabutan.jp/stock/finance?code=" + stockCd + "&mode=k"
            driver.get(finance_url)

            # set profitAnnoDay
            profitAnnoDay = driver.find_element_by_xpath("//*[@id='kessan_happyoubi']").text.replace(' 発表', '')
            if profitAnnoDay:
                stockInfo["profitAnnoDay"] = profitAnnoDay[-10:]
            else:
                stockInfo["profitAnnoDay"] = '-'

            # set finance_url
            stockInfo["finance_url"] = "<" + finance_url + "|決算情報>"

    def settlement_notice(self):
        driver = self.driver
        user = self.user

        # holdings stock list
        stockInfoList = self.get_stockInfoList()

        # set finance info from kabtan
        self.set_kabtan_stockInfo(stockInfoList)

        # set display message
        sortedStockInfoList = sorted(stockInfoList, key=itemgetter("profitAnnoDay"))
        mesList = []
        for info in sortedStockInfoList:
            if info["profitAnnoDay"] == '-':
                continue
            mesList.append(" ".join([val for val in info.values()]))

        mesStockInfo = '\n'.join(mesList)
        message = "■保有銘柄の決算日\n" + mesStockInfo

        # slack notice
        slack = Slack()
        slack.post_message_to_channel("general", message)

        self.driver.quit()

if __name__ == "__main__":
    settle = SettlementNotice()
    settle.settlement_notice()

