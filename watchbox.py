from logging.config import dictConfig
from flask import request, make_response
from datetime import datetime
import threading
import urllib.parse
import uuid, time, sys, json

minijs = """var __watchboxvars__={joingroups:[],inited:!1,logginglevel:3,registered:!1,dtime:0,serverlogs:!0,reconnect:function(){},disconnect:function(){}};async function __watchboxdeamon__(){for(;;)if(await watchbox._sleep_(__watchboxvars__.dtime),__watchboxvars__.registered)for(item in __watchboxvars__.joingroups){let o=__watchboxvars__.joingroups[item][0],_=__watchboxvars__.joingroups[item][1];new Promise(function(_,t){$.post("/watchbox.get.wb",{group:o},function(o){_("wb00"==o?"":"wb11"==o?"join":"wb41"==o?"register":JSON.parse(o))}).fail(function(){__watchboxvars__.registered&&(__watchboxvars__.registered=!1,watchbox._log_("disconnected",2),__watchboxvars__.disconnect())})}).then(async function(t){"join"==t?await watchbox._join_(o):""==t||("register"==t?(__watchboxvars__.registered=!1,watchbox._log_("disconnected",2),__watchboxvars__.disconnect()):_(t))},function(o){})}else null!=__watchboxvars__.registered&&watchbox._register_()}const watchbox={_sleep_:async function(o){return new Promise(_=>setTimeout(_,o))},_log_:function(o,_){_<=__watchboxvars__.logginglevel&&(1==_?console.error("[watchbox] "+o):console.log("[watchbox] [level "+_+"] "+o),__watchboxvars__.serverlogs&&watchbox.send(["_log_","internals",o],!0))},_register_:async function(){for(__watchboxvars__.registered=null;!__watchboxvars__.registered;){await watchbox._sleep_(1e3);var o=new Promise(function(o,_){$.post("/watchbox.register.wb",{},function(_){"wb42"==_?o(!0):"wb41"==_&&o(!1)}).fail(function(){o(!1)})});await o.then(function(o){o?(watchbox._log_("connected",2),__watchboxvars__.reconnect(),__watchboxvars__.registered=!0):__watchboxvars__.registered=null},function(o){})}},_join_:async function(o){$.post("/watchbox.join.wb",{group:o},function(_){watchbox._log_("join response: "+_,2),watchbox._log_("from group: "+o,3)})},init:function(o=100,_=3,t=function(){},e=function(){}){__watchboxdeamon__(),__watchboxvars__.dtime=o,__watchboxvars__.disconnect=t,__watchboxvars__.reconnect=e,__watchboxvars__.logginglevel=_,__watchboxvars__.inited=!0},join:function(o,_,t=function(){}){__watchboxvars__.inited?(__watchboxvars__.joingroups.push([o,_]),t()):watchbox._log_("watchbox not inited, use 'watchbox.init'",1)},publish:function(o,_){__watchboxvars__.inited?"server"==_?watchbox._log_("cannot send messages to locked group",1):$.post("/watchbox.brdcst.wb",{group:_,text:encodeURIComponent(JSON.stringify(o))},function(o){watchbox._log_("message response: "+o,3)}):watchbox._log_("watchbox not inited, use 'watchbox.init'",1)},send:function(o,_){__watchboxvars__.inited?$.post("/watchbox.server.wb",{text:encodeURIComponent(JSON.stringify(o))},function(o){_?"wb24"==o&&(__watchboxvars__.serverlogs=!1):watchbox._log_("message response: "+o,3)}):watchbox._log_("watchbox not inited, use 'watchbox.init'",1)}};"""

class server(object):
  def __init__(self, app):
    self.__clients = {}
    self.__messages = {}

    self.__servermsg = None
    self.__servertimeout = None
    self.__serverjoin = None
    self.__serverregister = None

    self.logginglevel = 3
    self.timeout = 10
    self.listlimit = 50
    self.clientlogging = True

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
    for item in self.__messages:
      try:
        if len(self.__messages[item][group]) >= self.listlimit:
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
          self.__log("client timed out", 2)
          if self.__servertimeout != None:
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

    if mtype == "register" and cokie == False:
      pass
    elif cokie == False:
      res = make_response("wb41")
      return res
    else:
      self.__clients[cokie]["tm"] = time.time()

    if mtype == "join":
      grup = rqst.form['group']
      self.__log("client joined group '" + grup + "'", 2)
      res = make_response("wb31")
      self.__messages[cokie][grup] = []
      if self.__serverjoin != None: # alert the server of a join
        self.__serverjoin(cokie)
      return res
    elif mtype == "brdcst":
      grup = rqst.form['group']
      self.__log("client broadcast message to group '" + grup + "'", 3)
      text = urllib.parse.unquote(rqst.form['text'])
      res = make_response("wb21")
      self.__publish(text, grup)
      return res
    elif mtype == "server":
      item = json.loads(urllib.parse.unquote(rqst.form['text']))
      if type(item) == list:
        if len(item) == 3:
          if item[0] == "_log_":
            if self.clientlogging:
              res = make_response("wb22")
              self.__clientlog(item[1], item[2], cokie)
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
          self.__servermsg(self, item, cokie)
          return res
    elif mtype == "get":
      grup = rqst.form['group']
      self.__log("client got messages from server '" + grup + "'", 3)

      if grup in self.__messages[cokie]:
        if len(self.__messages[cokie][grup]) != 0:
          res = make_response(str(self.__messages[cokie][grup].pop(0)))
        else:
          res = make_response("wb00")
      else:
        res = make_response("wb11")
      
      return res
    elif mtype == "register":
      res = make_response("wb42")

      if cokie == False:
        uid = uuid.uuid4().hex
        res.set_cookie('__wb.client', uid)
        self.__clients[uid] = {"tm":time.time()}
        self.__messages[uid] = {}

        if self.__serverregister != None: # alert the server of a register
          self.__serverregister(uid)

        self.__log("client registered to server", 2)

      return res

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
    elif text.startswith(" * Running on http"):
      indexoftext = text.find("(Press CTRL+C to quit)")
      sys.stdout.write(text[:indexoftext] + "with WatchBox (Press CTRL+C twice to quit)\n")
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
