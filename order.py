from typing import Dict
from enum import IntEnum
from datetime import datetime



class symbol_infoo:
    def __init__(self):
        self.name = ''
        self.digits = 0
        self.tp = 0
        self.sl = 0
        self.sp = 0
        self.lot = 0


class symbol_info:
    def __init__(self):
        self.digits = 0
        self.tp = 0
        self.sl = 0
        self.sp = 0
        self.lot = 0

        self.syminfo: Dict[str,symbol_infoo] = {}
        """
        self.fill_syminfo('EURUSD',10000,5,5,3,0.1)
        self.fill_syminfo('USDJPY',100,50,50,3,0.1)
        self.fill_syminfo('GBPJPY',100,70,70,3,0.1)
        """


    
    def fill_syminfo(self,symbol,digits,tp,sl,sp,lot):
        self.syminfo[symbol] = symbol_infoo()
        self.syminfo[symbol].name = symbol
        self.syminfo[symbol].digits = digits
        self.syminfo[symbol].tp = tp/digits
        self.syminfo[symbol].sl = sl/digits
        self.syminfo[symbol].sp = sp/digits
        self.syminfo[symbol].lot = lot  



class OrderType(IntEnum):
    Sell = 0
    Buy = 1

    @property
    def sign(self) -> float:
        return 1. if self == OrderType.Buy else -1.

    @property
    def opposite(self) -> 'OrderType':
        if self == OrderType.Sell:
            return OrderType.Buy
        return OrderType.Sell



class Order:

    def __init__(
        self,
        id: int, idn: int, type: OrderType, symbol: str, volume: float,
        entry_time: datetime, entry_price: float,
        sl: float, tp: float,
        exit_time: datetime, exit_price: float
    ) -> None:

        self.id = id
        self.idn = idn
        self.type = type
        self.symbol = symbol
        self.volume = volume
        self.entry_time = entry_time
        self.entry_price = entry_price
        self.exit_time = exit_time
        self.exit_price = exit_price
        self.sl=sl
        self.tp=tp
        self.profit = 0.0
        self.status = 'open'
        self.closed = False

