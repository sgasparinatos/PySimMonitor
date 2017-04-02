
from websocket import create_connection
ws = create_connection("ws://10.9.0.3:8000/livephone/" + "202010902412869")
print("CONNECTED")
# ws.send("Hello, World")
while True:
    result =  ws.recv()
    print("Received '%s'" % result)

ws.close()