(function($) {
    $(document).ready(function() {
        // Add anchor tag for Show/Hide link
        $("fieldset.collapse").each(function(i, elem) {
            // Don't hide if fields in this fieldset have errors
            if ($(elem).find("div.errors").length == 0) {
                if(!$(elem).hasClass('open')){
                    $(elem).addClass("collapsed");
                }
                $(elem).find("h2").first().append(' (<a id="fieldsetcollapser' +
                    i +'" class="collapse-toggle" href="#">' + gettext("Show") +
                    '</a>)');
            }
        });

        $("fieldset.collapse a.collapse-toggle").off('click').on('click', function(){
            var fieldset = $(this).closest("fieldset");
            if(fieldset.hasClass('collapsed')){
                $(this).text(gettext("Hide"));
                fieldset.removeClass("collapsed").trigger("show.fieldset", [$(this).attr("id")]);
                return false;
            }else{
                $(this).text(gettext("Show"));
                fieldset.addClass("collapsed").trigger("hide.fieldset", [$(this).attr("id")]);
                return false;
            }
        })

    });
})(django.jQuery);
