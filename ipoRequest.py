import datetime
import sys
from selenium.common.exceptions import WebDriverException
from slack_bot import Slack
from seleniumUtils import SeleniumUtils
from fileUtils import FileUtils


class IpoRequest():

    def __init__(self):
        self.driver = SeleniumUtils.getChromedriver(__file__)

        self.applyCount = 0
        self.IPO_REQ_BUTTON_SELECTOR = "a[name] + table .fl01 a img[alt='申込']"

        # all member login info
        config = FileUtils.open_file(__file__, "/config.json")

        self.login_info_list = config["sbis_login_info"]

    def ipo_request(self):
        driver = self.driver
        slack = Slack()
        try:
            # SBI securities page
            driver.get("https://www.sbisec.co.jp/ETGate")

            for login_info in self.login_info_list:
                self.one_person_ipo_request(driver, login_info)

            # slack notice
            message = "everyone's ipo applied num:" + str(self.applyCount)
            slack.post_message_to_channel("general", message)
        except WebDriverException:
            import traceback
            message = "occurred system error!!\n" + str(traceback.print_exc())
            slack.post_message_to_channel("general", message)
        finally:
            driver.close()

    def one_person_ipo_request(self, driver, login_info):
        driver.find_element_by_name("user_id").send_keys(login_info["uid"])
        driver.find_element_by_name(
            "user_password").send_keys(login_info["upa"])
        driver.find_element_by_name("ACT_login").click()

        # open IPO apply page
        driver.find_element_by_xpath('//*[@id="navi01P"]/ul/li[3]').click()
        driver.find_element_by_xpath('//*[@id="navi02P"]/ul/li[6]').click()
        driver.find_element_by_xpath('//*[@id="main"]/div[10]/div/div').click()

        # apply IPO
        stock_tables = driver.find_elements_by_css_selector("a[name]+table")
        if not stock_tables:
            sys.exit()

        apply_stock_tables = self.createApplyStTbls(stock_tables)
        if not apply_stock_tables:
# remove commentout if you fail on the way, commmentout sys.exit()
            sys.exit()
#            driver.find_element_by_xpath('//*[@id="logoutM"]/a/img').click()
#            driver.find_element_by_xpath('//*[@id="navi01P"]/ul/li[1]/a/img').click()
#            return

        stock_len = len(apply_stock_tables)
        mostReceStockTbl = apply_stock_tables[stock_len - 1]
        stockInfoTds = mostReceStockTbl.find_elements_by_css_selector(".fl01")

# do commentout below two line if you fail on the way
        # if not self.isIpoApplyExec(stockInfoTds):
        #    sys.exit()

        stock_reqbtns = driver.find_elements_by_css_selector(self.IPO_REQ_BUTTON_SELECTOR)

        while(stock_reqbtns):
            stock_reqbtns[0].click()

            # input application contents
            driver.find_element_by_name("suryo").send_keys(3000)  # request num
            driver.find_element_by_xpath("//*[@id='strPriceRadio']").click()
            driver.find_element_by_name("useKbn").send_keys(0)
            driver.find_element_by_name("usePoint").send_keys("")
            driver.find_element_by_name(
                "tr_pass").send_keys(login_info["uspa"])
            driver.find_element_by_name("order_kakunin").click()

            # fixed apply
            driver.find_element_by_name("order_btn").click()
            driver.find_element_by_css_selector(
                ".mtext a[href='/oeliw011?type=21']").click()

            self.applyCount += 1
            stock_reqbtns = driver.find_elements_by_css_selector(self.IPO_REQ_BUTTON_SELECTOR)

        # logout
        driver.find_element_by_xpath('//*[@id="logoutM"]/a/img').click()
        driver.find_element_by_xpath(
            '//*[@id="navi01P"]/ul/li[1]/a/img').click()

    def createApplyStTbls(self, stock_tables):
        applyStTbls = []
        for table in stock_tables:
            if table.find_elements_by_css_selector(self.IPO_REQ_BUTTON_SELECTOR):
                applyStTbls.append(table)

        return applyStTbls

    def isIpoApplyExec(self, stockInfoTds):
        strApplyEndDate = stockInfoTds[3].text.split("～")[1].split(" ")[0]
        applyEndMon = int(strApplyEndDate.split("/")[0])
        applyEndDay = int(strApplyEndDate.split("/")[1])

        d_now = datetime.date.today()
        year_now = d_now.year
        applyEndDate = datetime.date(year_now, applyEndMon, applyEndDay)

        # when today is two days ago most recent apply date, execute application
        return applyEndDate >= d_now - datetime.timedelta(days=2)


if __name__ == "__main__":
    ipoRequest = IpoRequest()
    ipoRequest.ipo_request()
