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

// Not used

var actuallyDownload = function(url, name) {
  var a = $("<a>")
    .attr("href", url)
    .attr("download", name)
    .appendTo("body");

  a[0].click();
  a.remove();
}

var download = function() {
  console.log("downloading");
  var ids = [];
  $('.thing.saved.link').each(function() {
    var link = $(this);
    var id = idFromLink(link);
    var url = $(link.find('a.title')[0]).attr('href');
    
    if (url.includes("imgur")) {
      if (url.includes(".gifv")) {
        url = url.replace(".gifv", ".mp4")
        var thing = url.split("/").slice(-1)[0];
        actuallyDownload(url, thing);
        ids.push(id);
      } else if (url.includes("i.imgur.com")) {
        var thing = url.split("/").slice(-1)[0];
        actuallyDownload(url, thing);
        ids.push(id);
      } else if (url.includes("/a/")) {
        console.log(url);
        // var thing = url.split("/").slice(-1)[0] + ".zip";
        // url = url + "/zip";
        // actuallyDownload(url, thing);
        // ids.push(id);
      } else if (url.includes("m")) {
        url = url.replace("m.imgur", "i.imgur") + ".jpg";
        var thing = url.split("/").slice(-1)[0];
        actuallyDownload(url, thing);
        ids.push(id);
      }
    } else if (url.includes("gfycat")) {
      url = url.replace("gfycat.com", "zippy.gfycat.com") + ".webm";
      var thing = url.split("/").slice(-1)[0];
      actuallyDownload(url, thing);
      ids.push(id);
    } else if (url.endsWith(".jpg") || url.endsWith(".gif") || url.endsWith(".png")) {
      var thing = url.split("/").slice(-1)[0];
      actuallyDownload(url, thing);
      ids.push(id);  
    } else {
      console.log(url);
    }
  });
  return ids;
}