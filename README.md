# Watchbox
A mqtt-like program that runs locally. It containes many features to pritoritize memory over speed or vice a versa.

# Watchbox Server
To start a watchbox server on your flask app, use `watchbox.server(<app>)`. This will start a watchbox server running on your flask server.

## Running flask
When running flask, instead of using `app.run` use `watchbox.run(<watchbox app>)`, this will add an extra layer of logging to keep your log clean. All arguments after the 'watchbox app' are passed right into the `app.run`.

### Example

```python
from flask import Flask # We need to get the flask module
import watchbox # We need to get the watchbox module

app = Flask(__main__) # Starting a flask server

watcher = watchbox.server(app) # Adding a watchbox server to the flask server

@app.route("/")
def index():
  return "Watchbox test"

watchbox.run(watcher, host="127.0.0.1", port="1234") # Running the flask server with extra logging to reduce garbage
```
