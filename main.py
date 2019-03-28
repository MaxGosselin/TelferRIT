"""the telfer trader controller"""
import time

# from algo.bp.bp_producer import ProducerAlgo
from algo.demo_algo import DemoAlgo
from gui.gui_controller import GuiController
from lib.data_recorder import DataRecorder
from lib.case import Case


def start_trader(case, algo):
    """main control loop"""

    gui = GuiController()
    logger = DataRecorder(case)

    while True:
        while case.is_active():
            data = algo.on_update()
            gui.on_update(data)
            logger.on_update()
            time.sleep(0.1)
        print("Case is not active...", end="\r")
        time.sleep(5)  # wait before checiking if active again


def main():
    """define the case, algo, and gui you want to use"""
    case = Case()
    algo = DemoAlgo(case)
    start_trader(case, algo)


if __name__ == "__main__":
    main()
