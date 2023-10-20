from typing import List, Tuple, Dict, Any, Optional
import pandas as pd
import numpy as np
import os
from datetime import datetime,timedelta

from order import symbol_info, OrderType, Order
from exceptions import OrderNotFound, SymbolNotFound

class BackSim:
    """
    A class that simulates backtesting of trading strategies.

    Attributes:
    pairs (List[str]): A list of currency pairs to be used in the simulation.
    trailing (float): The trailing stop value for the simulation.

    Methods:
    __init__(self, pairs: List[str], trailing: float) -> None:
        Initializes the BackSim object with the given currency pairs and trailing stop value.
    load_data(self, symbol: str) -> None:
        Loads the historical data for the given currency pair.
    return_df(self, symbol: str) -> pd.DataFrame:
        Returns the historical data for the given currency pair.
    return_syminfo(self, symbol: str) -> SymbolInfo:
        Returns the SymbolInfo object for the given currency pair.
    tick(self, delta_time: timedelta=timedelta()) -> None:
        Simulates a tick of the market.
    modify_takeprofit(self, TakeProfit: float, StopLoss: float) -> None:
        Modifies the take profit and stop loss values for all open orders.
    price_at(self, symbol: str, time: datetime) -> pd.Series:
        Returns the price data for the given currency pair at the given time.
    nearest_time(self, symbol: str, time: datetime) -> datetime:
        Returns the nearest time in the historical data for the given currency pair to the given time.
    _create_order(self, order_type: OrderType, symbol: str, volume: float, tpt: float, idn: str) -> Order:
        Creates a new order with the given parameters.
    trailing_sl(self, order: Order, trail: float) -> None:
        Simulates a trailing stop loss for the given order.
    close_order(self, order: Order, status: str, exTime) -> float:
        Closes the given order with the given status and exit time, and returns the profit/loss.
    close_all_orders(self, stat: str) -> None:
        Closes all open orders with the given status.
    """
class BackSim:
    def __init__(self, pairs,trailing,):
        self.pairs = pairs
       
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
        self.pPair=pairs[0]
        

        for pair in self.pairs:
            self.load_data(pair)
        
    
        self.symbols_info.fill_syminfo('XAUUSD',10,70,70,5,0.1)
        self.symbols_info.fill_syminfo('EURUSD',10000,10,10,2,0.1)
        self.sSP=self.symbols_info.syminfo[pairs[0]].sp

    

    def load_data(self,symbol):
        df = pd.read_csv(f'./sortData/{symbol}.csv')
        df['date'] = pd.to_datetime(df['date'], format='%Y.%m.%d %H:%M')
        df.set_index('date', inplace=True)
        self.symbols_data[symbol] = df
        

        
    
    def return_df(self,symbol):
        return self.symbols_data[symbol]
    
    def return_syminfo(self,symbol):
        return self.symbols_info.syminfo[symbol]

    def tick(self,delta_time: timedelta=timedelta()) -> None:
        df = self.symbols_data[self.pairs[0]]

        self.current_time += delta_time
        while self.current_time+delta_time not in df.index and self.current_time+delta_time<df.index[-1]:
            self.current_time += delta_time
            #continue
        
        
 
        self.equity = self.balance
        
        for order in self.orders:
            order.exit_time = self.current_time
            order.exit_price = self.price_at(order.symbol, order.exit_time)['close']
            self.check_sltp(order)
            self._update_order_profit(order)
            self.equity += order.profit



    def modify_SLTP(self,TakeProfit: float,StopLoss: float):
        
        for order in self.orders:
            if order.type == OrderType.Buy: 
                order.tp = order.entry_price + (TakeProfit*self.symbols_info.syminfo[order.symbol].digits)
                order.sl = order.entry_price - (StopLoss*self.symbols_info.syminfo[order.symbol].digits)
            if order.type == OrderType.Sell: 
                order.tp = order.entry_price - (TakeProfit*self.symbols_info.syminfo[order.symbol].digits)-self.sSP
                order.sl = order.entry_price + (StopLoss*self.symbols_info.syminfo[order.symbol].digits)
           



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
    

    def _create_order(self, order_type: OrderType, symbol: str, volume: float,tpt: float, idn: str) -> Order:
        order_id = len(self.closed_orders) + len(self.orders) + 1
        entry_time = self.current_time
        entry_price = self.price_at(symbol, entry_time)['open']
      
        tp=entry_price-(tpt/self.symbols_info.syminfo[symbol].digits)
        if order_type == OrderType.Buy:
            entry_price = self.price_at(symbol, entry_time)['open']+self.symbols_info.syminfo[symbol].sp
            tp=entry_price+(tpt/self.symbols_info.syminfo[symbol].digits)
        exit_time = entry_time
        exit_price = self.price_at(symbol, entry_time)['close']

        

        order = Order(
            order_id, idn, order_type, symbol, volume,
            entry_time, entry_price,tp, exit_time, exit_price
        )
     
        

        self.equity += order.profit
        self.orders.append(order)
        return order
    

    def trailing_sl(self,order: Order,trail: float):
        ttrail=abs(order.tp-order.entry_price)*trail
        hh=self.price_at(order.symbol, order.exit_time)['high']
        ll=self.price_at(order.symbol, order.exit_time)['low']

       

    def close_order(self, order: Order,status,exTime) -> float:
        if order not in self.orders:
            raise OrderNotFound("order not found in the order list")

        #order.exit_time = self.current_time
        #order.exit_price = self.price_at(order.symbol, order.exit_time)['close']
        
        if status=='TP':
            order.exit_price=order.tp
            order.exit_time = self.current_time
            
        
        if status=='close':
            order.exit_price = self.price_at(order.symbol, order.exit_time)['close']
            order.exit_time = self.current_time
           

        self._update_order_profit(order)

        self.balance += order.profit

        order.closed = True
        order.status=status
        #print(order.type,order.idn,order.entry_price,order.tp,order.exit_time)
        self.orders.remove(order)
        self.closed_orders.append(order)
        return order.profit
    

    def close_all_orders(self,stat) -> None:
        for order in self.orders:
            if stat=="All":
                 self.close_order(order,'close',self.current_time)
            if stat=="Buy" and order.type==OrderType.Buy:
                self.close_order(order,'close',self.current_time)
            if stat=="Sell" and order.type==OrderType.Sell:
                self.close_order(order,'close',self.current_time)

    def check_sltp(self,order: Order):

        if order.type==OrderType.Buy:
            if self.price_at(order.symbol, self.current_time)['high']>=order.tp:
                #self.close_order(order,'TP')
                try:
                    self.close_order(order,'TP',order.exit_time)
                except:
                    pass
        if order.type==OrderType.Sell:
            if self.price_at(order.symbol, self.current_time)['low']<=order.tp-self.sSP:
                #self.close_order(order,'TP')
                try:
                    self.close_order(order,'TP',order.exit_time)
                except:
                    pass


    def Order_Status(self,sStatus,symbol):
        lastTime=datetime(2000,1,1)
        lastPrice=0
        step=-1
        count=0
        countB=0
        countS=0
        bundleProfit=0
        for order in self.orders:
            if order.symbol==symbol:
                if order.type==OrderType.Buy and sStatus==1:
                    bundleProfit+=order.profit
                    countB+=1
                    if order.entry_time>lastTime:
                        lastPrice=order.entry_price
                        lastTime=order.entry_time
                        step=int(order.idn.replace('Buy-',''))


                if order.type==OrderType.Sell and sStatus==-1:
                    bundleProfit+=order.profit
                    countS+=1
                    if order.entry_time>lastTime:
                        lastPrice=order.entry_price
                        lastTime=order.entry_time
                        step=int(order.idn.replace('Sell-',''))
                
                #Stat.append([order.idn,order,order.profit,self.equity])

        """if len(Stat)==0:
            Stat.append([0,0,0,self.equity]) """   
        if sStatus==1: count=countB
        if sStatus==-1: count=countS      
        return step,lastPrice,lastTime,count,bundleProfit


    


    def reset_balance(self):
        self.balance = 0
        self.equity = 0
        self.closed_orders = []
        self.orders = []
        
    
    def get_state(self) -> Dict[str, Any]:
        orders = []
        eq_graph=[]
        ord_p=0
        for order in (self.closed_orders + self.orders):
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
                'Profit': round(order.profit,5),
                'Status': order.status,
                'closed': order.closed,
                'lowE': self.price_at(order.symbol, order.exit_time)['low'],
                'highE': self.price_at(order.symbol, order.exit_time)['high'],
                'low': self.price_at(order.symbol, order.entry_time)['low'],
                'high': self.price_at(order.symbol, order.entry_time)['high'],
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
        
    

    
    






        

    