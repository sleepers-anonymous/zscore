var colors = ["#ff0000", "#666666", "#00ff00", 
              "#ffff00", "#0000ff", "#00ffff",
              "#999999", "#ff9966", "#ff00ff",
              "#99ff66", "#6699ff"];

function setCyclingColor($element) {
    var i = Math.floor(Math.random()*11);
    $element.css("color", colors[i]);
    setTimeout(function(){setCyclingColor($element)}, 100);
}

$(document).ready(function() {
    $("p,a").each(function(index, element) {
        setCyclingColor($(element));
        if (Math.random() < 0.8) {
            $(element).html($("<marquee/>")
                            .attr("scrollamount", Math.floor(Math.random()*30)+10)
                            .html($(element).html()));
        }
    });
});
