# -*- coding: utf-8 -*-
from fileUtils import FileUtils


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
            stockInfoList = []
            pfStockList = driver.find_elements_by_xpath(
                "/html/body/table/tbody/tr")
            END_INDEX = (len(pfStockList) - 1) - 1

            # From stock data start index To end index.
            for stockIndex in range(START_INDEX, END_INDEX):
                pfStockEl = pfStockList[stockIndex]
                elTds = pfStockEl.find_elements_by_tag_name("td")
                portStock = PortStock()
                portStock.stockCd = elTds[0].text
                portStock.stockNm = elTds[1].text
                portStock.volume = elTds[6].text
                portStock.dividend = elTds[7].text
                portStock.numSharesHeld = elTds[8].text
                portStock.purchasePrice = elTds[10].text
                portStock.profitLoss = elTds[11].text
                portStock.profitLossRate = elTds[12].text
                portStock.annualDividend = elTds[13].text
                portStock.yutai = elTds[14].text
                portStock.settlementMonth = elTds[15].text

                stockInfoList.append(portStock)

            # holdings stock
            return stockInfoList

        except Exception:
            import traceback
            traceback.print_exc()
