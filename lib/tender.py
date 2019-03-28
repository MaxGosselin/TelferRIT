# Author : Max Gosselin
# Copyright TRITCT2019

from time import sleep
import pandas as pd
import numpy as np
import math
from scipy.stats import norm


"""
TODO: add bidding functionality for reserve and winner take alls.
"""


class Tender:
    """ Interface for dealing with tenders. """

    def __init__(self, raw_tender):
        """ Construct the tender object. """

        self.t_id = raw_tender["tender_id"]
        self.period = raw_tender["period"]
        self.arrival = raw_tender["tick"]
        self.expiry = raw_tender["expires"]
        self.caption = raw_tender["caption"]
        self.quantity = raw_tender["quantity"]
        self.action = raw_tender["action"]
        self.biddable = not raw_tender["is_fixed_bid"]
        self.price = raw_tender["price"]
        self.ticker = raw_tender["ticker"]

    def get_vwap(self, book):
        """ Get the Volume Weighted Average Price of a tender. """

        # Select the rows with a cvol less than the tender volume.
        levels = book[book["cvol"].lt(self.quantity)]
        value = (
            levels["price"] * (levels["quantity"] - levels["quantity_filled"])
        ).sum()

        # Don't forget that you could miss a little after the cutoff.
        missing_level = min(len(book) - 1, len(levels))
        missing_quantity = self.quantity - levels["cvol"].max()
        missing_value = book.iloc[missing_level, 4] * missing_quantity
        # print(f"Missing Value: {missing_value}")

        # Compute the vwap
        return (value + missing_value) / self.quantity

    def get_profit(self):
        """ Compute the profit of the tender. """

        # Gotta do something about bid tenders
        if not self.biddable:
            if self.action == "BUY":
                return (self.vwap - self.price) * self.quantity
            else:
                return (self.price - self.vwap) * self.quantity

        else:
            print("Biddable: what do??")

    def update(self, book):
        """ Update the vwap and recompute the profit. """

        self.vwap = self.get_vwap(book)
        self.profit = self.get_profit()
