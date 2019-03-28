"""the GUI controller"""
import time
from multiprocessing.connection import Client


class GuiController:
    """Manages sending data at specified intervals to the connected chart"""

    def __init__(self, update_freq=1):
        self.update_freq = update_freq
        self.last_time = time.time() - update_freq

        # attempt connection to listener aka bokeh chart
        self.conn = None
        try:
            self.conn = Client(("localhost", 6000))
        except ConnectionRefusedError:
            print("No charts connected.")

    def on_update(self, algo_output):
        """if (update_freq) seconds have occured, send the data returned by
        data_getter() to the listening chart"""
        if self.conn and time.time() - self.last_time > self.update_freq:
            self.last_time = time.time()
            self.conn.send(algo_output)

    def close_connection(self):
        """close socket connection"""
        self.conn.send("close")
        self.conn.close()
