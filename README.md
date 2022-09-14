# Watchbox
A mqtt-like program that runs locally. It has a flask-python server and a javascript client. It containes many features to pritoritize memory over speed or vice a versa.

# Installation
The installation process is very easy, make sure the `watchbox.py` file is in the same directory as the server, then `import watchbox` will finish it off.

Using watchbox on the javascript client is a bit trickier, the client script is stored with the `.py` file, so all that it needed is a simple `<script src="/watchbox.file.wb"></script>`

# Theory
Watchbox is a program that allows many clients to send messages to eachother like mqtt. The server also handles disconnects and controles for all kinds of properties. The client's features contain the ability to auto reconnect as well as a callback for when disconnects occur and when re-connects occur.

-----------

# Watchbox Server
To start a watchbox server on your flask app, use `watchbox.server(<app>)`. This will start a watchbox server running on your flask server.

## Running Flask
When running flask, instead of using `app.run` use `watchbox.run(<watchbox app>)`, this will add an extra layer of logging to keep the log clean. All arguments after the 'watchbox app' are passed right into the `app.run`.

### Example

```python
from flask import Flask # need to get the flask module
import watchbox # need to get the watchbox module

app = Flask(__name__) # starting a flask server

watcher = watchbox.server(app) # adding a watchbox server to the flask server

@app.route("/")
def index():
  return "Watchbox test"

watchbox.run(watcher, host="127.0.0.1", port=1234) # running the flask server with extra logging to reduce garbage
```

## Sending messages
To send messages to a path, use `<watcher>.publish(<message>, <group>)`. This will send a message to any client that is listening to that group.

### Example
```python
from flask import Flask
import watchbox

app = Flask(__name__)

watcher = watchbox.server(app)

@app.route("/")
def index():
  watcher.publish("person joined", "foo") # publishes a message to the "foo" group
  return "Watchbox test"


watchbox.run(watcher, host="127.0.0.1", port=1234)
```

## Server callbacks
There are 3 callbacks that the flask server can utilize. One is to get oncomming messages `@<watcher>.onMessage()` another to handle when a client disconnects `@<watcher>.onTimeout()` and the last to handle when a client reconnects `@<watcher>.onJoin()`.

The `@<watcher>.onMessage()` callback passes a `_message_object`, this object has three methods:
 - `.msg` is the text that the client sent to the server
 - `.uid` is the unique identifier of the client that sent the message
 - `.reply(<message>, <force=False>)` this will add the `<message>` JSON right to the clients que, if `<force>` is `true` this the function will ignore the `listlimit` function and forcefully add the message to the que

*NOTE: These callbacks do not actually interfere with the watchbox core, the core stays the same. These are async functions called when something happens.*

### Example
```python
from flask import Flask
import watchbox

app = Flask(__name__)

watcher = watchbox.server(app)

@app.route("/")
def index():
  return "Watchbox test"

@watcher.onMessage()
def msg(message):
  print("Message send: " + message.msg) # prints out the message that was sent to the server
  print("From: " + message.uid) # prints out the uuid of the client that sent the message
  message.reply("Sending a message back") # this adds a message directly to the clients que

@watcher.onTimeout()
def discon(uid):
  print("Client disconnect: " + uid) # prints out the uuid of the client that disconnected

@watcher.onJoin()
def connect(uid):
  print("Client connect: " + uid) # prints out the uuid of the client that connected

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

# Watchbox JavaScript Client
To initilize watchbox on a JavaScript client, use `watchbox.init()`, this will start the watchbox background process.

## Receiving Messages
To receive messages with the JavaScript client, use the function `watchbox.join(<group>, <message callback>)`. This will join the group and will run the callback on every message. There is a block in place that will prevent more than one callback being called at one time, but the client will not wait for the callback to end before it calls the next one.

### Example
```javascript
watchbox.init() // sets up the watchbox client

watchbox.join("foo", function(message){
  console.log("Message reveived: " + message) // this will run every time a message is received
})
```

## Sending Messages (Clients)
To send messages to other clients use `watchbox.publish(<message>, <group>)`, this will send the message to all other members in the group that was defined.

### Example
```javascript
watchbox.init()

watchbox.join("foo", function(message){
  watchbox.publish("im here!", "bar") // it does not have join a group to publish to one
})
```

## Sending Messages (Server)
To send messages directly to the server use `watchbox.send(<message>)`, this will send the message directly to the server for it to parse using its `onMessage` decorator.

### Example
```javascript
watchbox.init()

watchbox.send("player 1 joined") // this will send a message directly to the server
```

## Extra Arguments
There are some extra argument that can be set on the client, all of them are listed below:
- `watchbox.init(<dtime>, <disconnect>, <reconnect>)` contains 3 arguments
  - `dtime` **:** this is the time between loops of the background process in milliseconds, the lower the number the higher the preformance (defualt is 100)
  - `disconnect` **:** this is the function that is called when the watchbox client loses the connection with the server (defualt is blank function)
  - `reconnect` **:** this is the function that is called when the watchbox client re-gains a connection with the server (defualt is blank function)
- `watchbox.join(<onjoin>)` contains 1 argument
  - `onjoin` **:** this is called when the join function finishes (defualt is blank function)
