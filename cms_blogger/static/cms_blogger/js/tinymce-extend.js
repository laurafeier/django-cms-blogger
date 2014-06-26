(function($){
    window['tinyMCESetup'] = function(ed) {
        ed.onInit.add(function(ed) {
            var HTML = "";
            HTML += "<td class='more' ><table style='border-collapse:collapse' class='mceListBox mceListBoxEnabled mce_formatselect'>"
            HTML += "<tr>"
            HTML += "<td class='mceFirst'><a href='javascript:void(0);' class='mceText'>Advanced</a></td>"
            HTML += "<td class='mceLast'><a href='javascript:void(0);' class='mceOpen' ><span><span ></span></span></a></td>"
            HTML += "</tr></table></td>";

            $('#id_body_toolbar1').remove('.more');
            $('#id_body_toolbar1 > tbody > tr')
            .append(HTML);

            $('#id_body_toolbar1 .more').off('click').on('click', function(){
                $(this).toggleClass('open');
                if(!$(this).hasClass('open')){
                    $('.mceToolbar:gt(1)').hide();
                    $(this).find('.mceText').html("Advanced")
                }else{
                    $('.mceToolbar:gt(1)').show();
                    $(this).find('.mceText').html("Simple")
                }
            })

            if(!$(this).hasClass('open')){
                $('.mceToolbar:gt(1)').hide();
                $(this).find('.mceText').html("Advanced")
            }else{
                $('.mceToolbar:gt(1)').show();
                $(this).find('.mceText').html("Simple")
            }
        });
    }
}(django.jQuery || jQuery))
