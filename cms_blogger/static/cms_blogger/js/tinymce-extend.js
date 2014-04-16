(function($){
    $(window).load(function(){
        var HTML = "";
        HTML += "<td><span><table style='border-collapse:collapse' class='mceListBox mceListBoxEnabled mce_formatselect more'>"
        HTML += "<tr>"
        HTML += "<td class='mceFirst'><a href='javascript:void(0);' class='mceText'>More</a></td>"
        HTML += "<td class='mceLast'><a href='javascript:void(0);' class='mceOpen' ><span><span ></span></span></a></td>"
        HTML += "</tr></table></span></td>"

        $('#id_body_toolbar1').remove('.more')
        $('#id_body_toolbar1 > tbody > tr')
        .append(HTML)
        $('#id_body_toolbar1 .more').off('click').on('click', function(){
            $(this).toggleClass('open');
            if(!$(this).hasClass('open')){
                $('.mceToolbar:gt(1)').hide();
                $(this).find('.mceText').html("More")
            }else{
                $('.mceToolbar:gt(1)').show();
                $(this).find('.mceText').html("Hide")
            }
        })

        if(!$(this).hasClass('open')){
            $('.mceToolbar:gt(1)').hide();
            $(this).find('.mceText').html("More")
        }else{
            $('.mceToolbar:gt(1)').show()
            $(this).find('.mceText').html("Hide")
        }
    })
}(django.jQuery || jQuery))
