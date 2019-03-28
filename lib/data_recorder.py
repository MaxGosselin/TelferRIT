import time
import os, copy
import numpy as np
import pandas as pd
from pandas.io.json import json_normalize


class DataRecorder:
    def __init__(self, case, update_freq=1, base_dir=".\\data\\"):
        self.case = case
        self.rows = []
        self.update_freq = update_freq
        self.session_start = time.strftime("%a%d%b%Y-%H-%M-%S", time.localtime())
        self.path = base_dir
        self.runs = 0
        self.last_time = time.time() - update_freq
        self.first_run = True
        self.last_data = {"tick": 0}
        self.blacklist = []

        # log_file = open("data/logfile.csv", "w")
        # self.csv_writer = csv.writer(log_file)

    def get_data(self):

        ld = self.last_data

        ctick = self.case.get_tick()

        if ctick > ld["tick"]:

            # print(f"PASS :  ctick : {ctick}, 'tick' : {ld['tick']}")
            ld["tick"] = ctick
            ld["nlv"] = self.case.get_nlv()

            ld["securities"] = self.case.get_securities()
            ld["orderbook"] = [
                self.case.get_security_book(ticker)
                for ticker in self.case.get_tickers()
            ]
            ld["orders"] = self.case.get_orders()

            # Enable if your case has tenders
            ld["tenders"] = self.case.get_tenders()

            self.rows.append(copy.deepcopy(ld))

        return ld

    def log_data(self):
        # Update the recording data each tick for the columns in last_data
        self.last_data = self.get_data()

        info = self.case.get_case()
        time_rem = info["ticks_per_period"] - self.last_data["tick"]

        if time_rem <= 1 and info["period"] == info["total_periods"]:
            self.news = self.case.get_news()
            self.candles = self.get_candles()

    def on_update(self):
        if time.time() - self.last_time > self.update_freq:
            self.last_time = time.time()
            self.log_data()

    def get_candles(self):

        candles = []

        for ticker in self.case.tickers:

            try:
                raw = self.case.get_candles(ticker, self.period, 1)

                # print(raw)
                # Reverse the candles so they're ordered first -> last.
                for i in range(len(raw) - 1, 0, -1):
                    cndl = raw[i]

                    cndl["ticker"] = ticker
                    # Calculate the change in price from open to closese.
                    # Rounds to the nearest cent.
                    cndl["delta"] = round((cndl["close"] - cndl["open"]), 3)

                    candles.append(cndl)
            except:
                pass

        candle_frame = pd.DataFrame(candles)
        cols = ["open", "high", "low", "close", "delta"]

        # Don't adjust the frame if it's empty
        if not candle_frame.empty:

            # Reindex the df
            candle_frame = candle_frame.set_index(
                ["ticker", "tick"], drop=False
            ).reindex(columns=cols)

            # Add some additional info to the candle frame like log returns
            candle_frame["log_ret"] = candle_frame.groupby("ticker")["close"].apply(
                lambda x: np.log(x) - np.log(x.shift())
            )

            return candle_frame

        else:
            return candle_frame

    def _force_slowup(self):
        info = self.case.info
        self.news = self.case.get_news()
        self.candles = {}
        for ticker in self.case.get_tickers():
            try:
                tmp = []
                for i in range(info["total_periods"]):
                    tmp += self.case.get_candles(
                        ticker=ticker, period=i + 1, limit=info["ticks_per_period"]
                    )
                self.candles[ticker] = tmp
            except:
                print(f"took a shit recording {ticker}")

    def write_out_data(self):
        if self.rows:
            # Make some room to save
            case_folder = f"{self.case.info['name']}\\"
            folder = f"{case_folder}{self.session_start}"
            os.makedirs(f"{self.path}{folder}", exist_ok=True)

            # Preprocess data and save
            json_normalize(self.rows, "securities", "tick").to_csv(
                f"{self.path}{folder}\\securities_run{self.runs}.csv"
            )
            # pd.DataFrame(self.rows, "orders", "tick").to_csv(
            #     f"{self.path}{folder}\\securities_run{self.runs}.csv"
            # )
            json_normalize(
                self.rows, ["orderbook", ["bids"]], "tick", meta_prefix="round_"
            ).to_csv(f"{self.path}{folder}\\askbook_run{self.runs}.csv")
            json_normalize(
                self.rows, ["orderbook", ["asks"]], "tick", meta_prefix="round_"
            ).to_csv(f"{self.path}{folder}\\bidbook_run{self.runs}.csv")
            pd.DataFrame(self.news).to_csv(
                f"{self.path}{folder}\\news_run{self.runs}.csv"
            )
            json_normalize(self.rows, "tenders").to_csv(
                f"{self.path}{folder}\\tenders_run{self.runs}.csv"
            )

            for ticker, candles in self.candles.items():
                pd.DataFrame(candles).to_csv(
                    f"{self.path}{folder}\\{ticker}_candles_run{self.runs}.csv"
                )

            self._cleanup()

            self.runs += 1
            print(f"Round Saved! \n That was the {self.runs} run this session!")

    def _cleanup(self):

        self.rows = []
        self.last_data = {"tick": 0}
        self.blacklist = []
