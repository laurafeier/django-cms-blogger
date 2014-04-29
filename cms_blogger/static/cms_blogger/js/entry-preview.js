function showEntryPreviewPopup(triggeringLink, admin_static_url) {
    var win = window.open('', 'entry-preview', 'height=800,width=1024,resizable=yes,scrollbars=yes');
    if(win)
    {
        with(win.document)
        {
            open();
            html = '\
                <!DOCTYPE html>\
                <html><head>\
                    <style>\
                        html {\
                        width: 100%; height: 100%;\
                        background: url(\"' + admin_static_url + 'img/spinner.gif\") center center no-repeat;}\
                    </style>\
                </head></html>';
            write(html);
            close();
        }
    }

    $.ajax({
        type: "POST",
        datatype: "text",
        url: triggeringLink.href,
        data: { "body": tinyMCE.activeEditor.getContent() },
        success: function(data) {
            with(win.document) {
                open();
                write(data);
                close();
            }
        }
    });
}
