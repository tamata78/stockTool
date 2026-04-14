import datetime
import sys
import time
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait  # wait
from selenium.webdriver.support import expected_conditions as EC  # condition wait
from selenium.webdriver.common.action_chains import ActionChains
from slack_bot import Slack
from seleniumUtils import SeleniumUtils
from fileUtils import FileUtils
from selenium.webdriver.common.by import By

class IpoRequest():

    def __init__(self):
        self.driver = SeleniumUtils.getChromedriver(__file__)

        self.applyCount = 0
        self.IPO_REQ_BUTTON_SELECTOR = "a[name] + table .fl01 a img[alt='申込']"
        self.WEB_WAITE_TIME = 90
        self.getIpoStockInfoMessage = ""

        # all member login info
        config = FileUtils.open_file(__file__, "/config.json")

        self.login_info_list = config["sbis_login_info"]

    def ipo_request(self):
        driver = self.driver
        slack = Slack()
        wait = WebDriverWait(driver, self.WEB_WAITE_TIME)
        try:
            # SBI securities page
            driver.get("https://login.sbisec.co.jp/login/entry?_ReturnPageInfo=WPLEThmR001Control%2FWPLEThmR001Tlst10%2FDefaultAID%2FDSWPLEThmR001Control&_ALLPARAM_JSON=&eventCode=")

            for login_info in self.login_info_list:
                self.one_person_ipo_request(driver, wait, login_info, slack)

            # slack notice
            message = "everyone's ipo applied num:" + str(self.applyCount)
            slack.post_message_to_channel("general", message)
        except WebDriverException:
            import traceback
            message = "occurred system error!!\n" + str(traceback.print_exc())
            slack.post_message_to_channel("general", message)
        finally:
            driver.close()

    def one_person_ipo_request(self, driver, wait, login_info, slack):
        username_field = driver.find_element(By.NAME, "username")
        username_field.send_keys(login_info["uid"])
        driver.find_element(By.NAME, "password").send_keys(login_info["upa"])

        # overlay click
        actions = ActionChains(self.driver)
        actions.move_to_element_with_offset(username_field, 10, 10).click().perform()

        # login
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="pw-btn"]'))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="sendEmailButton"]'))).click()

        time.sleep(50)

        # open IPO apply page
        wait.until(EC.presence_of_element_located((By.ID, "domestic-global-nav")))
        driver.find_element(By.XPATH, '//*[@id="domestic-global-nav"]').click()
        driver.find_element(By.XPATH, '//*[@id="domestic-local-nav"]/li[5]/a').click()
        driver.find_element(By.XPATH, '//*[@id="MAINAREA02_780"]/div[1]/a[1]').click()

        # apply IPO
        stock_tables = driver.find_elements(By.CSS_SELECTOR, "a[name]+table")
        if not stock_tables:
            sys.exit()

        # notification of IPO stock info
        ipoStockInfoMessList = []
        ipoStockInfoMessList.append(f"================= IPO apply status {login_info['uid']} =================")
        for table in stock_tables:
            stockInfoTds = table.find_elements(By.CSS_SELECTOR, ".fl01")
            ipoStockInfoMessList.append(self.getIpoStockInfo(stockInfoTds))
        slack.post_message_to_channel("general", '\n'.join(ipoStockInfoMessList))        

        apply_stock_tables = self.createApplyStTbls(stock_tables)
        if not apply_stock_tables:
            sys.exit()

        # get request buttons
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, self.IPO_REQ_BUTTON_SELECTOR)))
        stock_reqbtns = driver.find_elements(By.CSS_SELECTOR, self.IPO_REQ_BUTTON_SELECTOR)

        while(stock_reqbtns):
            stock_reqbtns[0].click()

            # input application contents
            driver.find_element(By.NAME, "suryo").send_keys(6000)  # request num
            driver.find_element(By.XPATH, "//*[@id='strPriceRadio']").click()
            driver.find_element(By.NAME, "useKbn").send_keys(0)
            driver.find_element(By.NAME, "usePoint").send_keys("")
            driver.find_element(By.NAME, "tr_pass").send_keys(login_info["uspa"])
            driver.find_element(By.NAME, "order_kakunin").click()

            # fixed apply
            driver.find_element(By.NAME, "order_btn").click()
            driver.find_element(By.CSS_SELECTOR, ".mtext a[href='/oeliw011?type=21']").click()

            self.applyCount += 1
            stock_reqbtns = driver.find_elements(By.CSS_SELECTOR, self.IPO_REQ_BUTTON_SELECTOR)

        # logout
        driver.find_element(By.XPATH, "//*[contains(@class, 'slc-nav-item') and contains(@class, 'slc-logout')]").click()
        driver.find_element(By.XPATH, "//*[@id='middleAreaM']/div/div[1]/a").click()

    def createApplyStTbls(self, stock_tables):
        applyStTbls = []
        for table in stock_tables:
            if table.find_elements(By.CSS_SELECTOR, self.IPO_REQ_BUTTON_SELECTOR):
                applyStTbls.append(table)

        return applyStTbls

    def getIpoStockInfo(self, stockInfoTds):
        return  f""" {stockInfoTds[0].text}        
        BB:{stockInfoTds[3].text} status:{stockInfoTds[5].text} LotteryRet:{stockInfoTds[15].text}
        """

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
