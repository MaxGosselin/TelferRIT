from time import sleep
from algo.base_algo import BaseAlgo

import pandas as pd


class DemoAlgo(BaseAlgo):
    def __init__(self, case, candle_length=5):
        super().__init__(case)

        # Case specific variables go here
        self.candle_length = candle_length

    def on_update(self):

        # This must come first if you want your data to be fresh.
        self.update_data()
        self.update_candles()
        self.update_tenders()
        
        # Check your limits
        # self.risk_engine()

        # Compute metrics
        # self.model()

        # Algo calculations and trading after here.
        # # print(f" Trader PnL : {self.nlv}\r")

        return self.output_to_gui()

    def update_candles(self):

        # How many ticks since the beginning of this candle ?
        candle_index = (self.tick // self.candle_length) * self.candle_length
        rlast = self.securities.loc["CRZY", "last"]
        clast = self.securities.loc["TAME", "last"]
        
        remainder = self.tick - candle_index
        if remainder > 0:
            CRZY_cndls_df = self.candles.loc["CRZY"].head(remainder)
            TAME_cndls_df = self.candles.loc["TAME"].head(remainder)

            self.CRZY_candle = dict(
                tick=candle_index,
                open=CRZY_cndls_df["open"].iloc[-1],
                high=max(CRZY_cndls_df["high"].max(), rlast),
                low=min(CRZY_cndls_df["low"].min(), rlast),
                close=rlast,
            )

            self.TAME_candle = dict(
                tick=candle_index,
                open=TAME_cndls_df["open"].iloc[-1],
                high=max(TAME_cndls_df["high"].max(), clast),
                low=min(TAME_cndls_df["low"].min(), clast),
                close=clast,
            )

        else:
            
            self.CRZY_candle = dict(
                tick=self.tick, open=rlast, high=rlast, low=rlast, close=rlast
            )

            self.TAME_candle = dict(
                tick=self.tick, open=clast, high=clast, low=clast, close=clast
            )

    def output_to_gui(self):
        """Make a dictionary to pass everything to the gui"""

        return {
            "case": self.case_info,
            "tick": self.tick,
            "period": self.period,
            "trader": self.trader,
            "limits": self.limits,
            "orderbook": self.orderbook,
            "securities": self.securities,
            "CRZY_candle": self.CRZY_candle,
            "TAME_candle": self.TAME_candle,
            "candle_length": self.candle_length,
            # Tender Specific
            "tenders": self.__tenders_to_gui(),
        }

    def __tenders_to_gui(self):
        tenders = []
        for tender in self.tenders.values():
            tenders.append(
                {
                    "ticker": tender.ticker,
                    "quantity": tender.quantity,
                    "price": tender.price,
                    "action": tender.action,
                    "biddable": tender.biddable,
                }
            )
        return tenders
