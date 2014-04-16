(function($){
    var Entry = function(){

        this.init = function(){
            DOMChanges();

        };

        function DOMChanges(){
            $('.field-categories .help')
                .insertAfter($('.field-categories label:eq(0)'));
            $('.field-short_description .help')
                .insertAfter($('.field-short_description label:eq(0)'));
            $('.field-categories ul').wrap("<div class='categ-wrapper'>");

            $('.field-categories .categ-wrapper').scroller();
        }

        return this;
    };

    $(document).ready(function(){
        (new Entry()).init();
    });
})(jQuery);