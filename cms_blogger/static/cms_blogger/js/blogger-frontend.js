(function($){
    function Blogger(){

        this.init = function(){
            normalizeSocialURLs();
        };

        var social = {
            facebook_share : function(){
                if(typeof _gaq !== 'undefined'){
                    _gaq.push(['_trackSocial', 'facebook', 'send']);
                }
            },

            twitter_share : function(){
                if(typeof _gaq !== 'undefined'){
                    _gaq.push(['_trackSocial', 'twitter', 'tweet']);
                }
            },

            email_share : function(){
                if(typeof _gaq !== 'undefined'){
                    _gaq.push(['_trackSocial', 'email', 'send']);
                }
            }
        };

        function getHost(){
            return window.location.host;
        }

        function getProtocol(){
            return window.location.protocol;
        }

        function tokenizeParams(string){
            string = string.replace(/&amp;/g, "&").substr(string.indexOf("?")+1);
            var obj = {};

            string = string.split("&").map(function(item, i){
                obj[item.split("=")[0]] = item.split("=")[1];
            });

            return obj;
        }

        function flattenParams(params){
            var s = "";
            for(var p in params) {
                if(params.hasOwnProperty(p)){
                    s += "&"+p+"="+params[p];
                }
            }

            return s;
        }

        function normalizeSocialURLs(){
            var widgets = $('.blog-entry a.social, .blog-post a.social');

            widgets.each(function(){
                var shreLink, url, prefix,
                    href = $(this).data("href") || $(this).attr("href"),
                    params = tokenizeParams(href);

                for(var p in params) {
                    if(params.hasOwnProperty(p)){
                        if(params[p].charAt(0) === "/"){
                            prefix = getProtocol()+"//"+getHost();
                            params[p] = prefix + params[p];
                        }
                    }
                }

                href = href.split("?")[0] + "?" + flattenParams(params);
                if($(this).data("href")){
                    $(this).data("href", href);
                }else{
                    $(this).attr("href", href);
                }
                $(this).off('click');
                addClickHandlers($(this));
            });
        }


        function addClickHandlers(elem){
            function openWindow(elem){
                var win = window.open(
                    elem.data('href'),
                    'ShareBlogPost', 'height=800,width=960,resizable=yes,scrollbars=yes');
                win.focus();
            }

            elem.on('click', function(e){
                if($(this).hasClass('email')){
                    //set timeout to make sure request doesn't get canceled by the browser
                    setTimeout(social.email_share, 500);
                }

                if($(this).hasClass('facebook')){
                    social.facebook_share();
                    openWindow($(this));
                    e.preventDefault();
                }

                if($(this).hasClass('twitter')){
                    social.twitter_share();
                    openWindow($(this));
                    e.preventDefault();
                }
            });
        }

        return this;
    }

    var blogger = (new Blogger()).init();

})(jQuery);