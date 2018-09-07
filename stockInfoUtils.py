# -*- coding: utf-8 -*-
from fileUtils import FileUtils
from seleniumUtils import SeleniumUtils


class StockInfoUtils:

    @staticmethod
    def __read_init_conf(iniConf):
        iniConf["driver"] = SeleniumUtils.getChromedriver(__file__)
        iniConf["config"] = FileUtils.open_file(__file__, "/config.json")

    @staticmethod
    def getPortfolio():
        iniConf = {}
        StockInfoUtils.__read_init_conf(iniConf)

        driver = iniConf["driver"]
        iniConf = iniConf["config"]
        user = iniConf["stocks_pf"]
        try:
            # portfolio HP
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

                stockInfoList.append(stockInfo)

            # holdings stock
            return stockInfoList

        except Exception:
            import traceback
            traceback.print_exc()

        finally:
            driver.quit()
