var r;
var s;

console.log("config: ", config);

function setUser(u, p) {
  r = new window.snoowrap({
    userAgent: config.reddit.user_agent,
    clientId: config.reddit.client_id,
    clientSecret: config.reddit.client_secret,
    refreshToken: config.reddit.refresh_token,
    username: u,
    password: p
  });

  console.log("r:" + r.username);
}

function setSource(u, p) {
  s = new window.snoowrap({
    userAgent: config.reddit.user_agent,
    clientId: config.reddit.client_id,
    clientSecret: config.reddit.client_secret,
    refreshToken: config.reddit.refresh_token,
    username: u,
    password: p
  });

  console.log("s:" + s.username);
}

function logout() {
  r = null;
}

function logoutSource() {
  s = null;
}

function transferSavedTo(id) {
  if (r != null && s != null) {
    console.log("transferring " + id + " from " + s.username + " to " + r.username);
    r.get_submission(id).save();
    s.get_submission(id).unsave();
    console.log("done");
    return true;
  }
  return false;
}

chrome.runtime.onMessage.addListener(
  function(request, sender, sendResponse) {
    if (request.type == "unsave") {
      if (transferSavedTo(request.id)) {
        sendResponse({type: "unsave", id: request.id, success: true});
      } else {
        sendResponse({type: "unsave", id: request.id, success: false});
      }
    }
  }
);