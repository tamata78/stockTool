# -*- coding: utf-8 -*-
from selenium.webdriver.support.ui import Select
from enum import Enum
from seleniumUtils import SeleniumUtils
from fileUtils import FileUtils
import sys
import mojimoji
import datetime


class MoveMoneyInnerAccount():

    def __init__(self):
        self.driver = SeleniumUtils.getChromedriver(__file__)
        self.verificationErrors = []

        # target month setting
        if len(sys.argv) > 1:
            warn_mes = "Sample:\n  python3 sbi_monthly.py [write his memo month]"
            print(warn_mes)
            sys.exit()

        param_han_month = None
        if len(sys.argv) == 1:
            param_han_month = sys.argv[1]
        han_month = str(datetime.datetime.today().month + 1)
        self.month = mojimoji.han_to_zen(
            han_month if param_han_month is None else param_han_month)

        # all member login info
        config = FileUtils.open_file(__file__, "/config.json")
        # "sbib_login_info":{"uid": "user_id", "upa": "user_pass", "uspa": "user_tra_pass"},
        sbib = config["sbib"]
        self.login_info = sbib["sbib_login_info"]
        self.move_money_info = sbib["move_money_info"]

    def sbi_money_move(self):
        driver = self.driver
        login_info = self.login_info

        # login
        driver.get("https://www.netbk.co.jp/wpl/NBGate/i010002CT")
        driver.find_element_by_name("userName").send_keys(login_info["uid"])
        driver.find_element_by_name("loginPwdSet").send_keys(login_info["upa"])
        driver.find_element_by_xpath(
            "//*[@id='side']/form/div/div[2]/div[1]/input").click()
        driver.find_element_by_xpath(
            "//*[@id='main']/div[5]/dl[1]/dd/dl[2]/dt/a").click()

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
        self.editMemoDelegate(AcctNote.TRAVEL)
        self.editMemoDelegate(AcctNote.FUNDING)
        self.editMemoDelegate(AcctNote.SEXPENSE)
        self.editMemoDelegate(AcctNote.PERSONAL)
        self.editMemoDelegate(AcctNote.EDUCATION)
        driver.find_element_by_name("ACT_doDecideMemoEdit").click()

        # account details move
        driver.find_element_by_xpath("//*[@id='MC2020001_M03']/a").click()

        # fund memo edit
        self.editMemo(AcctNote.TRAVEL)
        self.editMemo(AcctNote.FUNDING)
        self.editMemo(AcctNote.SEXPENSE)
        self.editMemo(AcctNote.PERSONAL)
        self.editMemo(AcctNote.EDUCATION)

        # each account display
        driver.find_element_by_xpath(
            u"(//a[contains(text(),'残高照会（口座別）')])[3]").click()

    def transfarMoney(self, acctCode):
        driver = self.driver
        mmoney_info = self.move_money_info
        login_info = self.login_info

        driver.find_element_by_name("whdrwlAcctCode").click()
        driver.find_element_by_xpath(
            "(//input[@name='dpstAcctCode'])[" + acctCode.code + "]").click()
        driver.find_element_by_name("transAmt").send_keys(
            mmoney_info[acctCode.money_key])
        driver.find_element_by_name("ACT_doConfirm").click()
        driver.find_element_by_name("transPW").send_keys(login_info["uspa"])
        driver.find_element_by_name("ACT_doDecide").click()
        driver.find_element_by_link_text(u"他の振替を行う").click()

    def editMemoDelegate(self, acctNote):
        driver = self.driver
        zen_month = self.month

        driver.find_element_by_xpath(
            "(//input[@name='memoInput'])[" + acctNote.move_money_order + "]").send_keys(u"" + zen_month + "月分" + acctNote.memo)

    def editMemo(self, acctNote):
        driver = self.driver
        zen_month = self.month

        driver.find_element_by_name("acctBusPdCodeInput").click()
        Select(driver.find_element_by_name("acctBusPdCodeInput")
               ).select_by_visible_text(acctNote.acct)
        driver.find_element_by_name("ACT_doShow").click()
        driver.find_element_by_link_text(u"メモ編集").click()
        driver.find_element_by_name("memoInput").send_keys(
            u"" + zen_month + "月分" + acctNote.memo)
        driver.find_element_by_name("ACT_doDecideMemoEdit").click()

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


class AcctNote(Enum):
    TRAVEL = ("5", u"旅費", "")
    FUNDING = ("4", u"積立（教、節税）", "、教育教材、寄付控")
    SEXPENSE = ("3", u"冠婚・大物・服", "、冠婚・ネット購入代")
    PERSONAL = ("2", u"個人", "")
    EDUCATION = ("1", u"教育費", "")

    def __init__(self, move_money_order, acct, memo):
        self.move_money_order = move_money_order
        self.acct = acct
        self.memo = memo


if __name__ == "__main__":
    moveMoney = MoveMoneyInnerAccount()
    moveMoney.sbi_money_move()
