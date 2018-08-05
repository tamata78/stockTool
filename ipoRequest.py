import unittest
import time
import json
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

class PythonOrgSearch(unittest.TestCase):
    def setUp(self):
        # options = Options()
        # options.add_argument('--headless')
        self.driver = webdriver.Chrome("./chromedriver")

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

    def one_person_ipo_request(self, driver, login_info):
        driver.find_element_by_name("user_id").send_keys(login_info["uid"])
        driver.find_element_by_name("user_password").send_keys(login_info["upa"])
        driver.find_element_by_name("ACT_login").click()

        # open IPO apply page
        driver.find_element_by_xpath('//*[@id="navi01P"]/ul/li[3]').click()
        driver.find_element_by_xpath('//*[@id="navi02P"]/ul/li[6]').click()
        driver.find_element_by_xpath('//*[@id="main"]/div[10]/div/div').click()

        # apply IPO
        IPO_REQ_BUTTON = "a[name]+table .mtext a img[alt='申込']"
        while driver.find_elements_by_css_selector(IPO_REQ_BUTTON):
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

        # logout
        driver.find_element_by_xpath('//*[@id="logoutM"]/a/img').click()
        driver.find_element_by_xpath('//*[@id="navi01P"]/ul/li[1]/a/img').click()

    def tearDown(self):
        self.driver.close()

if __name__ == "__main__":
    unittest.main()
