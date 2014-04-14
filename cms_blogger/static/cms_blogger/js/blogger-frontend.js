(function($){
    function Blogger(){

        this.init = function(){
            normalizeSocialURLs();
        }

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
            var widgets = $('.blog-entry a.social, .blog-post a.social ');

            widgets.each(function(){
                var shreLink, url, prefix,
                    href = $(this).attr("href"),
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
                $(this).attr("href", href);

            });
        }

        return this;
    }

    var blogger = (new Blogger()).init();
})(jQuery);