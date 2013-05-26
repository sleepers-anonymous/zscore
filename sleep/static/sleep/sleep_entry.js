// Constants
DAYS_PER_WEEK = 7
HOURS_PER_DAY = 24
MINUTES_PER_HOUR = 60


// Track the global mouse state
// 0 = No click
// 1 = Click, but no drag
// 2 = Click and drag
mouseState = 0;
// Helper variables to track currently selected range (as we drag)
startTime = null;
endTime = null;

function mouseDown(time)
{
    mouseState = 1;
    startTime = time;
    endTime = null;
}
function mouseUp(time)
{
    mouseState = 0;
    endTime = time;
    spawnPopup();
}
function mouseMove(time)
{
    if (mouseState == 1)
    {
	mouseState = 2;
	if (time != endTime)
	{
	    endTime = time;
	    updateTentativeBox();
	}
    }
}

function spawnPopup()
{
    alert('Done creating sleep: ' + String(startTime) + ' to ' + String(endTime));
}
function updateTentativeBox()
{
    //TODO
}

$(document).ready(function()
{
    // Get the sleep grid div, create a table
    var $sleep_grid = $(".sleep_grid");
    var $sleep_table = $("<table></table>").addClass("sleep-table");
    $sleep_table.prop("cellspacing", 0).prop("cellpadding", 0);
    $sleep_grid.append($sleep_table);

    // Store the date without any time component
    var today = new Date();
    today.setHours(0);
    today.setMinutes(0);
    today.setSeconds(0);
    today.setMilliseconds(0);

    // Iterate backwards over the past week, starting from the current date
    for (var d = 0; d < DAYS_PER_WEEK; ++d)
    {
	var $tr = $("<tr></tr>");
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
	    })();
	}
	$sleep_table.append($tr);
    } 
});
