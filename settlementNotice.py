# -*- coding: utf-8 -*-
from slack_bot import Slack
from operator import itemgetter
from seleniumUtils import SeleniumUtils
from stockInfoUtils import StockInfoUtils
from fileUtils import FileUtils


class SettlementNotice():

    def __init__(self):
        self.driver = SeleniumUtils.getChromedriver(__file__)

        # user
        config = FileUtils.open_file(__file__, "/config.json")
        self.user = config["stocks_pf"]

    def set_kabtan_stockInfo(self, stockInfoList):
        driver = self.driver
        for stockInfo in stockInfoList:
            stockCd = stockInfo["stockCd"]
            finance_url = "https://kabutan.jp/stock/finance?code=" + stockCd + "&mode=k"
            driver.get(finance_url)

            # set profitAnnoDay
            profitAnnoDay = driver.find_element_by_xpath(
                "//*[@id='kessan_happyoubi']").text.replace(' 発表', '')
            if profitAnnoDay:
                stockInfo["profitAnnoDay"] = profitAnnoDay[-10:]
            else:
                stockInfo["profitAnnoDay"] = '-'

            # set finance_url
            stockInfo["finance_url"] = "<" + finance_url + "|決算情報>"

    def settlement_notice(self):
        # holdings stock list
        stockInfoList = StockInfoUtils.getPortfolio()

        # set finance info from kabtan
        self.set_kabtan_stockInfo(stockInfoList)

        # set display message
        sortedStockInfoList = sorted(
            stockInfoList, key=itemgetter("profitAnnoDay"))
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
