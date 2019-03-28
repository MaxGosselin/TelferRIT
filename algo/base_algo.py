import time
from lib.tender import Tender
from lib.helpers import cvols, unpack_books
from lib.case import API_KEY_ERROR, RESPONSE_ERROR, RATE_LIMIT_ERROR
import numpy as np
import pandas as pd
from pandas.io.json import json_normalize


class BaseAlgo:
    def __init__(self, case, slow_update=1):
        self.slow_update = slow_update
        self.last_slow_update = time.time()
        self.case = case

        while not self.case.is_active():
            time.sleep(0.1)

        self.candles = pd.DataFrame([])
        self.tenders = {}
        self.update_data()

    def update_data(self):

        self.case_info = self.case.get_case()
        self.tick = self.case_info["tick"]
        self.period = self.case_info["period"]
        self.trem = self.case_info["ticks_per_period"] - self.tick
        self.limits = self.get_limits()
        self.trader = self.case.get_trader()
        self.nlv = self.trader["nlv"]
        self.orderbook = self.get_orderbook()
        self.securities = self.get_securities()
        self.open_orders = self.get_all_open_orders()
        self.candles = self.get_candles()
        self.news = self.case.get_news()

    def get_limits(self):

        self.limits = json_normalize(self.case.get_limits()).set_index("name")
        return self.limits

    def get_securities(self):

        securities = {}
        for sec in self.case.get_securities():

            # Detect option then strip data (P/C, Strike) from ticker
            if sec["type"] == "OPTION":
                sec["right"] = sec["ticker"][-1]
                sec["strike"] = int("".join(s for s in sec["ticker"] if s.isdigit()))
            securities[sec["ticker"]] = sec

        securities_frame = pd.DataFrame.from_dict(securities, orient="index")

        if not securities_frame.empty:
            return securities_frame.drop(
                [
                    "ticker",
                    "limits",
                    "bid_size",
                    "ask_size",
                    "volume",
                    "unrealized",
                    "realized",
                    "currency",
                    "total_volume",
                    "interest_rate",
                    "is_tradeable",
                    "is_shortable",
                ],
                1,
            )
        else:
            return securities_frame

    def get_orderbook(self):

        books = {}

        for ticker in self.case.tickers:
            tmp = self.case.get_security_book(ticker)
            books[ticker] = cvols(tmp)

        flat_book = unpack_books(books)
        book_frame = pd.DataFrame(flat_book)

        if not book_frame.empty:
            return book_frame.set_index(["ticker", "action", "trader_id"])
        else:
            return book_frame

    def get_candles(self):

        candles = []
        # # print(self.case.tickers)

        for ticker in self.case.tickers:

            raw = self.case.get_candles(
                ticker, self.period, self.case.info["ticks_per_period"]
            )
            for c in raw:
                c["ticker"] = ticker
                candles.append(c)

        # # print(candles)
        candle_frame = pd.DataFrame(candles)
        cols = ["open", "high", "low", "close", "ticker", "tick"]

        # Reindex the df
        candle_frame = candle_frame.set_index(["ticker", "tick"], drop=False).reindex(
            columns=cols
        )

        # # Add some additional info to the candle frame like log returns
        # candle_frame["log_ret"] = candle_frame.groupby("ticker")["close"].apply(
        #     lambda x: np.log(x) - np.log(x.shift())
        # )
        # # print(candle_frame)

        return candle_frame

    def get_all_open_orders(self):

        order_frame = pd.DataFrame(self.case.get_orders())
        if not order_frame.empty:
            return order_frame.set_index(["status", "ticker", "action"])
        else:
            return order_frame

    def add_new_tenders(self):

        for tender in self.case.get_tenders():
            t_id = tender["tender_id"]
            if t_id not in self.tenders:
                self.tenders[t_id] = Tender(tender)

                # # print("Added One!")

    def update_tenders(self):
        """update the tenders after currating the list"""

        # Check for newly arrived tenders
        self.add_new_tenders()

        discards = []

        for t_id, tender in self.tenders.items():
            if tender.expiry < self.case.get_tick():
                discards.append(t_id)

            else:
                tender.update(self.orderbook.loc[tender.ticker, tender.action])

        for d in discards:
            self.tenders.pop(d, None)

    def display(self):

        for t in self.tenders.values():
            pass
            # print(f"Tender Available:  {t.quantity} shares of {t.ticker} at {t.price}")

    def post_order(
        self, ticker, otype, quantity, action, price=None, dry=0, big=False, maxsize=100
    ):

        try:
            if big:
                return self.__post_big_order(
                    ticker, otype, quantity, action, price, maxsize
                )

            else:
                return self.case.post_order(ticker, otype, quantity, action, price)

        except RESPONSE_ERROR as RESPERR:
            if "trading limits" in RESPERR.message:
                # # print(self.limits)
                sec_type = self.securities.loc[ticker, "type"]
                sec_type = "OPT" if sec_type == "OPTION" else sec_type
                sec_type = "ETF" if ticker == "RTM" else sec_type
                gross_space = self.limits.loc[f"Limit-{sec_type}", "gross_limit"] - abs(
                    self.limits.loc[f"Limit-{sec_type}", "gross"]
                )

                net_space = self.limits.loc[f"Limit-{sec_type}", "net_limit"] - abs(
                    self.limits.loc[f"Limit-{sec_type}", "net"]
                )

                space = max(min(gross_space, net_space), 0)

                if space > 0:
                    try:
                        self.case.post_order(ticker, otype, space, action, price)
                    except:
                        pass
                       

            else:
                pass
                # print("problem")
                # print(*RESPERR.message)
                # print(*RESPERR.outputs, sep="\n")

        except RATE_LIMIT_ERROR as RLIMERR:
            time.sleep(RLIMERR.retry / 900)
            return self.case.post_order(ticker, otype, quantity, action, price)

    def __post_big_order(self, ticker, otype, big_q, action, price, maxsize):
        """ Posts an order whose size exceeds quantity limits
            by breaking it into chunks. """

        maxsize = -maxsize if big_q < 0 else maxsize

        # Compute the number of full size orders to submit.
        fullsize_orders = int(big_q // maxsize)

        # Compute the remaining quantity to order
        remainder = int(big_q % maxsize)

        # Dump it.
        results = []

        for i in range(fullsize_orders):
            # Send in the full size orders
            time.sleep(0.1)
            try:
                results.append(self.post_order(ticker, otype, maxsize, action, price))
            except RATE_LIMIT_ERROR as RLIMERR:
                time.sleep(RLIMERR.retry / 900)
                results.append(
                    self.case.post_order(ticker, otype, maxsize, action, price)
                )

        if remainder:
            try:
                res = self.case.post_order(ticker, otype, remainder, action, price)
                results.append(res)
            except RATE_LIMIT_ERROR as RLIMERR:
                time.sleep(RLIMERR.retry / 900)
                results.append(
                    self.case.post_order(ticker, otype, remainder, action, price)
                )

        return results

