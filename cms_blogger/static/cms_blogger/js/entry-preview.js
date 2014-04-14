

function showEntryPreviewPopup(triggeringLink) {
    var name = 'entry-preview';
    href = triggeringLink.href
    var params = {
        _popup:1,
        body: tinyMCE.activeEditor.getContent() };
    href += (href.indexOf('?') == -1) ?  '?': '&';
    href += jQuery.param(params);
    var win = window.open(
        href, name, 'height=500,width=800,resizable=yes,scrollbars=yes');
    win.focus();
    return false;
}