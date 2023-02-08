from logging.config import dictConfig
from flask import request, make_response, send_file
from datetime import datetime
import threading
import urllib.request
import uuid, time, sys, json
import copy

wburl = 'https://raw.githubusercontent.com/MaceroniMan/Watchbox/main/watchbox.js'
jqueryurl = 'https://code.jquery.com/jquery-3.6.3.min.js'

class server(object):
  def __init__(self, app):
    self.__clients = {}
    self.__messages = {}

    self.__servermsg = None
    self.__servertimeout = None
    self.__serverjoin = None
    self.__serverregister = None

    self.logginglevel = 2

    self.timeout = 10
    self.listlimit = 50
    self.clientlogging = True
    self.ttl = 50

    self._app = app

    print(" * Starting watchbox client")

    # add support for included jquery here

    watchbox_javascript = ""

    with open("watchbox.js", "r") as file:
      watchbox_javascript = file.read()

    @app.route("/watchbox.<string:mtype>.wb", methods=["GET", "POST"])
    def _watchbox_proc(mtype):
      if mtype == "file":
        return watchbox_javascript
      else:
        return self.__process(request, mtype)

    print(" * Starting timeout thread")

    self.__uthreadstop = False

    self.__uthread = threading.Thread(target=self.__userthread)
    self.__uthread.start()
  
  def __log(self, message, level):
    if self.logginglevel >= level:
      now = datetime.now()
      print("watchbox : level " + str(level) + " : " + now.strftime("%Y-%m-%d %H:%M:%S %p") + " : " + message)
    else:
      pass

  def __clientlog(self, application, text, uid):
    with open("client.watchbox.log", "a") as file:
      now = datetime.now()
      file.write("watchbox : " + str(application) + " : " + now.strftime("%Y-%m-%d %H:%M:%S %p") + " : " + uid + " : " + text + "\n")
  
  def __checkcookie(self, rqst):
    clientid = rqst.cookies.get('__wb.client')
    if clientid in self.__clients:
      return clientid
    else:
      return False

  def __publish(self, message, group):
    for client in self.__messages:
      if group in self.__messages[client]:
        if len(self.__messages[client][group]) >= self.listlimit:
          pass # if there are too many messages in the que
        else:
          self.__messages[client][group].append([message, self.ttl*2])

  def __userthread(self):
    while True:
      if self.__uthreadstop:
        break
      
      # disconnect any client
      cpy = copy.deepcopy(self.__clients)
      for uid in cpy:
        if time.time()-self.__clients[uid]["tm"] > self.timeout:
          self.__remove(uid)
          self.__log("client timed out", 2)
          if self.__servertimeout != None:
            self.__servertimeout(uid)
      
      # throw away any old messages
      cpy = copy.deepcopy(self.__messages)
      for client_index in cpy:
        client = cpy[client_index]
        for group_index in client:
          group = client[group_index]
          for message_index in range(len(group)):
            message = group[message_index]
            if message[1] == 0:
              del self.__messages[client_index][group_index][message_index]
            else:
              self.__messages[client_index][group_index][message_index][1] -= 1
      time.sleep(.5)

  def __remove(self, uid):
    if uid in self.__clients:
      del self.__clients[uid]
      del self.__messages[uid]
    else:
      pass
    
  def __process(self, rqst, mtype):
    cookie = self.__checkcookie(rqst)

    if mtype == "register" and cookie == False:
      pass
    elif cookie == False:
      res = make_response("wb41")
      return res
    else:
      self.__clients[cookie]["tm"] = time.time()

    if mtype == "join":
      group = rqst.form['group']
      self.__log("client joined group '" + group + "'", 2)
      res = make_response("wb31")

      # if the client has not joined anything yet
      if cookie in self.__messages:
        self.__messages[cookie][group] = []

      if self.__serverjoin != None: # alert the server of a join
        self.__serverjoin(cookie)
      return res
    elif mtype == "brdcst":
      group = rqst.form['group']
      self.__log("client broadcast message to group '" + group + "'", 3)
      text = urllib.parse.unquote(rqst.form['text'])
      res = make_response("wb21")
      self.__publish(text, group)
      return res
    elif mtype == "server":
      item = json.loads(urllib.parse.unquote(rqst.form['text']))
      if type(item) == list:
        if len(item) == 3:
          if item[0] == "_log_":
            if self.clientlogging:
              res = make_response("wb22")
              self.__clientlog(item[1], item[2], cookie)
              return res
            else:
              res = make_response("wb24")
              return res
          else:
            pass
        else:
          pass
      else:
        if self.__servermsg == None:
          self.__log("client tried to send message to server, but server was not watching", 1)
          res = make_response("wb23")
          return res
        else:
          res = make_response("wb22")
          self.__servermsg(self, item, cookie)
          return res
    elif mtype == "get":
      group = rqst.form['group']
      self.__log("client got messages from server '" + group + "'", 3)


      if group in self.__messages[cookie]:
        if len(self.__messages[cookie][group]) != 0:
          message = self.__messages[cookie][group].pop(0)
          res = make_response(str(message[0]))
        else:
          res = make_response("wb00")
      else:
        res = make_response("wb11")
      
      return res
    elif mtype == "register":
      res = make_response("wb42")

      if cookie == False:
        uid = uuid.uuid4().hex
        res.set_cookie('__wb.client', uid)
        self.__clients[uid] = {"tm":time.time()}
        self.__messages[uid] = {}

        if self.__serverregister != None: # alert the server of a register
          self.__serverregister(uid)

        self.__log("client registered to server", 2)

      return res
  
  def _shutdown(self):
    self.__uthreadstop = True
    self.__uthread.join()

  def _send(self, jsobject, uid, force=False):
    try:
      if force:
        self.__messages[uid]["server"].append(json.dumps(jsobject))
      else:
        if len(self.__messages[uid]["server"]) >= self.listlimit:
          self.__log("list limit reached on client, message not sent", 2)
        else:
          self.__messages[uid]["server"].append(json.dumps(jsobject))
    except KeyError:
      self.__log("client not listing to 'server' group, message not sent", 2)
      

  def onMessage(self):
    def decorator(function):
      def magic(selfs, msg, uid):
        selfs.__log("message sent to server", 3)
        function(_message_object(msg, uid, self))
      self.__servermsg = magic
    return decorator

  def onJoin(self):
    def decorator(function):
      def magic(uid):
        function(uid)
      self.__serverjoin = magic
    return decorator

  def onRegister(self):
    def decorator(function):
      def magic(uid):
        function(uid)
      self.__serverregister = magic
    return decorator

  def onTimeout(self):
    def decorator(function):
      def magic(uid):
        function(uid)
      self.__servertimeout = magic
    return decorator
  
  def publish(self, jsobject, group):
    self.__publish(json.dumps(jsobject), group)


class _watchbox_stream(object):
  def write(text):
    if "watchbox.brdcst.wb" in text or "watchbox.server.wb" in text or "watchbox.join.wb" in text or "watchbox.get.wb" in text or "watchbox.file.wb" in text or "watchbox.register.wb" in text:
      pass
    elif " * Running on " in text:
      sys.stdout.write(text[:-1] + " with WatchBox\n")
    else:
      sys.stdout.write(text)
  def flush():
    sys.stdout.flush()

class _message_object(object):
  def __init__(self, jsonmessage, clientuuid, refself):
    self.msg = jsonmessage # dont need to json.loads here because already done in the 'watchbox.server.wb' function
    self.client = clientuuid
    self.__refself = refself
  def reply(self, jsobject, force=False):
    self.__refself._send(jsobject, self.client, force)

def run(watcher, **kwargs):
  dictConfig({
    'version': 1,
    'formatters': {'default': {
      'format': '%(message)s',
    }},
    'handlers': {'wsgi': {
      'class': 'logging.StreamHandler',
      'stream': 'ext://watchbox._watchbox_stream',
      'formatter': 'default'
    }},
    'root': {
      'level': 'INFO',
      'handlers': ['wsgi']
    }
  })

  watcher._app.run(**kwargs)

  # will run when flask shuts down
  watcher._shutdown()

  # to make the console look nice again
  print("")

# Return Codes:
# wb00: Null
# wb11: Not in group
# wb21: Message sent
# wb22: Server reveived message
# wb23: Server not listining
# wb24: Server rejected message
# wb31: Joined server
# wb41: Not registered
# wb42: Register success
