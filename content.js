console.log(window.location.href);

function idFromLink(link) {
  return link.attr('id').split("_")[2];
}

function setTextOf(id, text) {
  var divID = "#newDiv" + id;
  $(divID).text(text);
}

var clicked = function(id) {
  chrome.runtime.sendMessage({type: "unsave", id: id}, function(response) {
    if (response.success) {
      console.log("success transferring ", id);
      setTextOf(id, "Transferred");
    } else {
      console.log("error transferring ", id);
      setTextOf(id, "Error, need to login");
    }
  });
}

var reload = function() {
  $('.thing.saved.link').each(function() {
    var link = $(this);
    var id = idFromLink(link);

    var normalCSS = {
      width: "100px",
      height: "70px",
      float: "left",
    };

    var $e = $("<div>", {
      class: "aClass",
      id: "newDiv" + id,
      text: "Transfer",
    }).css(normalCSS)
      .data("id", id)
      .click(function() { clicked($(this).data('id')) });

    if ($(this).find('.aClass').length == 0) {
      $e.insertAfter($(this).find('.thumbnail'));
    }
  });
}
reload();

var pages = 0;
var pageChecker = setInterval(function() {
  if ($('.NERPageMarker').size() != pages) {
    console.log("new page");
    pages = $('.NERPageMarker').size();
    reload();
  }
}, 2000);