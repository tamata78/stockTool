# -*- coding: utf-8 -*-
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
        if len(sys.argv) > 2:
            warn_mes = "Sample:\n  python3 sbi_monthly.py [write his memo month]"
            print(warn_mes)
            sys.exit()

        param_han_month = None
        if len(sys.argv) == 2:
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
        driver.get("https://www.netbk.co.jp/contents/pages/wpl010101/i010101CT/DI01010210")
        driver.find_element_by_name("userName").send_keys(login_info["uid"])
        driver.find_element_by_xpath("//input[@type='password']").send_keys(login_info["upa"])
        driver.find_element_by_xpath("//nb-button-login[@nblabel='ログイン']").click()

        driver.find_element_by_xpath("//div[@class='top-hdr-linklist']/ul/li/a[@class='m-icon-ps_furikae']").click()
        # transfar money from delegate
        self.transfarMoney(AcctCode.TRAVEL)
        self.transfarMoney(AcctCode.FUNDING)
        self.transfarMoney(AcctCode.SEXPENSE)
        self.transfarMoney(AcctCode.PERSONAL)
        self.transfarMoney(AcctCode.EDUCATION)
        self.transfarMoney(AcctCode.HIDEPOSIT)

        # access delegate detail
        driver.get("https://www.netbk.co.jp/contents/pages/wpl020201/i020201CT/DI02020100")

        # delegate memo edit
        driver.find_element_by_xpath("//div[@class='m-ctsAccountList-btn-txt view6']").click()
        driver.find_element_by_xpath("//span[@class='m-edit ng-tns-c3-3 ng-star-inserted']").click()

        self.editMemoDelegate(AcctNote.TRAVEL)
        self.editMemoDelegate(AcctNote.FUNDING)
        self.editMemoDelegate(AcctNote.SEXPENSE)
        self.editMemoDelegate(AcctNote.PERSONAL)
        self.editMemoDelegate(AcctNote.EDUCATION)
        self.editMemoDelegate(AcctNote.HIDEPOSIT)
        driver.find_element_by_xpath("//a[@class='m-btnEm-s']").click()

        self.editMemo(AcctNote.TRAVEL)
        self.editMemo(AcctNote.FUNDING)
        self.editMemo(AcctNote.SEXPENSE)
        self.editMemo(AcctNote.PERSONAL)
        self.editMemo(AcctNote.EDUCATION)
        self.editMemo(AcctNote.HIDEPOSIT)

    def transfarMoney(self, acctCode):
        driver = self.driver
        mmoney_info = self.move_money_info
        login_info = self.login_info

        driver.find_element_by_xpath("//div[contains(@class, 'm-formPulldown ng-tns-c3-4')]").click()
        driver.find_element_by_xpath("//li[contains(@class, 'ng-tns-c3-4 ng-star-inserted') and @value=" + AcctCode.DELEGATE.code + "]").click()

        driver.find_element_by_xpath("//div[contains(@class, 'm-formPulldown ng-tns-c3-5')]").click()
        driver.find_element_by_xpath("//li[contains(@class, 'ng-tns-c3-5 ng-star-inserted') and @value=" + acctCode.code + "]").click()
        driver.find_element_by_name("transAmt").send_keys(mmoney_info[acctCode.money_key])
        driver.find_element_by_xpath("//nb-button[@nblabel='確認する']").click()
        driver.find_element_by_xpath("//input[@id='transPW']").send_keys(login_info["uspa"])
        driver.find_element_by_xpath("//nb-button[@nblabel='確定する']").click()
        driver.find_element_by_link_text(u"他の振替を行う").click()

    def editMemoDelegate(self, acctNote):
        driver = self.driver
        zen_month = self.month

        driver.find_element_by_xpath("(//input[@class='ng-tns-c3-3 ng-untouched ng-pristine ng-valid'])[" + acctNote.move_money_order + "]").send_keys(u"" + zen_month + "月分" + acctNote.memo)

    def editMemo(self, acctNote):
        driver = self.driver
        zen_month = self.month

        # select account
        driver.find_element_by_xpath("//*[@class='ui-selectmenu-button ui-widget ui-state-default ui-corner-all']").click()
        driver.find_element_by_xpath("//*[text()='" + acctNote.acct + "']").click()
        driver.find_element_by_xpath("//nb-button[@nblabel='表示']").click()

        driver.find_element_by_xpath("//span[@class='m-edit ng-tns-c3-3 ng-star-inserted']").click()
        driver.find_element_by_xpath("(//input[@class='ng-tns-c3-3 ng-untouched ng-pristine ng-valid'])[1]").send_keys(u"" + zen_month + "月分" + acctNote.memo)
        driver.find_element_by_xpath("//a[@class='m-btnEm-s']").click()

    def tearDown(self):
        self.driver.quit()
        self.assertEqual([], self.verificationErrors)


class AcctCode(Enum):
    DELEGATE = ("1", "delegatee")
    HIDEPOSIT = ("2", "hi_deposit")
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
    HIDEPOSIT = ("0", u"SBIハイブリッド預金", "、つみＮＩＳＡ")

    def __init__(self, move_money_order, acct, memo):
        self.move_money_order = move_money_order
        self.acct = acct
        self.memo = memo


if __name__ == "__main__":
    moveMoney = MoveMoneyInnerAccount()
    moveMoney.sbi_money_move()
