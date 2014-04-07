(function($){
    $(window).load(function(){
        $('#id_body_toolbargroup').remove('.arrow')
        $('#id_body_toolbargroup span[role="application"]').before("<span class='arrow'><span></span></span>")
        $('#id_body_toolbargroup span.arrow').off('click').on('click', function(){
            $(this).toggleClass('open');
        })
    })
}(django.jQuery || jQuery))
