# -*- coding: utf-8 -*-
from selenium.common.exceptions import NoSuchElementException
from slack_bot import Slack
from seleniumUtils import SeleniumUtils
from fileUtils import FileUtils
from operator import itemgetter


class UsaSettlementNotice():

    def __init__(self):
        self.driver = SeleniumUtils.getChromedriver(__file__)
        self.CHART_DISP_LIMIT = 5

        # get main login user
        config = FileUtils.open_file(__file__, "/config.json")
        self.user = config["sbis_login_info"][0]

    def settlement_notice(self):
        try:
            # holdings stock list
            stockInfoList = self.get_stockInfoList()

            # set finance info from kabtan
            self.set_settlementInfo(stockInfoList)

            # set display message
            sortedStockInfoList = sorted(stockInfoList, key=itemgetter("profitAnnoDay"))
            mesList = []
            mesLinkParam = []
            stockCount = 1
            for info in sortedStockInfoList:
                mesList.append(" ".join([val for val in info.values()]))
                if stockCount <= self.CHART_DISP_LIMIT:
                    mesLinkParam.append("&symbol" + str(stockCount) + "=" + info["stockCd"])
                    stockCount += 1

            mesStockInfo = '\n'.join(mesList)
            mesCompareChartLink = '<https://www.morningstar.co.jp/frstock_us/compare.html?term=1Y' + ''.join(mesLinkParam) + '|compare chart>'
            mesLineUpChart = '<https://stockcharts.com/freecharts/candleglance.html?$SPX,' + ",".join(stock["stockCd"] for stock in sortedStockInfoList) + '|line up chart>'

            message = "=== portfolio settlement day ===\n" + mesStockInfo + "\n" + mesCompareChartLink + "\n" + mesLineUpChart

            # slack notice
            slack = Slack()
            slack.post_message_to_channel("general", message)

        except NoSuchElementException as e:
            print('settlement info extraction error.')
            print('例外args:', e.args)

        finally:
            self.driver.quit()

    def get_stockInfoList(self):
        # portfolio HP
        driver = self.driver
        user = self.user

        # SBI securities page
        driver.get("https://www.sbisec.co.jp/ETGate")
        driver.find_element_by_name("user_id").send_keys(user["uid"])
        driver.find_element_by_name("user_password").send_keys(user["upa"])
        driver.find_element_by_name("ACT_login").click()

        # forign stock page
        driver.find_element_by_xpath('//*[@id="side"]/div[2]/div/div/div/div/ul/li[3]/a').click()
        XPATH_AC = '//*[@id="gNav"]/ul/li[5]/a/img'
        self.window_handle_len = SeleniumUtils.switch_other_tab(driver, XPATH_AC)
        driver.find_element_by_xpath(XPATH_AC).click()
        driver.find_element_by_xpath('//*[@id="mArea02"]/div[2]/ul/li[2]/a').click()

        # get pfStockInfo
        pfSpeStockList = driver.find_elements_by_xpath('//*[@id="main"]/table[3]/tbody/tr')
        del pfSpeStockList[len(pfSpeStockList) - 1]  # del sum line
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
            stockInfo["profitAnnoDay"] = '-'
            morni_stock_url = "https://www.morningstar.co.jp/frstock_us/stock.html?symbol1=" + stockInfo["stockCd"]
            stockInfo["morningstar_st_info"] = "<" + morni_stock_url + "|stock_info>"

            stockInfoList.append(stockInfo)

        return stockInfoList

    def set_settlementInfo(self, stockInfoList):
        driver = self.driver
        finance_url = "https://www.sbisec.co.jp/ETGate/?_ControlID=WPLETmgR001Control&_PageID=WPLETmgR001Mdtl20&_DataStoreID=DSWPLETmgR001Control&_ActionID=DefaultAID&burl=iris_economicCalendar&cat1=market&cat2=economicCalender&dir=tl1-cal%7Ctl2-schedule%7Ctl3-foreign%7Ctl4-US&file=index.html&getFlg=on"
        driver.get(finance_url)

        settleInfo = driver.find_element_by_xpath('//*[@id="MAINAREA01"]/table/tbody')
        for stockInfo in stockInfoList:
            stockCd = stockInfo["stockCd"]
            try:
                stockInfo["profitAnnoDay"] = settleInfo.find_element_by_xpath(
                    'tr/td[position()=1][text()="' + stockCd + '"]/parent::tr/td[position()=3]').text
            except NoSuchElementException:
                stockInfo["profitAnnoDay"] = "-"


if __name__ == "__main__":

    settle = UsaSettlementNotice()
    settle.settlement_notice()
