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

// Track the global mouse state
// 0 = No click
// 1 = Click, but no drag
// 2 = Click and drag
mouseState = 0;

function mouseDown(time)
{
    // Update mouseState
    mouseState = 1;

    // Create a tentative sleep
    tentativeSleep = {
	'pk': "tentative",
	'start': time,
	'end': null,
	'comment': null,
	'date': null
    };
}
function mouseUp(time)
{
    // Update mouseState
    mouseState = 0;

    // Update the tentative sleep
    tentativeSleep.end = time;
    // Spawn a popup to make final edits, save the tentative
    // sleep
    spawnPopup();
}
function mouseMove(time)
{
    // Only repond to click-and-drag
    if (mouseState == 1 || mouseState == 2)
    {
	// Update mouseState
	mouseState = 2;
	if (time != tentativeSleep.end)
	{
	    tentativeSleep.end = time;
	    drawSleep(tentativeSleep, true);
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
    // Clear the sleep blocks
    $(".sleep-id-" + sleep.pk).removeClass("sleep-id-" + sleep.pk)
	.css("background-color", "");
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
	    'start': new Date(sleep.fields.start_time),
	    'end': new Date(sleep.fields.end_time),
	    'comments': sleep.fields.comments,
	    'date': new Date(sleep.fields.date)
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

    // First clear all of the current sleep blocks
    $(".sleep-id-" + sleep.pk)
	.css("background-color", "")
        .removeClass("sleep-id-" + sleep.pk);
    // Now find the appropriate blocks and fill them in
    var startblock = timeblocks[start.getTime()];
    if (typeof(startblock) !== 'undefined')
    {
	var $starttd = startblock['start'];
	if ($starttd != null)
	{
	    $starttd.addClass("sleep-id-" + sleep.pk);
	    $starttd.css("background-color", "green");
	}
    }
    start.setMinutes(start.getMinutes() + MINUTES_PER_HOUR/2);
    while (start.getTime() < end.getTime())
    {
	var block = timeblocks[start.getTime()];
	if (typeof(block) !== 'undefined')
	{
	    var $td = block['start'];
	    if ($td != null)
	    {
		$td.addClass("sleep-id-" + sleep.pk);
		$td.css("background-color", "blue");
	    }
	}
	start.setMinutes(start.getMinutes() + MINUTES_PER_HOUR/2);
    }
    var endblock = timeblocks[end.getTime()];
    if (typeof(endblock) !== 'undefined')
    {
	var $endtd = endblock['end'];
	if ($endtd != null)
	{
	    $endtd.addClass("sleep-id-" + sleep.pk);
	    $endtd.css("background-color", "red");
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
	var $td = $("<td></td>").html(date.toLocaleDateString())
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
		$td_left.mousedown(function() {mouseDown(t_left)})
		    .mousemove(function() {mouseMove(t_mid)})
		    .mouseup(function() {mouseUp(t_mid)});
		var $td_right = $("<td></td>").addClass("right");
		$td_right.mousedown(function() {mouseDown(t_mid)})
		    .mousemove(function() {mouseMove(t_right)})
		    .mouseup(function() {mouseUp(t_right)});

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
	buttons:
	{
	    "Create sleep": function()
	    {
		// Create the sleep
		$.post("/sleep/create/", {
		    "start[]": dateToArray($("#confirm-sleep-entry [name='start']").datepicker("getDate")),
		    "end[]": dateToArray($("#confirm-sleep-entry [name='end']").datepicker("getDate")),
		    "date[]": dateToArray($("#confirm-sleep-entry [name='date']").datepicker("getDate")),
		    "comments": $("#confirm-sleep-entry [name='comments']").val()
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
