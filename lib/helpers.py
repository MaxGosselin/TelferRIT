"""
library of helper functions for the algos
add your spaghetti code here :)
"""

import pandas as pd


def get_ohlc(case):
    """get open high low close for the first ticker on a case
    this is just an example template to follow"""
    ticker = case.get_tickers()[0]  # get the first ticker
    data = case.get_securities_history(ticker)
    return data["open"], data["high"], data["low"], data["close"]


def cvols(book):
    """ Adds the cumulative volume data to the book. """
    bcv = 0
    acv = 0
    last_price = 00.00
    count = 1

    for order in book["asks"] + book["bids"]:

        if order["action"] == "BUY":
            bcv += order["quantity"] - order["quantity_filled"]
            order["cvol"] = bcv

        else:
            acv += order["quantity"] - order["quantity_filled"]
            order["cvol"] = acv

        if order["price"] == last_price:
            count += 1
        else:
            count = 1

        order["count"] = count

        last_price = order["price"]

    return book


def unpack_books(books):

    orders = []

    for ticker in books.keys():
        for side in ["bids", "asks"]:
            for order in books[ticker][side]:
                orders.append(order)

    return orders
