var s;
var t;

console.log("config: ", config);

function setup() {
  console.log("setting up source");
  s = new window.snoowrap({
    userAgent: config.raccountS.user_agent,
    clientId: config.raccountS.client_id,
    clientSecret: config.raccountS.client_secret,
    refreshToken: config.raccountS.refresh_token,
    username: config.raccountS.username,
    password: config.raccountS.password
  });

  console.log("setting up target");
  t = new window.snoowrap({
    userAgent: config.raccountT.user_agent,
    clientId: config.raccountT.client_id,
    clientSecret: config.raccountT.client_secret,
    refreshToken: config.raccountT.refresh_token,
    username: config.raccountT.username,
    password: config.raccountT.password
  });
}

function transferSavedTo(id) {
  if (s == null || t == null) {
    setup();
  }

  console.log("transferring " + id);

  t.getSubmission(id).save().then(console.log("saved"));
  s.getSubmission(id).unsave().then(console.log("unsaved"));

  console.log("done");
  return true;
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