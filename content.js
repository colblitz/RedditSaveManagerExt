console.log(window.location.href);

function idFromLink(link) {
  return link.attr('id').split("_")[2];
}

// var unsaveButtons = {};
var reload = function() {
  $('.thing.saved.link').each(function() {
    // var link = $(this);
    // var id = idFromLink(link);
    //var comments = link.find('.bylink.comments')[0];
    // var unsave = $(link.find('.link-unsave-button').find('a')[0]);
    // unsaveButtons[id] = unsave;

    // var $e = $("<div>", {id: "newDiv" + id, class: "aClass"});
    // $e.css({
    //   border: "1px solid red"
    // });
    // $e.click(function(){ /* ... */ });
    // add the element to the body
    // $(this).append($e);
    // $(this).insertAfter($e);


    // add click to link
    $(this).click( function(e) {
      if (!$(e.target).is("a")) {
        var link = $(this);
        var id = idFromLink(link);
        var url = $(link.find('a.title')[0]).attr('href');
        
        if (url.includes("imgur")) {
          if (url.includes("/a/")) {
            console.log(url);
            var thing = url.split("/").slice(-1)[0] + ".zip";
            url = url + "/zip";
            actuallyDownload(url, thing);
            ids.push(id);
          }
        }
      }

      // clicked(idFromLink($(this)));
      // var link = $(this);



      // var id = (link);
      // if (!$(e.target).is("a")) {
        
      // }

      // console.log("mouseup");
      // var link = $(this);
      // var id = idFromLink(link);
      // if (!$(e.target).is("a")) {
      //   clicked(id);
      //   return;
      // }
      // console.log("clicking a");
      // var unsave = $(link.find('.link-unsave-button').find('a')[0]);
      // console.log(unsave);
      // var u = $($('.thing.saved.link[id$=' + id + ']')[0]).find('.link-unsave-button').find('a')[0];
      // console.log(u);
      
      // // unsave[0].click();
      // // $(unsave)[0].click();

      // unsave.click()
      // unsave.dispatchEvent(new MouseEvent("click"));
      // unsave[0].click();
      // unsave[0].dispatchEvent(new MouseEvent("click"));
      // $(unsave).click();
      // $(unsave).dispatchEvent(new MouseEvent("click"));
      // $(unsave)[0].click();
      // $(unsave)[0].dispatchEvent(new MouseEvent("click"));
       
      // u.click()
      // u.dispatchEvent(new MouseEvent("click"));
      // u[0].click();
      // u[0].dispatchEvent(new MouseEvent("click"));
      // $(u).click();
      // $(u).dispatchEvent(new MouseEvent("click"));
      // $(u)[0].click();
      // $(u)[0].dispatchEvent(new MouseEvent("click"));

      // $(u).click();
      // console.log("-----");
      // console.log("is a: " + );
      // console.log(e.target);
      // console.log("-");
      // console.log(e.currentTarget);
      // if (e.target !== e.currentTarget) {
      //   console.log("was child mwaha");
      //   return;
      // }
      
    });

    // stop propagation for unsave
    // unsave.click( function(e) {
    //   e.stopPropagation();
    // });

  });
};
reload();

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

var clicked = function(id) {
  chrome.runtime.sendMessage({type: "unsave", id: id}, function(response) {
    // console.log("message sent");
    console.log("got: " + response);
    if (response.success) {
      console.log("transferred: " + response.id);
      // console.log("unsaved: " + response.id); 
      // // console.log(unsaveButtons[response.id]);
      // // unsaveButtons[response.id].click();

      // var u = $($('.thing.saved.link[id$=' + response.id + ']')[0]).find('.link-unsave-button').find('a')[0];
      // console.log(u);
      // console.log($(u));
      // $(u).click();
    } else {
      console.log("login");
    }
  });
}

var pages = 0;
var pageChecker = setInterval(function() {
  if ($('.NERPageMarker').size() != pages) {
    console.log("new page");
    pages = $('.NERPageMarker').size();
    reload();
  }
}, 2000);


chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
  if (request.type == "download") {
    var d = download();
    sendResponse({downloaded: d});
  }
});

// saved: 4uoqf0
// content.js:40 <a href=​"#">​unsave​</a>​
// content.js:41 [a, context: a]
// content.js:35 unsaved: 4uoqf0
// content.js:40 <a href=​"#">​unsave​</a>​
// content.js:41 [a, context: a]
// content.js:35 unsaved: 4uoqf0
// content.js:40 <a href=​"#">​unsave​</a>​
// content.js:41 [a, context: a]
// content.js:35 unsaved: 4uoqf0
// content.js:40 <a href=​"#">​unsave​</a>​
// content.js:41 [a, context: a]
// content.js:35 unsaved: 4uoqf0
// content.js:40 <a href=​"#">​unsave​</a>​
// content.js:41 [a, context: a]
// content.js:35 unsaved: 4uoqf0