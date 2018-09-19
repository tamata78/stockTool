# -*- coding: utf-8 -*-
import dataclasses


@dataclasses.dataclass
class PortStock:
    stockCd: str
    stockNm: str
    volume: str
    dividend: str
    numSharesHeld: str
    purchasePrice: str
    profitLoss: str
    profitLossRate: str
    annualDividend: str
    yutai: str
    settlementMonth: str

@dataclasses.dataclass
class GmoTranHis:
    stockLink: str
    stockName: str
    stockCd: str
    marketCd: str
    tranKbn: str
    buySellKbn: str
    orderAmount: str
    limitPrice: str
    realPrice: str
    orderStatus: str
    tradeDatetime: str
    yakujyoSuuryo: str
    yakujyoTanka: str
    jyuchuDatetime: str
