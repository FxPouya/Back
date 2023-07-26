from typing import List, Tuple, Dict, Any, Optional
import pandas as pd
import numpy as np
import os
from datetime import datetime,timedelta

from order import symbol_info, OrderType, Order
from exceptions import OrderNotFound, SymbolNotFound

class BackSim:
    def __init__(self, pairs,trailing,time_duration: timedelta=timedelta()):
        self.pairs = pairs
        self.time_duration=time_duration
        self.equity=0.0
        self.profit=0
        self.balance=50000
        self.start=0
        self.end=0
        self.trailing=trailing

        self.symbols_data: Dict[str, pd.DataFrame] = {}
        self.symbols_info=symbol_info()
        

        self.orders: List[Order] = []
        self.closed_orders: List[Order] = []
        self.current_time: datetime = NotImplemented

        for pair in self.pairs:
            self.load_data(pair)
        
        self.symbols_info.fill_syminfo('EURUSD',10000,10,10,3,0.1)
        self.symbols_info.fill_syminfo('GBPUSD',10000,10,10,3,0.1)
        self.symbols_info.fill_syminfo('USDCAD',10000,10,10,3,0.1)
        self.symbols_info.fill_syminfo('EURCAD',10000,10,10,3,0.1)
        self.symbols_info.fill_syminfo('USDJPY',100,50,50,3,0.1)
        self.symbols_info.fill_syminfo('EURJPY',100,50,50,3,0.1)
        self.symbols_info.fill_syminfo('GBPJPY',100,70,70,3,0.1)
        self.symbols_info.fill_syminfo('XAUUSD',10,70,70,5,0.1)
        self.symbols_info.fill_syminfo('BTCUSD',1,70,70,20,0.1)
        self.symbols_info.fill_syminfo('US30',1,70,70,5,0.1)
        self.symbols_info.fill_syminfo('EURAUD',10000,10,10,3,0.1)
        self.symbols_info.fill_syminfo('GBPCHF',10000,10,10,3,0.1)
        self.symbols_info.fill_syminfo('USDCHF',10000,10,10,3,0.1)
        self.symbols_info.fill_syminfo('AUDUSD',10000,10,10,3,0.1)
        self.symbols_info.fill_syminfo('GBPNZD',10000,70,70,3,0.1)
        self.symbols_info.fill_syminfo('NZDJPY',100,70,70,3,0.1)
        self.symbols_info.fill_syminfo('AUDCHF',10000,70,70,3,0.1)
        self.symbols_info.fill_syminfo('NZDCAD',10000,70,70,3,0.1)
        self.symbols_info.fill_syminfo('AUDJPY',100,70,70,3,0.1)
        self.symbols_info.fill_syminfo('EURGBP',10000,70,70,3,0.1)
        self.symbols_info.fill_syminfo('EURNZD',10000,70,70,3,0.1)
        self.symbols_info.fill_syminfo('GBPNZD',10000,70,70,3,0.1)
        self.symbols_info.fill_syminfo('AUDUSD',10000,10,10,3,0.1)
        self.symbols_info.fill_syminfo('NZDUSD',10000,10,10,3,0.1)
        self.symbols_info.fill_syminfo('GBPAUD',10000,10,10,3,0.1)
        self.symbols_info.fill_syminfo('EURCHF',10000,10,10,3,0.1)
        self.symbols_info.fill_syminfo('NZDCAD',10000,10,10,3,0.1)
        self.symbols_info.fill_syminfo('CHFJPY',100,10,10,3,0.1)
        self.symbols_info.fill_syminfo('NZDUSD',10000,10,10,3,0.1)
        self.symbols_info.fill_syminfo('SPX',1,70,70,3,0.1)
        self.symbols_info.fill_syminfo('ETHUSD',1,70,70,8,0.1)
    

    def load_data(self,symbol):
        df = pd.read_csv(f'./sortData/{symbol}.csv')
        df['date'] = pd.to_datetime(df['date'], format='%Y.%m.%d %H:%M')
        df.set_index('date', inplace=True)
        self.symbols_data[symbol] = df
        

        """df = pd.read_csv(f'./data/{symbol}.csv')
        df.columns = ['date','time', 'open', 'high', 'low', 'close', 'volume']
        df['date'] = df['date']+ ' ' + df['time']
        df.drop('time', axis=1, inplace=True)
        #make date as index
        df['date'] = pd.to_datetime(df['date'], format='%Y.%m.%d %H:%M')
        df.set_index('date', inplace=True)
        self.symbols_data[symbol] = df"""
        
    
    def return_df(self,symbol):
        return self.symbols_data[symbol]
    
    def return_syminfo(self,symbol):
        return self.symbols_info.syminfo[symbol]

    def tick(self, delta_time: timedelta=timedelta()) -> None:
        df = self.symbols_data[self.pairs[0]]

        self.current_time += delta_time
        while self.current_time+delta_time not in df.index and self.current_time+delta_time<df.index[-1]:
            self.current_time += delta_time
            #continue
        
        
        #self.current_time += delta_time

        self.equity = self.balance

        for order in self.orders:
            order.exit_time = self.current_time
            order.exit_price = self.price_at(order.symbol, order.exit_time)['close']
            self.trailing_sl(order, self.trailing)
            self.check_sltp(order)
            self.check_close_at(order, self.time_duration)
            self._update_order_profit(order)
            self.equity += order.profit



    def check_close_at(self,order: Order, time_duration: datetime):
        #print(order.entry_time,order.entry_time+time_duration,time_duration,self.current_time,order.entry_time+time_duration >= self.current_time)
        if order.entry_time+time_duration <= self.current_time:
            try:
                self.close_order(order,'close')
            except:
                pass



    def price_at(self, symbol: str, time: datetime) -> pd.Series:
        df = self.symbols_data[symbol]
        time = self.nearest_time(symbol, time)
        return df.loc[time]
    


    def nearest_time(self, symbol: str, time: datetime) -> datetime:
        df = self.symbols_data[symbol]
        if time in df.index:
            return time
        try:
            i, = df.index.get_indexer([time], method='ffill')
        except KeyError:
            i, = df.index.get_indexer([time], method='bfill')
        return df.index[i]
    

    def _create_order(self, order_type: OrderType, symbol: str, volume: float,slt: float,tpt: float, idn: int) -> Order:
        order_id = len(self.closed_orders) + len(self.orders) + 1
        entry_time = self.current_time
        entry_price = self.price_at(symbol, entry_time)['open']
        sl=entry_price+(slt/self.symbols_info.syminfo[symbol].digits)
        tp=entry_price-(tpt/self.symbols_info.syminfo[symbol].digits)
        if order_type == OrderType.Buy:
            entry_price = self.price_at(symbol, entry_time)['open']+self.symbols_info.syminfo[symbol].sp
            #entry_price = self.price_at(symbol, entry_time)['open']
            sl=entry_price-(slt/self.symbols_info.syminfo[symbol].digits)
            tp=entry_price+(tpt/self.symbols_info.syminfo[symbol].digits)
        exit_time = entry_time
        exit_price = self.price_at(symbol, entry_time)['close']

        

        order = Order(
            order_id, idn, order_type, symbol, volume,
            entry_time, entry_price,sl,tp, exit_time, exit_price
        )
        self._update_order_profit(order)
        

        self.equity += order.profit
        self.orders.append(order)
        return order
    

    def trailing_sl(self,order: Order,trail: float):
        ttrail=abs(order.tp-order.entry_price)*trail
        hh=self.price_at(order.symbol, order.exit_time)['high']
        ll=self.price_at(order.symbol, order.exit_time)['low']
        if order.type==OrderType.Buy:
            if hh-order.entry_price>ttrail and hh-ttrail>order.sl and hh-trail<order.tp:
                order.sl=hh-ttrail
        if order.type==OrderType.Sell:
            if order.entry_price-ll>ttrail and ll+ttrail<order.sl and ll+trail>order.tp:
                order.sl=ll+ttrail

    def close_order(self, order: Order,status) -> float:
        if order not in self.orders:
            raise OrderNotFound("order not found in the order list")

        order.exit_time = self.current_time
        order.exit_price = self.price_at(order.symbol, order.exit_time)['close']
        
        if status=='TP':
            if order.type==OrderType.Buy:
                order.exit_price=order.tp
            else:
                order.exit_price=order.tp
        if status=='SL':
            if order.type==OrderType.Buy:
                order.exit_price=order.sl
            else:
                order.exit_price=order.sl

        self._update_order_profit(order)

        self.balance += order.profit

        order.closed = True
        order.status=status
        self.orders.remove(order)
        self.closed_orders.append(order)
        return order.profit
    

    def check_sltp(self,order: Order):
        if order.type==OrderType.Buy:
            
            if self.price_at(order.symbol, self.current_time)['low']<=order.sl-self.symbols_info.syminfo[order.symbol].sp:
            #if self.price_at(order.symbol, self.current_time)['low']<=order.sl:
                #self.close_order(order,'SL')
                try:
                    self.close_order(order,'SL')
                except:
                    pass
            if self.price_at(order.symbol, self.current_time)['high']>=order.tp:
                #self.close_order(order,'TP')
                try:
                    self.close_order(order,'TP')
                except:
                    pass
        else:
            if self.price_at(order.symbol, self.current_time)['high']>=order.sl:
                #self.close_order(order,'SL')
                try:
                    self.close_order(order,'SL')
                except:
                    pass
            if self.price_at(order.symbol, self.current_time)['low']<=order.tp:
                #self.close_order(order,'TP')
                try:
                    self.close_order(order,'TP')
                except:
                    pass


    def Order_Status(self,symbol):
        Stat=[]
        no1=0
        no2=0
        no3=0
        no4=0
        for order in self.orders:
            if order.symbol==symbol:
                if order.idn==1:no1+=1
                if order.idn==2:no2+=1
                if order.idn==3:no3+=1
                if order.idn==4:no4+=1
                Stat.append([order.idn,order,order.profit,self.equity])

        if len(Stat)==0:
            Stat.append([0,0,0,self.equity])          
        return Stat,no1,no2,no3,no4


    def reset_balance(self):
        self.balance = 0
        self.equity = 0
        self.closed_orders = []
        self.orders = []
        
    
    def get_state(self) -> Dict[str, Any]:
        orders = []
        eq_graph=[]
        ord_p=0
        for order in reversed(self.closed_orders + self.orders):
            orders.append({
                'Id': order.id,
                'Idn': order.idn,
                'Symbol': order.symbol,
                'Type': order.type.name,
                'volume': order.volume,
                'Entry time': order.entry_time,
                'Entry Price': order.entry_price,
                'SL': order.sl,
                'TP': order.tp,
                'Exit time': order.exit_time,
                'Exit Price': order.exit_price,
                'Profit': order.profit,
                'Status': order.status,
                'closed': order.closed,
            })
            #eq_graph.append([order.entry_time,order.profit])
            ord_p+=order.profit
            eq_graph.append(ord_p)
        orders_df = pd.DataFrame(orders)
        #reverse list
        #eq_graph=eq_graph.reverse()

        return {
            'current_time': self.current_time,
            'balance': self.balance,
            'equity': self.equity,
            'orders': orders_df,
            'equity_graph': eq_graph
        }


    def _update_order_profit(self, order: Order) -> None:
        order.exit_time = self.current_time
        #order.exit_price = self.price_at(order.symbol, order.exit_time)['close']
        diff = order.exit_price - order.entry_price
        
        #v = order.volume * self.symbols_info[order.symbol].trade_contract_size
        v=order.volume
        local_profit = v * (order.type.sign * diff*self.symbols_info.syminfo[order.symbol].digits)
        order.profit = local_profit *10
        
    

    
    






        

    