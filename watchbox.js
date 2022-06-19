var __watchboxvars__ = {
  "joingroups" : [],
  "inited" : false,
  "logginglevel" : 3,
  "registered" : false,
  "dtime" : 0,
  "serverlogs" : true,
  "reconnect" : (function(){}),
  "disconnect" : (function(){}),
}

async function __watchboxdeamon__() {
  while (true) {
    await watchbox._sleep_(__watchboxvars__.dtime)
    if (__watchboxvars__.registered) {
      for (item in __watchboxvars__["joingroups"]) {
        let group = __watchboxvars__["joingroups"][item][0]
        let clb = __watchboxvars__["joingroups"][item][1]
        var prom = new Promise(function(resolve, reject) {
          $.post("/watchbox.get.wb", {
            "group": group
          },function(data) {
            if (data == "wb00") {
              resolve("")
            }
            else if (data == "wb11") {
              resolve("join")
            }
            else if (data == "wb41") {
              resolve("register")
            }
            else {
              resolve(JSON.parse(data))
            }
          }).fail(function(){
            if (__watchboxvars__.registered) {
              __watchboxvars__.registered = false
              watchbox._log_("disconnected", 2)
              __watchboxvars__.disconnect()
            }
          });
        }); // end of promise
        prom.then(
          async function(value) {
            if (value == "join") {
              await watchbox._join_(group)
            }
            else if (value == "") {}
            else if (value == "register") {
              __watchboxvars__.registered = false
              watchbox._log_("disconnected", 2)
              __watchboxvars__.disconnect()
            }
            else {clb(value)}
         }, function(error) {}
        );
      } //
    }
    else {
      if (__watchboxvars__.registered != null) {
        watchbox._register_()
      }
    }
  }
}

const watchbox = {
  _sleep_: async function (ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  },

  _log_: function(text, number) {
    if (number <= __watchboxvars__.logginglevel) {
      if (number == 1) {
        console.error("[watchbox] " + text)
      }
      else {
        console.log("[watchbox] [level " + number + "] " + text)
      }
      if (__watchboxvars__.serverlogs) {
        watchbox.send(["_log_", "internals", text], true)
      }
    }
  },

  _register_: async function() {
    __watchboxvars__.registered = null
    while (!__watchboxvars__.registered) {
      await watchbox._sleep_(1000)
      var prom = new Promise(function(resolve, reject) {
        $.post("/watchbox.register.wb", {}, function(data) {
          if (data == "wb42") {
            resolve(true)
          }
          else if (data == "wb41") {
            resolve(false)
          }
        }).fail(function(){resolve(false)});
      });
      await prom.then(
        function(value) {
          if (value) {
            watchbox._log_("connected", 2)
            __watchboxvars__.reconnect()

            __watchboxvars__.registered = true
          }
          else {
            __watchboxvars__.registered = null
          }
       }, function(error) {}
      );
    }
  },

  _join_: async function(group) {
    $.post("/watchbox.join.wb", {
      "group": group
    },function(data) {
      watchbox._log_("join response: " + data, 2)
      watchbox._log_("from group: " + group, 3)
    });
  },

  init: function(dtime=100, logginglevel=3, disconnect=(function(){}), reconnect=(function(){})) {
    __watchboxdeamon__()
    __watchboxvars__.dtime = dtime
    __watchboxvars__.disconnect = disconnect
    __watchboxvars__.reconnect = reconnect
    __watchboxvars__.logginglevel = logginglevel
    __watchboxvars__.inited = true
  },
  join: function(group, callback, onjoin=(function(){})) {
    if (__watchboxvars__.inited) {
      __watchboxvars__["joingroups"].push([group, callback])
      onjoin()
    }
    else {
      watchbox._log_("watchbox not inited, use 'watchbox.init'", 1)
    }
  },
  publish: function(message, group) {
    if (__watchboxvars__.inited) {
      if (group == "server") {
        watchbox._log_("cannot send messages to locked group", 1)
      }
      else {
        $.post("/watchbox.brdcst.wb", {
          "group": group,
          "text" : encodeURIComponent(JSON.stringify(message))
        },function(data) {
          watchbox._log_("message response: " + data, 3)
        });
      }
    }
    else {
      watchbox._log_("watchbox not inited, use 'watchbox.init'", 1)
    }
  },
  send: function(message, _logs_) {
    if (__watchboxvars__.inited) {
      $.post("/watchbox.server.wb", {
        "text" : encodeURIComponent(JSON.stringify(message))
      },function(data) {
        if (!_logs_) {
          watchbox._log_("message response: " + data, 3)
        }
        else {
          if (data == "wb24") {
            __watchboxvars__.serverlogs = false
          }
        }
      });
    }
    else {
      watchbox._log_("watchbox not inited, use 'watchbox.init'", 1)
    }
  }
}
