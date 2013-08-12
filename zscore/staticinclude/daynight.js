//Code adapted from http://www.thesitewizard.com/javascripts/change-style-sheets.shtml

//Variables:
var style_cookie_name = "zscore_style" ;

var style_cookie_duration = 1 //in hours

function switch_style ( style_name )
{
    document.body.className = style_name;
    set_cookie (style_cookie_name, style_name, style_cookie_duration );
}

function set_style()
{
    var style_name = get_cookie( style_cookie_name );
    if (style_name.length) {
        switch_style( style_name );
    }
    else {
        var now = new Date();
        var h = now.getHours();
        if (h < 8 || h > 20) {
            switch_style("nighttime");
        }
        else {
            switch_style("daytime");
        }
    }
    return '';
}

function set_cookie ( cookie_name, cookie_value, lifespan_in_hours, valid_domain ) {
    // http://www.thesitewizard.com/javascripts/cookies.shtml
    var domain_string = valid_domain ?
        ("; domain=" + valid_domain) : '' ;
    document.cookie = cookie_name + "=" + encodeURIComponent( cookie_value ) +  "; max-age=" + 60 * 60 * lifespan_in_hours + "; path=/" + domain_string ;
    return '';
}

function get_cookie ( cookie_name )
{
    // http://www.thesitewizard.com/javascripts/cookies.shtml
    var cookie_string = document.cookie ;
    if (cookie_string.length != 0) {
        var cookie_value = cookie_string.match ( '(|^;)[\s]*' + cookie_name + '=([^;]*)' );
        return decodeURIComponent ( cookie_value[2] ) ;
    }
    return '' ;
}
