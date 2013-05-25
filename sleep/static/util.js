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