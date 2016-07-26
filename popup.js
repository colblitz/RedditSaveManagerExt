document.addEventListener('DOMContentLoaded', function() {
  // add functionality for button
  var button = document.getElementById('login');
  button.addEventListener('click', function() {
    console.log("yeah");
    var username = $('#targetname').val();
    var password = $('#targetpass').val();
    chrome.extension.getBackgroundPage().setUser(username, password);
  }, false);
}, false);
