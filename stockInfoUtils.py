# -*- coding: utf-8 -*-
from fileUtils import FileUtils
from gSpSheetUtils import GSpSheetUtils
from siteStockInfo import PortStock, GmoTranHis


class StockInfoUtils:

    @staticmethod
    def __read_init_conf():
        iniConf = {}
        iniConf["config"] = FileUtils.open_file(__file__, "/config.json")
        return iniConf

    @staticmethod
    def getPortfolio(driver):
        iniConf = StockInfoUtils.__read_init_conf()

        config = iniConf["config"]
        user = config["stocks_pf"]
        try:
            # portfolio HP
            driver.get("http://woodbook.kir.jp/pf/login.php")
            driver.find_element_by_name("usid").send_keys(user["uid"])
            driver.find_element_by_name("pass").send_keys(user["upa"])
            driver.find_element_by_xpath(
                "/html/body/div[3]/form/table/tbody/tr[2]/td[3]/input").click()
            driver.get("http://woodbook.kir.jp/pf/userpf.php?usid=" +
                       user["uid"])

            START_INDEX = 6
            pfStocks = []
            pfStockList = driver.find_elements_by_xpath(
                "/html/body/table/tbody/tr")
            END_INDEX = (len(pfStockList) - 1) - 1

            # From stock data start index To end index.
            for stockIndex in range(START_INDEX, END_INDEX):
                pfStockEl = pfStockList[stockIndex]
                elTds = pfStockEl.find_elements_by_tag_name("td")
                stockCd = elTds[0].text
                stockNm = elTds[1].text
                volume = elTds[6].text
                dividend = elTds[7].text
                numSharesHeld = elTds[8].text
                purchasePrice = elTds[10].text
                profitLoss = elTds[11].text
                profitLossRate = elTds[12].text
                annualDividend = elTds[13].text
                yutai = elTds[14].text
                settlementMonth = elTds[15].text

                portStock = PortStock(stockCd, stockNm, volume, dividend,
                                      numSharesHeld, purchasePrice, profitLoss,
                                      profitLossRate, annualDividend, yutai, settlementMonth)
                pfStocks.append(portStock)

            # holdings stock
            return pfStocks

        except Exception:
            import traceback
            traceback.print_exc()

    @staticmethod
    def getGmoTranHis(driver):
        iniConf = StockInfoUtils.__read_init_conf()
        config = iniConf["config"]
        user = config["gmo"]

        try:
            DISP_SPAN_1WEEK_AGO = 2
            DISP_STATUS_EFFECTIVE_PROMISED = 2

            # login
            driver.get("https://sec-sso.click-sec.com/loginweb/sso-redirect")
            driver.find_element_by_name("j_username").send_keys(user["uid"])
            driver.find_element_by_name("j_password").send_keys(user["upa"])
            driver.find_element_by_name("LoginForm").click()

            # search trade history
            driver.find_element_by_id("kabuMenu").click()
            driver.find_element_by_id("kabuSubMenuOrderHistory").click()
            driver.find_element_by_name("displaySpan").send_keys(DISP_SPAN_1WEEK_AGO)
            driver.find_element_by_name("displayStatus").send_keys(DISP_STATUS_EFFECTIVE_PROMISED)
            driver.find_element_by_id("searchButton").click()

            # get trade history
            traHisDomList = driver.find_elements_by_class_name("is-selectable")
            tranHisInfoList = []

            for index, traHisDom in enumerate(traHisDomList):
                sIndex = str(index)
                traHisTds = traHisDom.find_elements_by_tag_name("td")
                orderStatus = traHisTds[6].find_element_by_id("orderStatus" + sIndex).text
                if orderStatus in ["取消済", "失効済"]:
                    continue

                stockLink = traHisTds[1].find_element_by_id("meigara" + sIndex)
                stockName = traHisTds[1].find_element_by_id("meigaraName" + sIndex)
                stockCd = traHisTds[1].find_element_by_id("securityCode" + sIndex)
                marketCd = traHisTds[1].find_element_by_id("marketCode" + sIndex)
                tranKbn = traHisTds[2].find_element_by_id("torihikiKbn" + sIndex)
                buySellKbn = traHisTds[2].find_element_by_id("baibaiKbn" + sIndex)
                orderAmount = traHisTds[3].find_element_by_id("orderAmount" + sIndex)
                limitPrice = traHisTds[4].find_element_by_id("limitPrice" + sIndex)
                realPrice = traHisTds[4].find_element_by_id("realPrice" + sIndex)
                orderStatus = orderStatus
                tradeDatetime = traHisTds[7].find_element_by_id("tradeDatetime" + sIndex)
                yakujyoSuuryo = traHisTds[8].find_element_by_id("yakujyoSuuryo" + sIndex)
                yakujyoTanka = traHisTds[9].find_element_by_id("yakujyoTanka" + sIndex)
                jyuchuDatetime = traHisTds[11].find_element_by_id("jyuchuDatetime" + sIndex)

                gmoTranHis = GmoTranHis(stockLink, stockName, stockCd, marketCd, tranKbn, buySellKbn, orderAmount, limitPrice, realPrice, orderStatus, tradeDatetime, yakujyoSuuryo, yakujyoTanka, jyuchuDatetime)
                tranHisInfoList.append(gmoTranHis)

            return tranHisInfoList

        except Exception:
            import traceback
            traceback.print_exc()

