# Watchbox
A mqtt-like program that runs locally. It containes many features to pritoritize memory over speed or vice a versa.

# Theory
Watchbox is a program that allows many clients to send messages to eachother like mqtt. The server also handles disconnects and controles for all kinds of properties. The client's features contain the ability to auto reconnect as well as a callback for when disconnects occur and when re-connects occur.

# Watchbox Server
To start a watchbox server on your flask app, use `watchbox.server(<app>)`. This will start a watchbox server running on your flask server.

## Running Flask
When running flask, instead of using `app.run` use `watchbox.run(<watchbox app>)`, this will add an extra layer of logging to keep the log clean. All arguments after the 'watchbox app' are passed right into the `app.run`.

### Example

```python
from flask import Flask # Need to get the flask module
import watchbox # Need to get the watchbox module

app = Flask(__main__) # Starting a flask server

watcher = watchbox.server(app) # Adding a watchbox server to the flask server

@app.route("/")
def index():
  return "Watchbox test"

watchbox.run(watcher, host="127.0.0.1", port=1234) # Running the flask server with extra logging to reduce garbage
```

## Sending messages
To send messages to a path, use `<watcher>.publish(<message>, <group>)`. This will send a message to any client that is listening to that group.

### Example
```python
from flask import Flask
import watchbox

app = Flask(__main__)

watcher = watchbox.server(app)

@app.route("/")
def index():
  watcher.publish("person joined", "foo") # Publishes a message to the "foo" group
  return "Watchbox test"


watchbox.run(watcher, host="127.0.0.1", port=1234)
```

## Server callbacks
There are 2 callbacks that the flask server can utilize. One is to get oncomming messages `@<watcher>.onMessage()` and the other to handle when a client disconnects `@<watcher>.onTimeout()`.

### Example
```python
from flask import Flask
import watchbox

app = Flask(__main__)

watcher = watchbox.server(app)

@app.route("/")
def index():
  return "Watchbox test"

@watcher.onMessage()
def msg(message):
  print("Message send: " + message.msg) # Print out the message that was sent to the server
  print("From: " + message.uid) # Print out the uuid of the client that sent the message

@watcher.onTimeout()
def discon(uid):
  print("Client disconnect: " + uid) # Print out the uuid of the client that disconnected

watchbox.run(watcher, host="127.0.0.1", port=1234)
```
## Watcher properties
There are some properties that can be changed to reduce RAM usage or reduce CPU usage. The following properties are listed:
- `<watcher>.logginglevel` **:** This can be any value between 0 and 3
  - `3` **:** All log messages are shown, client server and errors (defualt)
  - `2` **:** Only shows errors and server logs
  - `1` **:** Only shows errors
  - `0` **:** Disables logging
- `<watcher>.timeout` **:** The time before a client is disconnected in seconds, defualt is 10
- `<watcher>.listlimit` **:** The amount of entries that can be qued up for each client before they start replaceing them.
  - Lower values use less ram but there is more of a possability of 'skipping' or missing messages
  - Defualt is 50, the recommended lowest value is 2 to avoid 'skipping'
