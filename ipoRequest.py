import time
import json
import datetime
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from slacker import Slacker
from slack_bot import Slack

class IpoRequest():
    def __init__(self):
        # options = Options()
        # options.add_argument('--headless')
        self.driver = webdriver.Chrome("./chromedriver")
        self.applyCount = 0

        # all member login info
        f = open("config.json", 'r')
        json_data = json.load(f)

        #"sbis_login_info": [
        #{"uid": "111-022200", "upa": "user_pass", "uspa": "user_trade"},
        #{"uid": "111-033300", "upa": "user_pass", "uspa": "user_trade"},
        #]
        login_info = json_data["sbis_login_info"]
        self.login_info_list = login_info

    def test_ipo_request(self):
        driver = self.driver

        # SBI securities page
        driver.get("https://www.sbisec.co.jp/ETGate")

        for login_info in self.login_info_list:
            self.one_person_ipo_request(driver, login_info)

        # slack notice
        slack = Slack()
        message = "everyone's ipo applied num:" + self.applyCount
        slack.post_message_to_channel("general", message)

        self.driver.close()

    def one_person_ipo_request(self, driver, login_info):
        driver.find_element_by_name("user_id").send_keys(login_info["uid"])
        driver.find_element_by_name("user_password").send_keys(login_info["upa"])
        driver.find_element_by_name("ACT_login").click()

        # open IPO apply page
        driver.find_element_by_xpath('//*[@id="navi01P"]/ul/li[3]').click()
        driver.find_element_by_xpath('//*[@id="navi02P"]/ul/li[6]').click()
        driver.find_element_by_xpath('//*[@id="main"]/div[10]/div/div').click()

        # apply IPO
        stock_tables = driver.find_elements_by_css_selector("a[name]+table")
        stock_len = len(stock_tables)
        if stock_len > 0:
            mostReceStockTbl = stock_tables[stock_len - 1]
            stockInfo = mostReceStockTbl.find_elements_by_css_selector(".mtext")

            if not self.isIpoApplyExec(stockInfo):
                sys.exit()

            IPO_REQ_BUTTON = "a[name]+table .mtext a img[alt='申込']"
            while driver.find_element_by_css_selector(IPO_REQ_BUTTON):
                driver.find_element_by_css_selector(IPO_REQ_BUTTON).click()
                driver.find_element_by_name("suryo").send_keys(1000)
                driver.find_element_by_xpath("//*[@id='strPriceRadio']").click()
                driver.find_element_by_name("useKbn").send_keys(0)
                driver.find_element_by_name("usePoint").send_keys("")
                driver.find_element_by_name("tr_pass").send_keys(login_info["uspa"])
                driver.find_element_by_name("order_kakunin").click()

                # fixed apply
                driver.find_element_by_name("order_btn").click()
                driver.find_element_by_css_selector(".mtext a[href='/oeliw011?type=21']").click()

                self.applyCount+=1

        # logout
        driver.find_element_by_xpath('//*[@id="logoutM"]/a/img').click()
        driver.find_element_by_xpath('//*[@id="navi01P"]/ul/li[1]/a/img').click()

    def isIpoApplyExec(self, stockInfo):
        strApplyEndDate = stockInfo[0].split("～")[1].split(" ")[0]
        strApplyEndMon = strApplyEndDate.split("/")[0]
        strApplyEndDay = strApplyEndDate.split("/")[1]

        d_now = datetime.date.today()
        year_now = d_now.year
        applyEndDate = datetime.date(year_now, strApplyEndMon, strApplyEndDay)

        # when today isthe previous most recent apply date, execute application
        return applyEndDate >= d_now - datetime.timedelta(days=1)

if __name__ == "__main__":
    ipoRequest = IpoRequest()
    ipoRequest.test_ipo_request()
