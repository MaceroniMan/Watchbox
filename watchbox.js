var __watchboxvars__ = {
  "connected" : true,
  "joingroups" : [],
  "inited" : false
}

async function __watchboxdeamon__(dtime, disconnect, reconnect) {
  let connected = true
  let time = dtime
  while (true) {
    await watchbox._sleep(time)
    for (item in __watchboxvars__["joingroups"]) {
      let group = __watchboxvars__["joingroups"][item][0]
      let clb = __watchboxvars__["joingroups"][item][1]
      var prom = new Promise(function(resolve, reject) {
        $.post("/watchbox.get.wb", {
          "group": group
        },function(data) {
          if (connected) {}
          else {
            connected = true
            time = dtime
            console.log("[watchbox] connected")
            reconnect()
          }
          if (data == "wb00") {
            resolve("")
          }
          else if (data == "wb11") {
            resolve("join")
          }
          else {
            resolve(data)
          }
        }).fail(function(){
          if (connected) {
            time = 1000
            connected = false
            console.log("[watchbox] disconnected")
            disconnect()
          }
        });
      });
      prom.then(
        async function(value) {
          if (value == "join") {
            await watchbox._join(group)
          }
          else if (value == "") {}
          else {clb(value)}
       }, function(error) {}
      );
    }
  }
}

const watchbox = {
  _sleep: async function (ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  },
  init: function(dtime=100, disconnect=(function(){}), reconnect=(function(){})) {
    __watchboxdeamon__(dtime, disconnect, reconnect)
    __watchboxvars__.inited = true
  },
  _join: async function(group) {
    $.post("/watchbox.join.wb", {
      "group": group
    },function(data) {
      console.log("[watchbox] join response: " + data)
    });
  },
  join: function(group, callback, onjoin=(function(){})) {
    if (__watchboxvars__.inited) {
      __watchboxvars__["joingroups"].push([group, callback])
      onjoin()
    }
    else {
      console.error("[watchbox] watchbox not inited, use 'watchbox.init'")
    }
  },
  publish: function(message, group) {
    if (__watchboxvars__.inited) {
      $.post("/watchbox.brdcst.wb", {
        "group": group,
        "text" : encodeURIComponent(message)
      },function(data) {
        console.log("[watchbox] message response: " + data)
      });
    }
    else {
      console.error("[watchbox] watchbox not inited, use 'watchbox.init'")
    }
  },
  send: function(message) {
    if (__watchboxvars__.inited) {
      $.post("/watchbox.server.wb", {
        "text" : encodeURIComponent(message)
      },function(data) {
        console.log("[watchbox] message response: " + data)
      });
    }
    else {
      console.error("[watchbox] watchbox not inited, use 'watchbox.init'")
    }
  }
}
