# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
from slacker import Slacker
from slack_bot import Slack
from seleniumUtils import SeleniumUtils
from operator import itemgetter
import json

class UsaSettlementNotice():
    def __init__(self):
        self.driver = webdriver.Chrome("./chromedriver")
        self.window_handle_len = len(self.driver.window_handles)

        # get main login user
        f = open("./config.json", 'r')
        config = json.load(f)
        f.close()
        self.user = config["sbis_login_info"][0]

    def settlement_notice(self):
        try:
            driver = self.driver

            # holdings stock list
            stockInfoList = self.get_stockInfoList()

            # set finance info from kabtan
            self.set_settlementInfo(stockInfoList)

            # set display message
            sortedStockInfoList = sorted(stockInfoList, key=itemgetter("profitAnnoDay"))
            mesList = []
            for info in sortedStockInfoList:
                mesList.append(" ".join([val for val in info.values()]))

            mesStockInfo = '\n'.join(mesList)
            message = "portfolio settlement day\n" + mesStockInfo

            # slack notice
            slack = Slack()
            slack.post_message_to_channel("general", message)

        except:
            print 'settlement info extraction error.'

        finally:
            self.driver.quit()

    def get_stockInfoList(self):
        # portfolio HP
        driver = self.driver
        user = self.user
        window_handle_len = self.window_handle_len

        # SBI securities page
        driver.get("https://www.sbisec.co.jp/ETGate")
        driver.find_element_by_name("user_id").send_keys(user["uid"])
        driver.find_element_by_name("user_password").send_keys(user["upa"])
        driver.find_element_by_name("ACT_login").click()

        # forign stock page
        driver.find_element_by_xpath('//*[@id="side"]/div[2]/div/div/div/div/ul/li[3]/a').click()
        self.window_handle_len = SeleniumUtils.switch_other_tab(driver, window_handle_len)
        driver.find_element_by_xpath('//*[@id="gNav"]/ul/li[5]/a/img').click()
        driver.find_element_by_xpath('//*[@id="mArea02"]/div[2]/ul/li[2]/a').click()

        # get pfStockInfo
        pfSpeStockList = driver.find_elements_by_xpath('//*[@id="main"]/table[3]/tbody/tr')
        del pfSpeStockList[len(pfSpeStockList) - 1] # del sum line
        pfNisaStockList = driver.find_elements_by_xpath('//*[@id="main"]/table[5]/tbody/tr')
        del pfNisaStockList[len(pfNisaStockList) - 1]
        pfStockList = pfSpeStockList + pfNisaStockList

        stockInfoList = []
        START_INDEX = 0
        END_INDEX = len(pfStockList)
        for stockIndex in range(START_INDEX, END_INDEX):
            stockInfo = {}
            pfStockEl = pfStockList[stockIndex]
            elTds = pfStockEl.find_elements_by_tag_name('td')

            stockInfo["stockCd"] = elTds[0].find_element_by_tag_name('div').text.split()[0]
            stockInfo["stockNm"] = elTds[0].find_element_by_tag_name('a').text

            stockInfoList.append(stockInfo)

        return stockInfoList

    def set_settlementInfo(self, stockInfoList):
        driver = self.driver
        finance_url = "https://www.sbisec.co.jp/ETGate/?_ControlID=WPLETmgR001Control&_PageID=WPLETmgR001Mdtl20&_DataStoreID=DSWPLETmgR001Control&_ActionID=DefaultAID&burl=iris_economicCalendar&cat1=market&cat2=economicCalender&dir=tl1-cal%7Ctl2-schedule%7Ctl3-foreign%7Ctl4-US&file=index.html&getFlg=on"
        driver.get(finance_url)

        for stockInfo in stockInfoList:
            stockCd = stockInfo["stockCd"]

            # set profitAnnoDay
            settleList = driver.find_elements_by_xpath('//*[@id="MAINAREA01"]/table/tbody/tr')
            profitAnnoDay = ''
            for settle in settleList:
                settleTds = settle.find_elements_by_tag_name('td')
                if settleTds[0].text == stockInfo["stockCd"]:
                    profitAnnoDay = settleTds[2].text

            if profitAnnoDay:
                stockInfo["profitAnnoDay"] = profitAnnoDay
            else:
                stockInfo["profitAnnoDay"] = '-'

            stock_url = "https://www.morningstar.co.jp/frstock_us/stock.html?symbol1=" + stockCd
            stockInfo["stock_info"] = "<" + stock_url + "|stock_info>"

if __name__ == "__main__":
    settle = UsaSettlementNotice()
    settle.settlement_notice()

