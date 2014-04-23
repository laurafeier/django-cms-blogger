(function($){
    var Entry = function(){

        this.init = function(){
            DOMChanges();
            explandErrorFields();
        };

        function DOMChanges(){
            $('.field-categories .help')
                .insertAfter($('.field-categories label:eq(0)'));
            $('.field-short_description .help')
                .insertAfter($('.field-short_description label:eq(0)'));
            $('.field-categories ul').wrap("<div class='categ-wrapper'>");

            $('.field-categories .categ-wrapper').scroller();

            $('#id_short_description').attr('maxlength', 400);
        }

        function explandErrorFields(){
            $('.errors:hidden').closest('.closed').removeClass('closed');
            $('.errors:hidden').closest('.collapsed').removeClass('collapsed');
        }

        return this;
    };

    $(document).ready(function(){
        (new Entry()).init();
    });
})(jQuery);