# -*- coding: utf-8 -*-
from selenium.common.exceptions import NoSuchElementException
from fileUtils import FileUtils
from seleniumUtils import SeleniumUtils
from gSpSheetUtils import GSpSheetUtils
from stockInfoUtils import StockInfoUtils


class TranHisReco:

    def __init__(self):
        self.driver = SeleniumUtils.getChromedriver(__file__)
        config = FileUtils.open_file(__file__, "/config.json")
        self.user = config["gmo"]
        self.gc = GSpSheetUtils.getGoogleCred(__file__, 'mypro_sec.json')

    def main(self):
        try:
            # trade his
            self.getTradeHis()
            tran_his_wks = self.gc.open("treHisReco").worksheet("TranHis")
            self.writeTradeHis(tran_his_wks)

        except NoSuchElementException:
            import traceback
            traceback.print_exc()

        except PortfolioError:
            import traceback
            traceback.print_exc()

        finally:
            self.driver.quit()

    def getTradeHis(self):
        driver = self.driver

        self.portfolioList = StockInfoUtils.getPortfolio(driver)
        self.gmoTranHisList = StockInfoUtils.getGmoTranHis(driver)

    def writeTradeHis(self, wks):
        gthList = self.gmoTranHisList
        if len(gthList) == 0:
            return

        for gth in gthList:
            WRITE_LINE_INDEX = 2
            slippage = 0
            profitLoss = 0

            if not gth.limitPrice == "成行":
                slippage = self.subtraStrFloatYen(gth.limitPrice, gth.yakujyoTanka)

            if gth.buySellKbn == "売":
                purchasePrice = self.getPfStockBuyPrice(gth.stockCd)
                profitLoss = self.subtraStrFloatYen(gth.yakujyoTanka, purchasePrice)

            tranHisLine = [gth.tradeDatetime, gth.stockCd, gth.stockName, gth.buySellKbn, gth.orderAmount, gth.jyuchuDatetime, gth.yakujyoTanka, gth.limitPrice, slippage, profitLoss, "GMO", "-", "-"]
            wks.insert_row(tranHisLine, WRITE_LINE_INDEX)

    def getPfStockBuyPrice(self, stockCd):
        pfList = self.portfolioList
        for pf in pfList:
            if pf.stockCd == stockCd:
                return pf.purchasePrice
        return 198.9
        # raise PortfolioError

    def subtraStrFloatYen(self, yenToBeSubtracted, yenToSubtract):
        if (yenToBeSubtracted or yenToSubtract):
            return str(0)

        yen1 = yenToBeSubtracted.replace("円", "")
        yen2 = yenToSubtract.replace("円", "")
        return str(float(yen1) - float(yen2))


class PortfolioError(Exception):
    "portfolio exception base class"


if __name__ == "__main__":
    tranHisReco = TranHisReco()
    tranHisReco.main()
