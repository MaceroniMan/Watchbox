async function __watchboxpromise__(group, callback) {
  return new Promise((resolve, reject) => {
    $.post("/watchbox.get.wb", {
      "group": group
    },function(data) {
      if (data == "wb00") { }
      else if (data == "wb11") {
        console.error("[watchbox] not in group " + group)
      }
      else {
        callback(data)
      }
      resolve()
    });
  });
}

async function __watchboxdaemon__(group, callback) {
  while (true) {
    await watchbox._sleep(100)
    await __watchboxpromise__(group, callback)
  }
}

const watchbox = {
  _sleep: async function (ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  },
  join: function(group, callback, onjoin=(function(){})) {
    $.post("/watchbox.join.wb", {
      "group": group
    },function(data) {
      console.log("[watchbox] join response: " + data)
      onjoin()
      __watchboxdaemon__(group, callback, onjoin)
    });
    return true
  },
  publish: function(message, group) {
    $.post("/watchbox.brdcst.wb", {
      "group": group,
      "text" : encodeURIComponent(message)
    },function(data) {
      console.log("[watchbox] message response: " + data)
    });
  },
  send: function(message) {
    $.post("/watchbox.server.wb", {
      "text" : encodeURIComponent(message)
    },function(data) {
      console.log("[watchbox] message response: " + data)
    });
  }
}
