document.addEventListener('DOMContentLoaded', function() {
  // add functionality for button
  var button = document.getElementById('login');
  button.addEventListener('click', function() {
    var username = $('#targetname').val();
    var password = $('#targetpass').val();
    chrome.extension.getBackgroundPage().setUser(username, password);
  }, false);

  var button2 = document.getElementById('logout');
  button2.addEventListener('click', function() {
    chrome.extension.getBackgroundPage().logout();
  }, false);

  var button3 = document.getElementById('login2');
  button3.addEventListener('click', function() {
    var username = $('#sourcename').val();
    var password = $('#sourcepass').val();
    chrome.extension.getBackgroundPage().setSource(username, password);
  }, false);

  var button4 = document.getElementById('logout2');
  button4.addEventListener('click', function() {
    chrome.extension.getBackgroundPage().logoutSource();
  }, false);

  var button5 = document.getElementById('download');
  button5.addEventListener('click', function() {
  	chrome.extension.getBackgroundPage().download();
  }, false);

}, false);
