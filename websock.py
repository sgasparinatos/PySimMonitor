from threading import Thread
from declarations import *
from websocket import create_connection, WebSocketTimeoutException
import logging
from queue import Queue, Empty
import time
from declarations import *


class WebSocketThread(Thread):

    def __init__(self, ws_url, queue_cmd, queue_res, imsi):
        Thread.__init__(self)
        self.websock_url = ws_url + WEBSOCK_PATH + imsi
        self.queue_cmd = queue_cmd
        self.queue_res = queue_res
        self.work = True



    def stop(self):
        self.work = False

    def run(self):

        while self.work:
            try:
                self.ws = create_connection(self.websock_url)
                self.ws.settimeout(1)
                if LOG_WEBSOCKET:
                    logging.info("Connected to " + self.websock_url)
            except Exception:
                logging.warning("Failed to connect to websocket")
                time.sleep(1)
                continue

            while self.work:
                try:
                    command = self.ws.recv()
                    logging.info("GOT command \"" + command + "\"" )
                    self.queue_cmd.put(command)
                    res = self.queue_res.get(3)
                    logging.info("SENDING response \"" + res +"\"")
                    self.ws.send(res)

                except Empty:
                    self.ws.send("NO RESPSONSE")
                    continue

                except WebSocketTimeoutException:
                    continue

                except Exception:
                    logging.warning("Error receiving data ... disconnect.")
                    self.ws.close()
                    break





if __name__ == '__main__':


    logging.basicConfig(format='%(threadName)s %(levelname)s: %(message)s', level=logging.INFO)
    qr = Queue()
    qc = Queue()
    wst = WebSocketThread("ws://10.9.0.3:8000", qc, qr, "204043255462105")
    wst.start()
    while True:
        c=qc.get()
        qr.put("test")
        print(c)

    wst.join()