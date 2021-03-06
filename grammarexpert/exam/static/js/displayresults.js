
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

$.ajaxSetup({
    beforeSend: function (xhr, settings) {
        if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
            // Only send the token to relative URLs i.e. locally.
            xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
        }
    }
});

var showError = function (errorText, errorJSON) {
    var tooltip = errorJSON['message'] + "\nSuggestions:";

    for (var i = 0; i < errorJSON.suggestions.length; i++) {
        tooltip += "\n" + errorJSON.suggestions[i];
    }

    var tag = "span";
    if (errorText.trim().length == 0) {
        tag = "pre";
    }
    var x =
        "<" + tag + " class='error "
        + errorJSON.type
        + "' data-toggle='tooltip'"
        + " title='" + tooltip
        + "'>"
        + errorText
        + "</" + tag + ">";

    return x;
}

var showText = function (text) {
    return "<span class='correct'>" + text + "</span>";
}

var appendElem = function (e, html) {
    e.append($(html));
}

var highlightErrors = function (data) {
    var round = function(v) {
        return Math.round(v * 100)/100
    };
    var text = data["answer"];
    var errors = data["errors"];
    $('#w_c').text(data['wordCount']);
    $('#grammar').text(data['grammarErrorCount']);
    $('#spelling').text(data['spellingErrorCount']);
    $('#wordlimit').text(round(data['wordlimitpenalty']));
    $('#score').text(round(data['score']));
    $('#sentencequality').text(round(data['sentencequalitypenalty']));
    $('#wordquality').text(round(data['wordqualitypenalty']));
    $('#requiredtext').text(data['requiredtextpenalty']);
    var e = $('#essay');
    e.empty();
    if (errors.length == 0) {
        $('#essay').text(text);
    } else {

    var offset = errors[0].offset;
    var length;
    
    if (offset > 0) {
        appendElem(e, showText(text.substring(0, offset)));
    }

    for (var i = 0; i < errors.length; i++) {
        offset = errors[i].offset;
        length = errors[i].length;
        appendElem(e, showError(
            text.substring(offset, offset + length),
            errors[i]
        ));

        if (i == errors.length - 1) {
            appendElem(e, showText(text.substring(offset + length)));
        } else {
            appendElem(e, showText(text.substring(offset + length, errors[i + 1].offset)));
        }
    }
    }
    $('#essay').show();
    $('#res').show();
}
