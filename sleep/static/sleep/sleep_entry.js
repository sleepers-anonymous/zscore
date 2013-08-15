// Constants
DAYS_PER_WEEK = 7
HOURS_PER_DAY = 24
MINUTES_PER_HOUR = 60


// Reverse map from the time to the timeblock
timeblocks = {};
// Dict of sleeps by pk
sleeps = {};
// Global object for tentative sleep
tentativeSleep = null;
// A sleep looks like:
// 'pk' -- the pk of the sleep ("tentative" for the tentative sleep)
// 'start' -- a Date object representing the start time/date
// 'end' -- a Date object representing the end time/date
// 'comment' -- a String; the user's comment on this sleep
// 'date' -- a Date object, in which we only care about the
//           actual day; which day to associate the sleep with
// 'timezone' -- the timezone in which we entered the sleep

// Track the global mouse state
// 0 = No click
// 1 = Click, but no drag
// 2 = Click and drag
mouseState = 0;

// Utility function used by the mouseX functions to choose
// a reasonable end time, if the one you are hovering over
// would cause a negative time sleep
function getValidEndTime(startTime, endTime)
{
    // Duplicate endTime, since we don't ever want to return
    // the original (because it's likely we'll be mutating
    // what we return)
    var newEndTime = new Date(endTime);
    if (newEndTime > startTime)
    {
	return newEndTime;
    }

    // Try bumping the end time to the current date
    newEndTime.setDate(startTime.getDate());
    if (newEndTime > startTime)
    {
	return newEndTime;
    }

    // Bump up by one more day, if that doesn't put us
    // into the future. Else, just return the same time as
    // the startTime.
    var dateToday = new Date();
    dateToday.setHours(24);
    dateToday.setMinutes(0);
    dateToday.setSeconds(0);
    dateToday.setMicroseconds(0);
    newEndTime.setDate(newEndTime.getDate()+1);
    if (newEndTime < dateToday)
    {
	return newEndTime;
    }
    else
    {
	return new Date(startTime);
    }
}
function mouseDown(startTime, endTime)
{
    // Make all content unselectable, so we don't get annoying test selection
    // issues
    $(".global-wrapper").addClass("unselectable");

    // If we aren't in the middle of creating a sleep,
    // initiate a new one.
    if (mouseState == 0 || mouseState == 1)
    {
	// Update mouseState
	mouseState = 1;

	// Create a tentative sleep
	tentativeSleep = {
	    'pk': "tentative",
	    'start': startTime,
	    'end': null,
	    'comment': null,
	    'date': null
	};
    }
    // If we were in the middle of creating a sleep,
    // use this to terminate the sleep
    else
    {
	// Update mouseState
	mouseState = 0;
	// Complete the tentative sleep
	tentativeSleep.end = getValidEndTime(tentativeSleep.start, endTime);
	// Spawn a popup to make final edits, save the tentative
	// sleep
	spawnPopup();
    }
}
function mouseUp(startTime, endTime)
{
    // Make all content reselectable
    $(".global-wrapper").removeClass("unselectable");

    // Only if we were previously dragging, complete this sleep
    if (mouseState == 2)
    {
	// Update mouseState
	mouseState = 0;

	// Update the tentative sleep
	tentativeSleep.end = getValidEndTime(tentativeSleep.start, endTime);
	// Spawn a popup to make final edits, save the tentative
	// sleep
	spawnPopup();
    }
}
function mouseMove(startTime, endTime)
{
    // Only repond to click-and-drag
    if (mouseState == 1 || mouseState == 2)
    {
	// Update mouseState
	mouseState = 2;
	if (getValidEndTime(tentativeSleep.start, endTime) != tentativeSleep.end)
	{
	    tentativeSleep.end = getValidEndTime(tentativeSleep.start, endTime);
	    drawSleep(tentativeSleep);
	}
    }
}

function spawnPopup()
{
    $("#confirm-sleep-entry [name='start']").datepicker("setDate", tentativeSleep.start);
    $("#confirm-sleep-entry [name='end']").datepicker("setDate", tentativeSleep.end);
    $("#confirm-sleep-entry [name='date']").datepicker("setDate", new Date((tentativeSleep.start.valueOf() + tentativeSleep.end.valueOf()) / 2));
    $("#confirm-sleep-entry").dialog("open");
}
function clearSleep(sleep)
{
    // Clear the sleep box
    $(".sleep-id-" + sleep.pk).remove();
}
// Handle the JSON response from the server
// containing a list of our sleeps
function processSleeps(jsonData)
{
    // Clear our current dict of sleeps
    sleeps = {};
    // Build a new dict based on JSON data
    for (var i in jsonData)
    {
	var sleep = jsonData[i];
	sleeps[sleep.pk] = {
	    'pk': sleep.pk,
	    'start': moment(sleep.fields.start_time).toDate(),
	    'end': moment(sleep.fields.end_time).toDate(),
	    'comments': sleep.fields.comments,
	    'date': new Date(sleep.fields.date),
        'timezone': sleep.fields.timezone,
	};
    }
    // Now render all our current sleeps
    renderSleeps();
}
// Render all sleeps in the sleeps dict
function renderSleeps()
{
    for (var i in sleeps)
    {
	var sleep = sleeps[i];
	drawSleep(sleep);
    }
}
// Draw floating box from $td1 to $td2, potentially
// drawing the beginning and end as a continuing beginning/end
function drawSleepBox(sleep_pk, $td1, $td2, drawStartIcon, drawEndIcon)
{
    // Fill in default values
    if (typeof(drawStartIcon) === 'undefined')
    {
	drawStartIcon = true;
    }
    if (typeof(drawEndIcon) === 'undefined')
    {
	drawEndIcon = true;
    }

    // Compute the width and draw the box itself
    var width = $td2.position().left - $td1.position().left;
    var $sleep_box = $("<div></div>").css("padding-right", width+19).css("margin-right", -width-21)
	.css("margin-left", 1).addClass("sleep-box")
	.addClass("sleep-id-" + sleep_pk);
    // Add the mouse event handlers to prevent flicker
    // TODO(gurtej): Convert the sleep boxes into overlays which resize when hovered over
    // correctly
    $sleep_box.mouseup(function() {
	$td2.mouseup();
	return false;
    });
    $sleep_box.mousemove(function() {
	$td2.mousemove();
	return false;
    });
    $sleep_box.mousedown(function() {
	return false;
    });
    // Add the tentative class if it's a tentative box (changes the color)
    if (sleep_pk == "tentative") $sleep_box.addClass("tentative");

    // Draw the start icon if needed
    if (drawStartIcon)
    {
	var $sleep_box_start = $("<div class='start'></div>");
	if (sleep_pk == "tentative") $sleep_box_start.addClass("tentative");
	$sleep_box.append($sleep_box_start);
    }
    if (drawEndIcon)
    {
	var $sleep_box_end = $("<div class='end'></div>").css("margin-right", -width-29);
	if (sleep_pk == "tentative") $sleep_box_end.addClass("tentative");
	$sleep_box.append($sleep_box_end);
    }
    $td1.append($sleep_box);
}
// Draw a sleep on the grid
function drawSleep(sleep)
{
    // Duplicate the input Date objects on the sleep
    var start = new Date(sleep.start);
    var end = new Date(sleep.end);
    // Round off the times to the nearest half-hour
    var startMinutes = start.getMinutes() + MINUTES_PER_HOUR/4;
    var endMinutes = end.getMinutes() + MINUTES_PER_HOUR/4;
    start.setMinutes(startMinutes - (startMinutes % (MINUTES_PER_HOUR/2)));
    start.setSeconds(0);
    start.setMicroseconds(0);
    end.setMinutes(endMinutes - (endMinutes % (MINUTES_PER_HOUR/2)));
    end.setSeconds(0);
    end.setMicroseconds(0);

    // First clear the current sleep box
    $(".sleep-id-" + sleep.pk).remove();
    // Now find the appropriate blocks
    var startblock = timeblocks[start.getTime()];
    if (typeof(startblock) === 'undefined') return false;
    var $starttd = startblock['start'];
    if ($starttd == null) return false;
    var endblock = timeblocks[end.getTime()];
    if (typeof(endblock) === 'undefined') return false;
    var $endtd = endblock['end'];
    if ($endtd == null) return false;
    // Fill them in with carryovers as needed
    if (start.getDate() == end.getDate())
    {
	// It's all one line -- render normally
	drawSleepBox(sleep.pk, $starttd, $endtd);
    }
    else
    {
	// Multiline display with carryovers
	var curDate = new Date(start);
	curDate.setHours(0);
	curDate.setMinutes(0);
	curDate.setSeconds(0);
	curDate.setMicroseconds(0);
	while (curDate <= end)
	{
	    if (curDate.getDate() == start.getDate())
	    {
		var endRowTime = new Date(start);
		endRowTime.setHours(24);
		endRowTime.setMinutes(0);
		var endRowBlock = timeblocks[endRowTime.getTime()];
		if (typeof(endRowBlock) === 'undefined') return false;
		var $endRowTd = endRowBlock['end'];
		if($endRowTd == null) return false;
		drawSleepBox(sleep.pk, $starttd, $endRowTd, true, false);
	    }
	    else if (curDate.getDate() == end.getDate())
	    {
		var beginRowTime = new Date(end);
		beginRowTime.setHours(0);
		beginRowTime.setMinutes(0);
		var beginRowBlock = timeblocks[beginRowTime.getTime()];
		if (typeof(beginRowBlock) === 'undefined') return false;
		var $beginRowTd = beginRowBlock['start'];
		if($beginRowTd == null) return false;
		drawSleepBox(sleep.pk, $beginRowTd, $endtd, false, true);
	    }
	    else
	    {
		var beginRowTime = new Date(curDate);
		beginRowTime.setHours(0);
		beginRowTime.setMinutes(0);
		var beginRowBlock = timeblocks[beginRowTime.getTime()];
		if (typeof(beginRowBlock) === 'undefined') return false;
		var $beginRowTd = beginRowBlock['start'];
		if($beginRowTd == null) return false;
		var endRowTime = new Date(curDate);
		endRowTime.setHours(24);
		endRowTime.setMinutes(0);
		var endRowBlock = timeblocks[endRowTime.getTime()];
		if (typeof(endRowBlock) === 'undefined') return false;
		var $endRowTd = endRowBlock['end'];
		if($endRowTd == null) return false;
		drawSleepBox(sleep.pk, $beginRowTd, $endRowTd, false, false);
	    }
	    // Increment the date
	    curDate.setDate(curDate.getDate()+1);
	}
    }
}

$(document).ready(function()
{
    // Clear the timeblocks reverse map
    timeblocks = {};

    // Get the sleep grid div, create a table
    var $sleep_grid = $(".sleep-grid");
    var $sleep_table = $("<table></table>").addClass("sleep-table");
    $sleep_table.prop("cellspacing", 0).prop("cellpadding", 0);
    $sleep_grid.append($sleep_table);

    // Store the date without any time component
    var today = new Date();
    today.setHours(0);
    today.setMinutes(0);
    today.setSeconds(0);
    today.setMilliseconds(0);

    // Create a header for the times
    var $tr = $("<tr></tr>").addClass("header-row");
    $tr.append($("<th></th>").addClass("corner"));
    for (var h = 0; h < HOURS_PER_DAY; ++h)
    {
	var $th = $("<th colspan=2></th>").addClass("column-header")
	    .html(h + ":00");
	$tr.append($th);
    }
    $sleep_table.append($tr);
    // Iterate backwards over the past week, starting from the current date
    for (var d = 0; d < DAYS_PER_WEEK; ++d)
    {
	var $tr = $("<tr></tr>");
	// Create a header for the row
	var date = new Date(today);
	date.setDate(date.getDate() - d);
	var $td = $("<td></td>").html("<a class='hidden' href='/sleep/allnighter/?withdate="+ $.datepicker.formatDate('yymmdd', date)+  "'>" + date.toLocaleDateString() + "</a>")
	    .addClass("row-header");
	$tr.append($td);
	// Create a left and right cell per hour
	for (var h = 0; h < HOURS_PER_DAY; ++h)
	{
	    // Define an anonymous function for scoping
	    (function()
	    {
		// Compute the times at the start, middle, and end of this block
		var t_left = new Date(today);
		t_left.setDate(t_left.getDate() - d);
		var t_mid = new Date(t_left);
		var t_right = new Date(t_left);
		t_left.setHours(h);
		t_mid.setHours(h);
		t_mid.setMinutes(MINUTES_PER_HOUR/2);
		t_right.setHours(h+1);
	    
		// Split the block into the two half-hours;
		// Set the mouse triggers
		var $td_left = $("<td></td>").addClass("left");
		$td_left.mousedown(function() {mouseDown(t_left, t_mid)})
		    .mousemove(function() {mouseMove(t_left, t_mid)})
		    .mouseup(function() {mouseUp(t_left, t_mid)});
		var $td_right = $("<td></td>").addClass("right");
		$td_right.mousedown(function() {mouseDown(t_mid, t_right)})
		    .mousemove(function() {mouseMove(t_mid, t_right)})
		    .mouseup(function() {mouseUp(t_mid, t_right)});

		$tr.append($td_left);
		$tr.append($td_right);

		// Add the half-blocks to the reverse map
		var left_time = t_left.getTime();
		var mid_time = t_mid.getTime();
		var right_time = t_right.getTime();
		if (typeof(timeblocks[left_time]) == 'undefined')
		{
		    timeblocks[left_time] = {'start': $td_left, 'end': null};
		}
		else
		{
		    timeblocks[left_time]['start'] = $td_left;
		}
		if (typeof(timeblocks[right_time]) == 'undefined')
		{
		    timeblocks[right_time] = {'start': null, 'end': $td_right};
		}
		else
		{
		    timeblocks[right_time]['end'] = $td_right;
		}
		timeblocks[mid_time] = {'start': $td_right, 'end': $td_left};
	    })();
	}
	$sleep_table.append($tr);
    } 


    // Get the list of current sleeps and display them in the grid
    $.post("/sleep/getSleeps/", null, processSleeps);


    // Set the fields of the confirm sleep dialog to be datetimepicker objects
    $("#confirm-sleep-entry [name='start']").datetimepicker();
    $("#confirm-sleep-entry [name='end']").datetimepicker();
    $("#confirm-sleep-entry [name='date']").datepicker();
    // Set up the confirm sleep dialog
    $("#confirm-sleep-entry").dialog({
	autoOpen: false,
	height: 350,
	width: 400,
	modal: true,
	position: {my: "center top", at: "center top", of: window},
	buttons:
	{
	    "Create sleep": function()
	    {
		// Create the sleep
		$.post("/sleep/create/", {
		    "start[]": dateToArray($("#confirm-sleep-entry [name='start']").datepicker("getDate")),
		    "end[]": dateToArray($("#confirm-sleep-entry [name='end']").datepicker("getDate")),
		    "date[]": dateToArray($("#confirm-sleep-entry [name='date']").datepicker("getDate")),
		    "comments": $("#confirm-sleep-entry [name='comments']").val(),
		    "timezone": $("#confirm-sleep-entry [name='timezone']").val()
		}, function() {
		    // TODO: Update the page dyanmically (without reloading)
		    // For now:
		    location.reload();
		});
	    },
	    Cancel: function()
	    {
		$(this).dialog("close");
	    }
	},
	close: function()
	{
	    clearSleep(tentativeSleep);
	    $(".confirm-sleep-entry input").removeClass("ui-state-error");
	}
    });
});
