console.log(window.location.href);

function idFromLink(link) {
  return link.attr('id').split("_")[2];
}

var unsaveButtons = {};
var reload = function() {
  $('.thing.saved.link').each(function() {
    var link = $(this);
    var id = idFromLink(link);
    //var comments = link.find('.bylink.comments')[0];
    var unsave = link.find('.link-unsave-button');
    unsaveButtons[id] = unsave;
  });
};
reload();

var clicked = function(id) {
  chrome.runtime.sendMessage({type: "test", id: id}, function(response) {
    // if success, unsave
  });
}

$('.thing.saved.link').each( function() {
  $(this).click( function() {
    var link = $(this);
    var id = idFromLink(link);
    console.log(id);
    clicked(id);
  });
});

var pages = 0;
var pageChecker = setInterval(function() {
  if ($('.NERPageMarker').size() != pages) {
    console.log("new page");
    pages = $('.NERPageMarker').size();
    reload();
  }
}, 2000);