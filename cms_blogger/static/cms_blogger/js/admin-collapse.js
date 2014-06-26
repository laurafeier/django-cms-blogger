(function($) {
    //make sure the reaady callback is added only once
    $(document).unbind('ready.collapseFieldset')
    $(document).bind('ready.collapseFieldset', function() {
        // Add anchor tag for Show/Hide link
        $("fieldset.collapse").each(function(i, elem) {
            // Don't hide if fields in this fieldset have errors
            if ($(elem).find("div.errors").length == 0) {
                if(!$(elem).hasClass('open')){
                    $(elem).addClass("collapsed");
                }
                var text = $(elem).find("h2").first().text()
                $(elem).find("h2").first().html('<a id="fieldsetcollapser' +
                    i +'" class="collapse-toggle" href="#">' + text +
                    '</a>');
            }
        });

        $("fieldset.collapse a.collapse-toggle").off('click').on('click', function(){
            var fieldset = $(this).closest("fieldset");
            if(fieldset.hasClass('collapsed')){
                fieldset.removeClass("collapsed").trigger("show.fieldset", [$(this).attr("id")]);
                return false;
            }else{
                fieldset.addClass("collapsed").trigger("hide.fieldset", [$(this).attr("id")]);
                return false;
            }
        });

        // Add anchor tag for Show/Hide link
        $('fieldset.collapsible-inner').each(function(index, Element) {
            var prev_fieldset = $(this).prev();
            var fieldset = $(this);
            if(prev_fieldset.length){
                fieldset.appendTo(prev_fieldset);
                var anchor = $('<a class="collapse-toggle"></a>')
                var header = fieldset.find("h2")
                anchor.off('click').on('click', function(event){
                    event.preventDefault();
                    fieldset.toggleClass('closed');
                });
                header.wrap(anchor);
                $("<a class='inline-deletelink'/>").appendTo(header);
            }
        });

    });
})(django.jQuery);
