function showEntryPreviewPopup(triggeringLink) {
    $.ajax({
        type:  "POST",
        datatype:  "text",
        url:  triggeringLink.href,
        data:  { "body": tinyMCE.activeEditor.getContent() },
        success: function(data) {
            var win = window.open('', 'entry-preview', 'height=800,width=1024,resizable=yes,scrollbars=yes');
            if (win && win.document) {
                with(win.document) {
                    open();
                    write(data);
                    close();
                }
            } else {
                alert('Your popup blocker is preventing the Preview Page from opening.');
            }
        }
    });
}
