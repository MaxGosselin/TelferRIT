"""
The Rotman Interactive Trader (RIT) allows users to query for market data and
submit trading instructions through a REST API.
The API is documented at http://rit.306w.ca/RIT-REST-API/
"""
import requests

API_KEY = {"X-API-key": "MAXMAXMAX"}
BASE = "http://localhost:9999/v1/"


class API_KEY_ERROR(Exception):
    def __init__(self, response):
        response = response.json()
        self.code = response["code"]
        self.message = response["message"]
        self.outputs = [
            "An operation failed with code: %s" % self.code,
            "Error Message: %s" % self.message,
            "Your API key: %s" % BASE,
        ]


class RESPONSE_ERROR(Exception):
    def __init__(self, response):
        self.code = response.status_code
        response = response.json()
        self.code_detail = response["code"]
        self.message = response["message"]
        self.outputs = [
            "An operation failed with code: %i (%s)" % (self.code, self.code_detail),
            "Error Message: %s" % self.message,
        ]


class RATE_LIMIT_ERROR(Exception):
    def __init__(self, response):
        self.code = response.status_code
        response = response.json()
        print(response)
        self.code_detail = response["code"]
        self.message = response["message"]
        self.retry = response["wait"]
        self.outputs = [
            "An operation failed with code: %i (%s)" % (self.code, self.code_detail),
            "Error Message: %s" % self.message,
        ]


class Case:
    """ Represents the currently running RIT Case """

    def __init__(self, user_supplied_port=None):
        """we use a session to reuse the TCP connection
        makes things faster :)"""

        self.session = requests.Session()
        self.session.headers = API_KEY
        self.info = self.get_case()
        self.tickers = self.get_tickers()
        self.trader = self.get_trader()

    def is_active(self):
        """check whether the case is active"""
        return self.get_case()["status"] == "ACTIVE"

    def get_tickers(self):
        """get the tickers for the case"""
        return [x["ticker"] for x in self.get_securities()]

    def submit_get_request(self, endpoint):
        """submit get request to RIT api and return the json"""
        response = self.session.get(BASE + endpoint)

        if response.ok:
            return response.json()
        elif response.status_code == 401:
            raise API_KEY_ERROR(response)
        elif response.status_code == 429:
            raise RATE_LIMIT_ERROR(response)
        else:
            raise RESPONSE_ERROR(response)

    def delete(self, endpoint):
        """submit delete request to RIT api and return the json"""
        response = self.session.delete(BASE + endpoint)
        response.raise_for_status()

    def submit_post_request(self, endpoint):
        """submit post request to RIT api and return the json"""
        response = self.session.post(BASE + endpoint)

        if response.ok:
            return response.json()
        elif response.status_code == 401:
            raise API_KEY_ERROR(response)
        elif response.status_code == 429:
            raise RATE_LIMIT_ERROR(response)
        else:
            raise RESPONSE_ERROR(response)

    # GETS

    def get_case(self):
        """Gets information about the current case."""
        return self.submit_get_request("case")

    def get_tick(self):
        return self.get_case()["tick"]

    def get_trader(self):
        """Gets information about the currently signed in trader."""
        return self.submit_get_request("trader")

    def get_nlv(self):
        """Returns just the tick from the current case."""
        return self.get_trader()["nlv"]

    def get_limits(self):
        return self.submit_get_request("limits")

    def get_assets(self):
        return self.submit_get_request("assets")

    def get_securities(self):
        return self.submit_get_request("securities")

    def get_orders(self):
        return self.submit_get_request("orders")

    def get_tenders(self):
        return self.submit_get_request("tenders")

    def get_news(self, since=0, limit=100):
        endpoint = f"news?since={since}&limit={limit}"
        return self.submit_get_request(endpoint)

    def get_security_book(self, ticker, limit=100):
        endpoint = f"securities/book?ticker={ticker}&limit={limit}"
        return self.submit_get_request(endpoint)

    def get_candles(self, ticker, period=1, limit=1):
        endpoint = f"securities/history?ticker={ticker}&period={period}&limit={limit}"
        return self.submit_get_request(endpoint)

    # DELETES

    def delete_order(self, order_id):
        return self.delete(f"orders/{order_id}")

    def delete_tender(self, tender_id):
        return self.delete(f"tenders/{tender_id}")

    # POSTS

    def post_tender(self, tender_id):
        return self.submit_post_request(f"tenders/{tender_id}")

    def post_order(self, ticker, otype, quantity, action, price=None, dry=0):
        endpoint = f"orders?ticker={ticker}&type={otype}&quantity={quantity}&price={price}&action={action}&dry_run={dry}"
        return self.submit_post_request(endpoint)

    def post_cancel_expression(self, query):
        return self.submit_post_request(f"commands/cancel?query='{query}'")
