(function($){

    window['tinyMCESetup'] = function(ed) {

        function removePlaceholder(content){
            if(content === '<p>Sample content</p>'){
                //don't use setContet('') to avoid triggering beforeSetContent
                //and get an endless loop
                ed.getDoc().body.innerHTML = '';
            }
        }

        function addPlaceholder(content){
            if(content === ''){
                ed.setContent('<p>Sample content</p>');
            }
        }

        if(typeof dismissEditPluginPopup === 'function' &&
           typeof window._super_dismissEditPluginPopup === 'undefined'){

            //extend the default edit plugin callback (dismissEditPluginPopup)
            //this is a global function and gets called whne the user finishes 
            //to edit the plugin
            //this is the only way to receive a callback when adding pluggins 
            //because they don't trigger any event on TinyMCE
            window._super_dismissEditPluginPopup = window.dismissEditPluginPopup;
            window.dismissEditPluginPopup = function(){
                
                removePlaceholder(ed.getContent({format: 'raw'}))
                //call super
                window._super_dismissEditPluginPopup.apply(this, arguments);
            };

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
                addPlaceholder(content)
            });

            ed.onClick.add(function(ed, e) {
                var content = ed.getContent({format: 'raw'});

                removePlaceholder(content)
            });

            ed.onBeforeSetContent.add(function(ed, o) {
                var content = ed.getContent({format: 'raw'});
                removePlaceholder(content)       
            });

            ed.onBeforeExecCommand.add(function(ed, cmd, ui, val) {
                ed.oldContent = ed.getContent({format: 'raw'})
                removePlaceholder(ed.oldContent)
            });

            ed.onExecCommand.add(function(ed, cmd, ui, val) {
                var content = ed.getContent({format: 'raw'});

                addPlaceholder(content)
            });
        });
    }
}(django.jQuery || jQuery))
