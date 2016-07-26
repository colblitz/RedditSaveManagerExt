var username = "";
var password = "";

function setUser(u, p) {
  username = u;
  password = p;
  console.log(username + " " + password);
}

chrome.runtime.onMessage.addListener(
  function(request, sender, sendResponse) {
    console.log(request);
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