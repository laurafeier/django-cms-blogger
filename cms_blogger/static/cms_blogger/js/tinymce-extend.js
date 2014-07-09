(function($){
    window['tinyMCESetup'] = function(ed) {
        
        function stripHTMLTags(html){
            return $("<div/>").html(html).text();
        }

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

            // Add blur event to set back the 'Sample content' placeholder
            // TinyMCE 3.x doesn't have this by default
            tinymce.dom.Event.add(ed.getDoc().body, 'blur', function(e) {
                var content = ed.getContent({format: 'raw'});
                var plainText = stripHTMLTags(content);

                if(plainText === ''){
                    ed.setContent('Sample content');
                }
            });

            ed.onClick.add(function(ed, e) {
                var content = ed.getContent({format: 'raw'});
                var plainText = stripHTMLTags(content);

                if(plainText === 'Sample content'){
                    ed.setContent('');
                }
            });
        });
    }
}(django.jQuery || jQuery))
