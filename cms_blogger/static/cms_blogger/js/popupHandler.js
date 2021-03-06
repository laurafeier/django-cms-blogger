function html_unescape(string) {
    // Unescape a string that was escaped using django.utils.html.escape.

    //Create in-memory element; jQuery.html() will decode it
    return jQuery('<div>').html(string).text();
}

function id_to_windowname(text) {
    text = text.replace(/\./g, '__dot__');
    text = text.replace(/\-/g, '__dash__');
    return text;
}

function windowname_to_id(text) {
    text = text.replace(/__dot__/g, '.');
    text = text.replace(/__dash__/g, '-');
    return text;
}

function showNavigationPopup(triggeringLink, pWin) {
    var name = triggeringLink.id.replace(/^add_/, '');
    name = id_to_windowname(name);
    href = triggeringLink.href
    if (href.indexOf('?') == -1) {
        href += '?_popup=1';
    } else {
        href  += '&_popup=1';
    }
    var win = window.open(href, name, 'height=500,width=800,resizable=yes,scrollbars=yes');
    win.focus();
    return false;
}

function closeNavigationPopup(win, newRepr) {
    newRepr = html_unescape(newRepr);
    var name = windowname_to_id(win.name);
    var pretty_repr = name + '_pretty';
    document.getElementById(pretty_repr).innerHTML = newRepr;
    document.getElementById(pretty_repr).style.display = "block";
    win.close();
}
