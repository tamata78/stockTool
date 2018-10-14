# -*- coding: utf-8 -*-
from slack_bot import Slack
from operator import attrgetter
from seleniumUtils import SeleniumUtils
from stockInfoUtils import StockInfoUtils


class SettlementNotice():

    def __init__(self):
        self.driver = SeleniumUtils.getChromedriver(__file__)

    def settlement_notice(self):
        # holdings stock list
        stockInfoList = StockInfoUtils.getPortfolio(self.driver)

        # set finance info from kabtan
        self.set_kabtan_stockInfo(stockInfoList)

        # set display message
        sortedStockInfoList = sorted(
            stockInfoList, key=attrgetter("profitAnnoDay"))
        mesList = []
        for stockInfo in sortedStockInfoList:
            if stockInfo.profitAnnoDay == '-':
                continue
            mesList.append(" ".join([stockInfo.stockCd, stockInfo.stockNm, stockInfo.profitAnnoDay]))

        mesStockInfo = '\n'.join(mesList)
        message = "■保有銘柄の決算日\n" + mesStockInfo

        # slack notice
        slack = Slack()
        slack.post_message_to_channel("general", message)

        self.driver.quit()

    def set_kabtan_stockInfo(self, stockInfoList):
        driver = self.driver
        for stockInfo in stockInfoList:
            stockCd = stockInfo.stockCd
            finance_url = "https://kabutan.jp/stock/finance?code=" + stockCd + "&mode=k"
            driver.get(finance_url)

            # set profitAnnoDay
            profitAnnoDay = driver.find_element_by_xpath(
                "//*[@id='kessan_happyoubi']").text.replace(' 発表', '')
            if profitAnnoDay:
                stockInfo.profitAnnoDay = profitAnnoDay[-10:]
            else:
                stockInfo.profitAnnoDay = '-'

            # set finance_url
            stockInfo.finance_url = "<" + finance_url + "|決算情報>"


if __name__ == "__main__":
    settle = SettlementNotice()
    settle.settlement_notice()
