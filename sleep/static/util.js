function dateToArray(dateObj)
{
    // Form of the post array:
    // 0 -- Year
    // 1 -- Month
    // 2 -- Day
    // 3 -- Hour
    // 4 -- Minutes
    // 5 -- Seconds
    return [dateObj.getFullYear(),
	    dateObj.getMonth()+1,
	    dateObj.getDate(),
	    dateObj.getHours(),
	    dateObj.getMinutes(),
	    dateObj.getSeconds()];
}

// Set up all AJAX requests to include the CSRF token and disable
// cross-domain AJAX requests (borrowed straight from the Django page)
var csrftoken = $.cookie("csrftoken");
function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
    crossDomain: false,
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type)) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

function addFriend(id,link) {
  $.post("/friends/add/", {
    "id": id
  }, function() {
    link.innerHTML="added";
  });
};
function removeFriend(id,link) {
  $.post("/friends/remove/", {
    "id": id
  }, function() {
    link.innerHTML="removed";
  });
};
function follow(id,link) {
  $.post("/friends/follow/", {
    "id": id
  }, function() {
    link.innerHTML="followed";
  });
};
function unfollow(id,link) {
  $.post("/friends/unfollow/", {
    "id": id
  }, function() {
    link.innerHTML="unfollowed";
  });
};
function friendRequest(id,link) {
  $.post("/friends/request/", {
    "id" : id
  }, function() {
    link.innerHTML="requested";
  });
};
function hideRequest(id,link) {
  $.post("/friends/hide/", {
    "id" : id
  }, function() {
    link.innerHTML="hidden";
  });
};
function inviteMember(gid,uid,link) {
  $.post("/groups/invite/", {
      "group" : gid,
      "user" : uid
  }, function() {
    link.innerHTML="invited";
  });
};
function removeMember(gid,uid,link) {
  $.post("/groups/membership/", {
      "group" : gid,
      "user" : uid,
      "action": "remove"
  }, function() {
    link.innerHTML="removed";
  }).fail ( function() {
      link.innerHTML = "cannot remove last admin";
      link.className = "button-error"
  });
};

function makeAdmin(gid,uid, link) {
    $.post("/groups/membership/", {
        "group": gid,
        "user": uid,
        "action": "makeAdmin"
    }, function() {
        link.innerHTML = "adminified";
    });
};

function removeAdmin(gid, uid, link) {
    $.post("/groups/membership/", {
        "group": gid,
        "user": uid,
        "action": "removeAdmin"
    }, function() {
        link.innerHTML = "unadminified";
    }).fail( function() {
        link.innerHTML = 'cannot remove last admin';
        link.className = "button-error"
    });
};

function acceptInvite(id,link) {
  $.post("/groups/accept/", {
      "id" : id,
      "accepted" : "True",
  }, function() {
    link.innerHTML="accepted";
  });
};

function rejectInvite(id,link) {
  $.post("/groups/accept/", {
      "id" : id,
      "accepted" : "False",
  }, function() {
    link.innerHTML="rejected";
  });
};

function requestGroup(id, link) {
    $.post("/groups/request/", {
            "group": id
            }, function() {
            link.innerHTML = "requested";
        });
};

function joinGroup(id, link) {
    $.post("/groups/join/", {
            "group": id
            }, function() {
            link.innerHTML = "joined";
        });
};

function acceptRequest(id,link) {
  $.post("/groups/request/process/", {
      "id" : id,
      "accepted" : "True",
  }, function() {
    link.innerHTML="accepted";
  });
};

function rejectRequest(id,link) {
  $.post("/groups/request/process/", {
      "id" : id,
      "accepted" : "False",
  }, function() {
    link.innerHTML="rejected";
  });
};
