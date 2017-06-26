var r;
var s;

console.log("config: ", config);

function setUser(u, p) {
  r = new window.snoowrap({
	  user_agent: config.reddit.user_agent,
	  client_id: config.reddit.client_id,
	  client_secret: config.reddit.client_secret,
	  username: u,
	  password: p
	});

  console.log("r:" + r.username);
}

function setSource(u, p) {
  s = new window.snoowrap({
    user_agent: config.reddit.user_agent,
	  client_id: config.reddit.client_id,
	  client_secret: config.reddit.client_secret,
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

function unsave(a, id) {
  console.log("unsaving " + id);
  a.get_submission(id).unsave();
}

function download() {
  r = new window.snoowrap({
    user_agent: config.reddit.user_agent,
	  client_id: config.reddit.client_id,
	  client_secret: config.reddit.client_secret,
    username: config.raccount1.username,
    password: config.raccount1.password
  });

  chrome.tabs.getSelected(null, function(tab) {
    chrome.tabs.sendMessage(tab.id, {
      type: "download"
    }, function(response) {
      console.log("downloaded: " + response.downloaded.length);
      for (var i = 0; i < response.downloaded.length; i++) {
        var id = response.downloaded[i];
        unsave(r, id);
      }
    });
  });
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

// https://github.com/not-an-aardvark/snoowrap
// https://github.com/not-an-aardvark/snoowrap/blob/master/src/objects/VoteableContent.js
// *
//   * @summary Saves this Comment or Submission (i.e. adds it to the list at reddit.com/saved)
//   * @returns {Promise} A Promise that fulfills when the request is complete
//   * @example r.get_submission('4e62ml').save()

//   save () {
//     return this._post({uri: 'api/save', form: {id: this.name}}).return(this);
//   }