# -*- coding: utf-8 -*-
from fileUtils import FileUtils


class StockInfoUtils:

    @staticmethod
    def __read_init_conf(iniConf):
        iniConf["config"] = FileUtils.open_file(__file__, "/config.json")

    @staticmethod
    def getPortfolio(driver):
        iniConf = {}
        StockInfoUtils.__read_init_conf(iniConf)

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
                stockInfo = {}
                pfStockEl = pfStockList[stockIndex]
                elTds = pfStockEl.find_elements_by_tag_name("td")

                stockInfo["stockCd"] = elTds[0].text
                stockInfo["stockNm"] = elTds[1].text
                stockInfo["volume"] = elTds[6].text
                stockInfo["yield"] = elTds[7].text
                stockInfo["num_shares_held"] = elTds[8].text
                stockInfo["purchase_price"] = elTds[10].text
                stockInfo["profit_loss"] = elTds[11].text
                stockInfo["profit_loss_rate"] = elTds[12].text
                stockInfo["annual_dividend"] = elTds[13].text
                stockInfo["yutai"] = elTds[14].text
                stockInfo["settlement_month"] = elTds[15].text

                stockInfoList.append(stockInfo)

            # holdings stock
            return stockInfoList

        except Exception:
            import traceback
            traceback.print_exc()
