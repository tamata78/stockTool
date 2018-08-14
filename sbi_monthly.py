# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
from enum import Enum
import time, re, sys
import mojimoji
import datetime
import json

class MoveMoneyInnerAccount():
    def __init__(self):
        self.driver = webdriver.Chrome("./chromedriver")
        self.verificationErrors = []

        # target month setting
        param_han_month = None
        if len(sys.argv) > 1:
            param_han_month = sys.argv[1]
        han_month = str(datetime.datetime.today().month + 1)
        self.month = mojimoji.han_to_zen(han_month if param_han_month is None else param_han_month)

        # all member login info
        f = open("config.json", 'r')
        json_data = json.load(f)
        # "sbib_login_info":{"uid": "user_id", "upa": "user_pass", "uspa": "user_tra_pass"},
        sbib = json_data["sbib"]
        self.login_info = sbib["sbib_login_info"]
        self.move_money_info = sbib["move_money_info"]

    def sbi_money_move(self):
        driver = self.driver
        login_info = self.login_info
        zen_month = self.month

        # login
        driver.get("https://www.netbk.co.jp/wpl/NBGate/i010002CT")
        driver.find_element_by_name("userName").send_keys(login_info["uid"])
        driver.find_element_by_name("loginPwdSet").send_keys(login_info["upa"])
        driver.find_element_by_xpath("//*[@id='side']/form/div/div[2]/div[1]/input").click()
        driver.find_element_by_xpath("//*[@id='main']/div[5]/dl[1]/dd/dl[2]/dt/a").click()

        # transfar money from delegate
        self.transfarMoney(AcctCode.TRAVEL)
        self.transfarMoney(AcctCode.FUNDING)
        self.transfarMoney(AcctCode.SEXPENSE)
        self.transfarMoney(AcctCode.PERSONAL)
        self.transfarMoney(AcctCode.EDUCATION)

        # access delegate detail
        driver.get("https://www.netbk.co.jp/wpl/NBGate/i020201CT/PD/01/01/001/01")

        # delegate memo edit
        driver.find_element_by_link_text(u"メモ編集").click()
        driver.find_element_by_name("memoInput").send_keys(u"" + zen_month + "月分")
        driver.find_element_by_xpath("(//input[@name='memoInput'])[2]").clear
        driver.find_element_by_xpath("(//input[@name='memoInput'])[2]").send_keys(u"" + zen_month + "月分")
        driver.find_element_by_xpath("(//input[@name='memoInput'])[3]").clear
        driver.find_element_by_xpath("(//input[@name='memoInput'])[3]").send_keys(u"" + zen_month + "月分、冠婚・ネット購入代")
        driver.find_element_by_xpath("(//input[@name='memoInput'])[4]").clear
        driver.find_element_by_xpath("(//input[@name='memoInput'])[4]").send_keys(u"" + zen_month + "月分、教育教材、寄付控")
        driver.find_element_by_xpath("(//input[@name='memoInput'])[5]").clear
        driver.find_element_by_xpath("(//input[@name='memoInput'])[5]").send_keys(u"" + zen_month + "月分")
        driver.find_element_by_name("ACT_doDecideMemoEdit").click()

        # account details move
        driver.find_element_by_xpath("//*[@id='MC2020001_M03']/a").click()

        # fund memo edit
        driver.find_element_by_name("acctBusPdCodeInput").click()
        Select(driver.find_element_by_name("acctBusPdCodeInput")).select_by_visible_text(u"旅費")
        driver.find_element_by_name("ACT_doShow").click()
        driver.find_element_by_link_text(u"メモ編集").click()
        driver.find_element_by_name("memoInput").send_keys(u"" + zen_month + "月分")
        driver.find_element_by_name("ACT_doDecideMemoEdit").click()

        # fund memo edit
        driver.find_element_by_name("acctBusPdCodeInput").click()
        Select(driver.find_element_by_name("acctBusPdCodeInput")).select_by_visible_text(u"積立（教、節税）")
        driver.find_element_by_name("ACT_doShow").click()
        driver.find_element_by_link_text(u"メモ編集").click()
        driver.find_element_by_name("memoInput").send_keys(u"" + zen_month + "月分教育教材、寄付控")
        driver.find_element_by_xpath("//body").click()
        driver.find_element_by_name("ACT_doDecideMemoEdit").click()

        # special expense memo edit
        driver.find_element_by_name("acctBusPdCodeInput").click()
        Select(driver.find_element_by_name("acctBusPdCodeInput")).select_by_visible_text(u"冠婚・大物・服")
        driver.find_element_by_name("ACT_doShow").click()
        driver.find_element_by_link_text(u"メモ編集").click()
        driver.find_element_by_name("memoInput").send_keys(u"" + zen_month + "月分")
        driver.find_element_by_xpath("//body").click()
        driver.find_element_by_name("ACT_doDecideMemoEdit").click()

        # personal memo edit
        driver.find_element_by_name("acctBusPdCodeInput").click()
        Select(driver.find_element_by_name("acctBusPdCodeInput")).select_by_visible_text(u"個人")
        driver.find_element_by_name("ACT_doShow").click()
        driver.find_element_by_link_text(u"メモ編集").click()
        driver.find_element_by_name("memoInput").send_keys(u"" + zen_month + "月分")
        driver.find_element_by_name("ACT_doDecideMemoEdit").click()

        # education memo edit
        driver.find_element_by_name("acctBusPdCodeInput").click()
        Select(driver.find_element_by_name("acctBusPdCodeInput")).select_by_visible_text(u"教育費")
        driver.find_element_by_name("ACT_doShow").click()
        driver.find_element_by_link_text(u"メモ編集").click()
        driver.find_element_by_name("memoInput").send_keys(u"" + zen_month + "月分")
        driver.find_element_by_name("ACT_doDecideMemoEdit").click()

        # each account display
        driver.find_element_by_xpath(u"(//a[contains(text(),'残高照会（口座別）')])[3]").click()

    def transfarMoney(self, acctCode):
        driver = self.driver
        mmoney_info = self.move_money_info
        login_info = self.login_info

        driver.find_element_by_name("whdrwlAcctCode").click()
        driver.find_element_by_xpath("(//input[@name='dpstAcctCode'])[" + acctCode.code + "]").click()
        driver.find_element_by_name("transAmt").send_keys(mmoney_info[acctCode.money_key])
        driver.find_element_by_name("ACT_doConfirm").click()
        driver.find_element_by_name("transPW").send_keys(login_info["uspa"])
        driver.find_element_by_name("ACT_doDecide").click()
        driver.find_element_by_link_text(u"他の振替を行う").click()

    def tearDown(self):
        self.driver.quit()
        self.assertEqual([], self.verificationErrors)

class AcctCode(Enum):
    TRAVEL = ("3", "travel")
    FUNDING = ("4", "funding")
    SEXPENSE = ("5", "special_expense")
    PERSONAL = ("6", "personal")
    EDUCATION = ("7", "education")

    def __init__(self, code, money_key):
        self.code = code
        self.money_key = money_key

if __name__ == "__main__":
    moveMoney = MoveMoneyInnerAccount()
    moveMoney.sbi_money_move()


