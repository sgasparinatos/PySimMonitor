import configparser
import logging
import signal
import sys
import time
from queue import Queue, Empty
import requests
from declarations import *
from modem import ModemControlThread
from websock import WebSocketThread
from dboperations import *
# import eventlet

class MainProg:
    changes_queue = Queue()
    websock_queue = Queue()
    work = True

    def __init__(self, settings):
        self.modem_thread = ModemControlThread(settings['Modem'], self.changes_queue, self.websock_queue)
        self.modem_thread.setName("MC")

        self.url = "http://" + settings['Server']['url']
        self.ws_url = "ws://" + settings['Server']['url']
        self.imsi = "imsi1"
        create_db(settings['Db'])
        self.dbo = DbOperations(settings['Db'])
        self.rest_fail_time = 0
        self.rest_success_time = 0


    def send_changes(self, changes):
        changes["imsi"] = self.imsi
        try:
            if LOG_REST:
                logging.info("Sending changes " + str(changes))


            req = requests.patch(self.url + PHONE_UPDATE, json=changes, headers=HEADERS, timeout=REQUESTS_TIMEOUT)
            if req.status_code != 200:
                logging.warning("Request FAILED with " + str(req.status_code))
                self.rest_fail_time = time.time()
                return False
            else:
                self.rest_success_time = time.time()
                return True
        except Exception:
            logging.warning("Failed to send changes to server")
            self.rest_fail_time = time.time()
            return False

    def send_full_phone(self):
        try:
            if LOG_REST:
                logging.info("Sending full phone")
            json_data = { 'imsi' : self.imsi }
            req = requests.post(self.url + PHONE_CREATE, json=json_data, headers=HEADERS, timeout=REQUESTS_TIMEOUT)
            if req.status_code != 200:
                logging.warning("Request FAILED with " + str(req.status_code))

        except Exception:
            logging.warning("Failed to send sample phone")


    def store_changes(self, changes):

        timestamp = changes['timestamp']
        for key in changes.keys():
            if key in ('timestamp', 'imsi'):
                continue
            self.dbo.new_change(key, str(changes[key]), timestamp)


    def run(self):

        signal.signal(signal.SIGINT, self.signal_handler)

        # self.enable_logging()

        if self.modem_thread.ready():
            self.modem_thread.start()

            while self.work:
                try:
                    changes = self.changes_queue.get(0)

                    if "imsi" in changes:
                        self.imsi = changes['imsi']
                        logging.info("IMSI :" + self.imsi)
                        self.send_full_phone()

                        if USE_WEBSOCKET:
                            self.websock_thread = WebSocketThread(self.ws_url, self.websock_queue, self.imsi)
                            self.websock_thread.setName("WS")
                            self.websock_thread.start()

                    elif USE_REST:
                        if not self.send_changes(changes):
                            self.store_changes(changes)

                except Empty:
                    pass

                if  time.time() - self.rest_success_time > RETRY_REST_DELAY:
                    count = self.dbo.has_changes()
                    for i in range(count):
                        id, change = self.dbo.get_older_change_rest()
                        if self.send_changes(change):
                            self.dbo.delete_change(id)





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
