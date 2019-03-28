"""draws the price charts for all the securities in the currently active
case"""
from multiprocessing.connection import Listener
from bokeh.driving import count
from bokeh.layouts import layout, column, gridplot, row, widgetbox
from bokeh.models import ColumnDataSource, CustomJS, Span
from bokeh.plotting import curdoc, figure
from bokeh.models.widgets import Div

import pandas as pd


def receive_data():
    """need to get something like [(ticker, tick, price)]"""
    data = conn.recv()
    # print(data)
    return data


def depth(ticker, books, level=50):
    """Extract the book for our ticker and set up the df the way we want."""

    bids = fill(books.loc[ticker, "BUY"].drop_duplicates("price", "first"), True).head(
        level
    )
    asks = fill(books.loc[ticker, "SELL"].drop_duplicates("price", "last"), False).tail(
        level
    )

    return bids, asks

    # center(bids, asks)


def fill(book, isbid):
    """ clean up the duplicates and fill up the empty spaces. """

    # if it's a bid, drop the first duplicate.
    # if isbid:
    #     clean = book.drop_duplicates('price', 'first')
    # else:
    #     clean = book.drop_duplicates('price', 'last')

    # count how many cents the book covers
    # _range = round(book['price'].max() - book['price'].min(), 2)
    # rungs = int(_range * 100)

    # Get the price range in a list to pass to numpy.linspace to generate our new index
    # pricerange = [book['price'].min(), book['price'].max()]
    pmax = int(book["price"].max() * 100)
    pmin = int(book["price"].min() * 100)

    # print(f"MAX/MIN : {pmax}/{pmin}")
    ix = []
    for i in range(pmin, pmax, 1):
        # print(i/100)
        ix.append(i / 100)

    newind = pd.Index(ix, name="priceline")
    # print(newind)

    # Set the new index and backfill the cvol values
    filled = book.set_index("price").reindex(newind, method="pad")
    # filled['price'] = newind.values

    filled["price"] = newind.get_values()

    # if isbid:
    filled = filled[::-1]

    # print(filled[["price", "cvol"]].to_string())

    return filled


def center(bids, asks):
    """ Modify the last data point to make the two books have symetric price ranges. """

    bidrange = bids["price"].max() - bids["price"].min()
    askrange = asks["price"].max() - asks["price"].min()

    if bidrange > askrange:
        #
        distance = round(bidrange - askrange, 2)
        shim_ask = asks["price"].max() + distance
        asks.iloc[-1, 0] = shim_ask

    elif bidrange < askrange:
        # 00
        distance = round(askrange - bidrange, 2)
        shim_bid = bids["price"].min() - distance
        bids.iloc[-1, 0] = shim_bid

    return bids, asks


@count()
def update(step):
    data = receive_data()

    # print(data["CRZY_candle"], data["TAME_candle"])
    if data["case"]["status"] == "ACTIVE":

        if data["CRZY_candle"]["tick"] is not None:
            color1 = (
                "#fe0000"
                if data["CRZY_candle"]["open"] > data["CRZY_candle"]["close"]
                else "#00fd02"
            )

            CRZY_data = dict(
                tick=[data["CRZY_candle"]["tick"]],
                open=[data["CRZY_candle"]["open"]],
                high=[data["CRZY_candle"]["high"]],
                low=[data["CRZY_candle"]["low"]],
                close=[data["CRZY_candle"]["close"]],
                mid=[(data["CRZY_candle"]["open"] + data["CRZY_candle"]["close"]) / 2],
                height=[
                    max(
                        0.01,
                        abs(data["CRZY_candle"]["open"] - data["CRZY_candle"]["close"]),
                    )
                ],
                color=[color1],
            )

            color2 = (
                "#fe0000"
                if data["TAME_candle"]["open"] > data["TAME_candle"]["close"]
                else "#00fd02"
            )
            TAME_data = dict(
                tick=[data["TAME_candle"]["tick"]],
                open=[data["TAME_candle"]["open"]],
                high=[data["TAME_candle"]["high"]],
                low=[data["TAME_candle"]["low"]],
                close=[data["TAME_candle"]["close"]],
                mid=[(data["TAME_candle"]["open"] + data["TAME_candle"]["close"]) / 2],
                height=[
                    max(
                        0.01,
                        abs(data["TAME_candle"]["open"] - data["TAME_candle"]["close"]),
                    )
                ],
                color=[color2],
            )

            # tick_num = len(CRZY.data['tick'])
            # if tick_num > 0:
            # print(CRZY.data, len(CRZY.data['tick'])) #, tick_num)
            if (
                len(CRZY.data["tick"])
                and CRZY.data["tick"][-1] == data["CRZY_candle"]["tick"]
            ):
                index = max(0, len(CRZY.data["tick"]) - 1)
                rpatches = {
                    "open": [(index, data["CRZY_candle"]["open"])],
                    "high": [(index, data["CRZY_candle"]["high"])],
                    "low": [(index, data["CRZY_candle"]["low"])],
                    "close": [(index, data["CRZY_candle"]["close"])],
                    "color": [(index, color1)],
                    "mid": [
                        (
                            index,
                            (data["CRZY_candle"]["open"] + data["CRZY_candle"]["close"])
                            / 2,
                        )
                    ],
                    "height": [
                        (
                            index,
                            max(
                                0.01,
                                abs(
                                    data["CRZY_candle"]["open"]
                                    - data["CRZY_candle"]["close"]
                                ),
                            ),
                        )
                    ],
                }
                CRZY.patch(rpatches)

                cpatches = {
                    "open": [(index, data["TAME_candle"]["open"])],
                    "high": [(index, data["TAME_candle"]["high"])],
                    "low": [(index, data["TAME_candle"]["low"])],
                    "close": [(index, data["TAME_candle"]["close"])],
                    "color": [(index, color2)],
                    "mid": [
                        (
                            index,
                            (data["TAME_candle"]["open"] + data["TAME_candle"]["close"])
                            / 2,
                        )
                    ],
                    "height": [
                        (
                            index,
                            max(
                                0.01,
                                abs(
                                    data["TAME_candle"]["open"]
                                    - data["TAME_candle"]["close"]
                                ),
                            ),
                        )
                    ],
                }
                TAME.patch(cpatches)
            else:

                CRZY.stream(CRZY_data, 600)
                TAME.stream(TAME_data, 600)

            # else:

            #     CRZY.stream(CRZY_data, 600)
            #     TAME.stream(TAME_data, 600)
        CRZY_price.location = data["CRZY_candle"]["close"]
        TAME_price.location = data["TAME_candle"]["close"]

        CRZY_bid_depth, CRZY_ask_depth = depth("CRZY", data["orderbook"])
        CRZY_bidbook.data = ColumnDataSource._data_from_df(CRZY_bid_depth)
        CRZY_askbook.data = ColumnDataSource._data_from_df(CRZY_ask_depth)
        # print(CRZY_bid_depth, CRZY_ask_depth, CRZY_bidbook.data)

        TAME_bid_depth, TAME_ask_depth = depth("TAME", data["orderbook"])
        TAME_bidbook.data = ColumnDataSource._data_from_df(TAME_bid_depth)
        TAME_askbook.data = ColumnDataSource._data_from_df(TAME_ask_depth)

        if data["tenders"]:
            output = ""

            for tender in data["tenders"]:
                reserve = " " if not tender["biddable"] else " BIDDABLE "
                text = f"<b>{tender['ticker']} {tender['action']}{reserve}TENDER</b>: {tender['quantity']//1000}K @ {tender['price']}<br>"
                # print(text)
                output += text
            div.text = output
        else:
            div.text = f"""Trader PnL : {data['trader']['nlv']}<br>
                            CRZY POSITION: {data['securities'].loc['CRZY', 'position']}<br> 
                            TAME POSITION: {data['securities'].loc['TAME', 'position']}"""

    elif data["case"]["status"] == "STOPPED":
        div.text = f"Round Over, final PnL : {data['trader']['nlv']}"
        CRZY.data = ColumnDataSource(
            dict(
                tick=[], mid=[], height=[], open=[], high=[], low=[], close=[], color=[]
            )
        )
        TAME.data = ColumnDataSource(
            dict(
                tick=[], mid=[], height=[], open=[], high=[], low=[], close=[], color=[]
            )
        )
        CRZY_bidbook.data = ColumnDataSource(dict(price=[], cvol=[]))
        CRZY_askbook.data = ColumnDataSource(dict(price=[], cvol=[]))
        TAME_bidbook.data = ColumnDataSource(dict(price=[], cvol=[]))
        TAME_askbook.data = ColumnDataSource(dict(price=[], cvol=[]))


# Data sources

CRZY = ColumnDataSource(
    dict(tick=[], mid=[], height=[], open=[], high=[], low=[], close=[], color=[])
)
TAME = ColumnDataSource(
    dict(tick=[], mid=[], height=[], open=[], high=[], low=[], close=[], color=[])
)

CRZY_bidbook = ColumnDataSource(dict(price=[], cvol=[]))
CRZY_askbook = ColumnDataSource(dict(price=[], cvol=[]))
TAME_bidbook = ColumnDataSource(dict(price=[], cvol=[]))
TAME_askbook = ColumnDataSource(dict(price=[], cvol=[]))

CRZY_chart = figure(
    plot_height=300,
    plot_width=600,
    y_axis_location="left",
    title="CRZY",
    background_fill_color="#d3d3d3",
)

CRZY_price = Span(location=9, dimension="width", line_width=2, line_color="gold")
CRZY_chart.add_layout(CRZY_price)

CRZY_chart.segment(
    x0="tick", y0="low", x1="tick", y1="high", line_width=1, color="black", source=CRZY
)
CRZY_chart.rect(
    x="tick",
    y="mid",
    width=4,
    height="height",
    line_width=1,
    line_color="black",
    fill_color="color",
    source=CRZY,
)

TAME_chart = figure(
    plot_height=300,
    plot_width=600,
    y_axis_location="left",
    title="TAME",
    background_fill_color="#d3d3d3",
)

TAME_price = Span(location=25, dimension="width", line_width=2, line_color="gold")
TAME_chart.add_layout(TAME_price)

TAME_chart.segment(
    x0="tick", y0="low", x1="tick", y1="high", line_width=2, color="black", source=TAME
)
TAME_chart.rect(
    x="tick",
    y="mid",
    width=4,
    height="height",
    line_width=1,
    line_color="black",
    fill_color="color",
    source=TAME,
)

CRZY_dchart = figure(
    plot_height=175, plot_width=600, y_axis_location="left", title="Orderbook"
)

CRZY_dchart.vbar(x="price", top="cvol", width=0.01, color="green", source=CRZY_bidbook)

CRZY_dchart.vbar(x="price", top="cvol", width=0.01, color="red", source=CRZY_askbook)

TAME_dchart = figure(
    plot_height=175, plot_width=600, y_axis_location="left", title="Orderbook"
)

TAME_dchart.vbar(x="price", top="cvol", width=0.01, color="green", source=TAME_bidbook)

TAME_dchart.vbar(x="price", top="cvol", width=0.01, color="red", source=TAME_askbook)

div = Div(
    text=f"<b>MADE BY UOTTAWA</br>", width=1100, height=200, style={"font-size": "200%"}
)


curdoc().add_root(
    layout(
        gridplot(
            [[CRZY_chart, TAME_chart], [CRZY_dchart, TAME_dchart]],
            toolbar_location=None,
        ),
        widgetbox(div),
    )
)

listener = Listener(("localhost", 6000))
print("Server up and running! Just waiting for you to run the main in another process.\n\n\
     Listening...")
conn = listener.accept()
# Add a periodic callback to be run every X milliseconds
curdoc().add_periodic_callback(update, 250)
