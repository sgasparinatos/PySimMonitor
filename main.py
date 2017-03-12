import configparser
import logging
import signal
import sys
import time
from queue import Queue, Empty

import requests

from declarations import *
from modem import ModemControlThread


class MainProg:
    changes_queue = Queue()
    work = True

    def __init__(self, settings):
        self.modem_thread = ModemControlThread(settings['Modem'], self.changes_queue)
        self.modem_thread.setName("MC")
        self.url = settings['Server']['url']
        self.imsi = "imsi1"

    def send_changes(self, changes):
        changes["imsi"] = self.imsi
        try:
            logging.info("Sending changes " + str(changes))
            requests.patch(self.url + PHONE_UPDATE, json=changes, headers=HEADERS)
        except Exception:
            logging.warning("Failed to send changes to server")
        return

    def run(self):

        signal.signal(signal.SIGINT, self.signal_handler)

        # self.enable_logging()

        if self.modem_thread.ready():
            self.modem_thread.start()

            while self.work:
                try:
                    changes = self.changes_queue.get(0)
                    if "imsi" in changes:
                        self.imsi = changes['IMSI']
                        logging.info("IMSI :" + self.imsi)
                    elif USE_REST:
                        self.send_changes(changes)

                except Empty:
                    pass

                time.sleep(0.1)

            self.modem_thread.join()
            logging.info("Exited")

        else:
            logging.fatal("Failed to open serial modem ")

    # noinspection PyUnusedLocal
    def signal_handler(self, event, signal):
        logging.info("CTRL+C , exitting...")
        self.work = False
        self.modem_thread.stop()


def enable_logging():
    # logging.basicConfig(format='%(asctime)s %(threadName)s %(levelname)s: %(message)s', level=logging.INFO)
    logging.basicConfig(format='%(threadName)s %(levelname)s: %(message)s', level=logging.INFO)


def parse_config():
    try:
        config = configparser.ConfigParser()
        config.read('settings.ini')
        return config

    except Exception as ex:
        logging.fatal("Configuration error " + str(ex))
        sys.exit(-1)


if __name__ == '__main__':
    enable_logging()
    settings = parse_config()
    prog = MainProg(settings)
    prog.run()
