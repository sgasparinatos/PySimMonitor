from threading import Thread
from declarations import *
# from websocket import create_connection
import logging
from queue import Queue


class WebSocketThread(Thread):

    def __init__(self, ws_url, websock_queue, imsi):
        Thread.__init__(self)
        self.websock_url = ws_url + WEBSOCK_PATH + imsi
        self.websock_queue = websock_queue
        self.work = True



    def stop(self):
        self.work = False

    def run(self):
        print(self.websock_url)
        self.ws = create_connection(self.websock_url)

        while self.work:
            command = self.ws.recv()
            logging.info("GOT command \"" + command + "\"" )
            self.websock_queue.put(command)





if __name__ == '__main__':

    q = Queue()
    wst = WebSocketThread("ws://10.9.0.3:8000", q, "202010902412869")
    wst.start()

    wst.join()