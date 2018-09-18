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
