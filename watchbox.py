from logging.config import dictConfig
from flask import request, make_response
import threading
import atexit
import urllib.parse
import uuid, time, sys

minijs = """async function __watchboxpromise__(o,n){return new Promise((t,e)=>{$.post("/watchbox.get.wb",{group:o},function(e){"wb00"==e||("wb11"==e?console.error("[watchbox] not in group "+o):n(e)),t()})})}async function __watchboxdaemon__(o,n,t){for(;;)await watchbox._sleep(100),await __watchboxpromise__(o,n)}const watchbox={_sleep:async function(o){return new Promise(n=>setTimeout(n,o))},join:function(o,n,t=function(){},e=null){return $.post("/watchbox.join.wb",{group:o},function(c){console.log("[watchbox] join response: "+c),t(),__watchboxdaemon__(o,n,t,e)}),!0},publish:function(o,n){$.post("/watchbox.brdcst.wb",{group:n,text:encodeURIComponent(o)},function(o){console.log("[watchbox] message response: "+o)})},send:function(o){$.post("/watchbox.server.wb",{text:encodeURIComponent(o)},function(o){console.log("[watchbox] message response: "+o)})}};"""

class server(object):
  def __init__(self, app):
    self.__clients = {}
    self.__messages = {}

    self.__servermsg = None
    self.__servertimeout = None

    self.logginglevel = 3
    self.timeout = 10
    self.listlimit = 50

    self._app = app

    print(" * Starting watchbox client")
    
    @app.route("/watchbox.<string:mtype>.wb", methods=["GET", "POST"])
    def _watchbox_proc(mtype):
      if mtype == "file":
        return minijs
      return self.__process(request, mtype)

    print(" * Starting timeout thread")
    self.__uthread = threading.Thread(target=self.__userthread)
    self.__uthread.start()
  
  def __log(self, message, level):
    if self.logginglevel >= level:
      print("watchbox : " + message)
    else:
      pass
  
  def __checkcookie(self, rqst):
    clientid = rqst.cookies.get('__wb.client')
    if clientid in self.__clients:
      return clientid
    else:
      return False

  def __publish(self, message, group):
    for item in self.__messages:
      try:
        if len(self.__messages[item][group]) >= self.listlimit:
          #self.__messages[item][group].pop(0)
          pass
        else:
          self.__messages[item][group].append(message)
      except:
        pass

  def __userthread(self):
    while True:
      copy = self.__clients.copy()
      for uid in copy:
        if time.time()-self.__clients[uid]["tm"] > self.timeout:
          self.__remove(uid)
          self.__log("client timed out", 1)
          if not self.__servertimeout == None:
            self.__servertimeout(uid)
      time.sleep(.5)

  def __remove(self, uid):
    if uid in self.__clients:
      del self.__clients[uid]
      del self.__messages[uid]
    else:
      pass
    
  def __process(self, rqst, mtype):
    cokie = self.__checkcookie(rqst)
    if cokie != False:
      self.__clients[cokie]["tm"] = time.time()
    if mtype == "join":
      grup = rqst.form['group']
      self.__log("client joined server '" + grup + "'", 1)
      res = make_response("wb31")
      if cokie == False:
        uid = uuid.uuid4().hex
        res.set_cookie('__wb.client', uid)
        self.__clients[uid] = {"tm":time.time()}
        self.__messages[uid] = {grup:[]}
      else:
        self.__messages[cokie][grup] = []
      return res
    elif mtype == "brdcst":
      grup = rqst.form['group']
      self.__log("client broadcast message to server '" + grup + "'", 3)
      text = urllib.parse.unquote(rqst.form['text'])
      res = make_response("wb21")
      if cokie == False:
        uid = uuid.uuid4().hex
        res.set_cookie('__wb.client', uid)
        self.__clients[uid] = {"tm":time.time()}
        self.__messages[uid] = {}
      else:
        pass
      self.__publish(text, grup)
      return res
    elif mtype == "server":
      text = urllib.parse.unquote(rqst.form['text'])
      if self.__servermsg == None:
        self.__log("tried to send message to server, but server was not watching", 1)
        res = make_response("wb23")
        return res
      else:
        res = make_response("wb21")
        if cokie == False:
          uid = uuid.uuid4().hex
          res.set_cookie('__wb.client', uid)
          self.__clients[uid] = {"tm":time.time()}
          self.__messages[uid] = {}
        else:
          uid = cokie
        self.__servermsg(self, text, uid)
        return res
    elif mtype == "get":
      grup = rqst.form['group']
      self.__log("client got messages from server '" + grup + "'", 3)
      setcokie = False
      if cokie == False:
        uid = uuid.uuid4().hex
        setcokie = True
        self.__clients[uid] = {"tm":time.time()}
        self.__messages[uid] = {}
      else:
        uid = cokie

      if grup in self.__messages[uid]:
        if len(self.__messages[uid][grup]) != 0:
          res = make_response(str(self.__messages[uid][grup].pop(0)))
        else:
          res = make_response("wb00")
      else:
        res = make_response("wb11")
      
      if setcokie:
        res.set_cookie('__wb.client', uid)
      
      return res

  def onMessage(self):
    def decorator(function):
      def magic(selfs, msg, uid):
        selfs.__log("message sent to server", 2)
        function({"msg": msg, "client": uid})
      self.__servermsg = magic
    return decorator

  def onTimeout(self):
    def decorator(function):
      def magic(uid):
        function(uid)
      self.__servertimeout = magic
    return decorator
  
  def publish(self, text, group):
    self.__publish(text, group)

class _watchbox_stream(object):
  def write(text):
    if "watchbox.brdcst.wb" in text or "watchbox.server.wb" in text or "watchbox.join.wb" in text or "watchbox.get.wb" in text or "watchbox.file.wb" in text:
      pass
    else:
      sys.stdout.write(text)
  def flush():
    sys.stdout.flush()

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

# Return Codes:
# wb00: Null
# wb11: Not in group
# wb21: Message sent
# wb23: Server not listining
# wb31: Joined server
# wb41: User not found
