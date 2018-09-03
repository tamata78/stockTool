# coding: UTF-8
import requests
import sys
from bs4 import BeautifulSoup


def getStockInfo(code):
    # create request
    base_url = "http://stocks.finance.yahoo.co.jp/stocks/detail/"
    query = {}
    query["code"] = code + ".T"

    # get stock top page
    ret = requests.get(base_url, params=query)
    soup = BeautifulSoup(ret.content, "lxml")
    return soup


def getStockprice(stockInfo):
    # base stock info
    main = stockInfo.find('div', {'id': 'main'})
    market = main.find('span', {'class': 'stockMainTabName'}).text

    # stock value
    stocktable = stockInfo.find('table', {'class': 'stocksTable'})
    symbol = stocktable.findAll('th', {'class': 'symbol'})[0].text
    stockprice = stocktable.findAll('td', {'class': 'stoksPrice'})[1].text
    change = stocktable.find('td', {'class': 'change'})
    changeprice = change.findAll('span')[1].text

    return market, symbol, stockprice, changeprice


if __name__ == "__main__":
    if len(sys.argv) > 1:
        code = sys.argv[1]

        if code is None:
            code = "3475"
    stockInfoHtml = getStockInfo(code)
    market, symbol, stockprice, changeprice = getStockprice(stockInfoHtml)
    indust = stockInfoHtml.select('dd[class="category yjSb"]')[0].text
    stockInfoDtls = stockInfoHtml.select(
        'div[class="lineFi yjMS clearfix"] strong')

    print(market, indust, symbol, stockprice, changeprice)
    for index, stockInfoDtl in enumerate(stockInfoDtls):
        if index == 2:
            print('配当:', stockInfoDtl.text, '%')
        if index == 4:
            print('PER:', stockInfoDtl.text)
        if index == 5:
            print('PBR:', stockInfoDtl.text)
