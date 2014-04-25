function showEntryPreviewPopup(triggeringLink) {
    var win = window.open('', 'entry-preview', 'height=800,width=1024,resizable=yes,scrollbars=yes');
    $.ajax({
        type:  "POST",
        datatype:  "text",
        url:  triggeringLink.href,
        data:  { "body": tinyMCE.activeEditor.getContent() },
        success: function(data) {
            with(win.document) {
                open();
                write(data);
                close();
            }
        }
    });
}
