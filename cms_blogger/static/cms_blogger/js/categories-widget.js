$(function(){

    $.widget("cmsblogger.tagitX", $.ui.tagit, {
        getTag: function (label) {
            return this._findTagByLabel(label);
        },
        getTagInput: function () {
            return this.tagInput;
        },
        allTags: function () {
            return this._tags();
        },
        lastTag: function () {
            return this._lastTag();
        }
    });

    var tagit_el = $('input[name="categories"]:first');
    var original_categories = new Array();
    var slug_preview = $('<p id="category-slug"></p>')
        .addClass('ui-widget-content ui-corner-all').css({
            'padding': '5px',
            'color': '#2e6e9e',
            'display': 'none',
            'margin-left': '105px'
        }).insertAfter(tagit_el);


    function prevSlug(slug) {

        var url = $('div.field-site p:first').text() + '/blogs/' + $('input[name="slug"]:first').val() + '/category';
        var text = url + "/" + slug + "/";
        if (!slug) {
            text = url + '<span class="ui-state-error"><strong>/&lt;no-slug&gt;/</strong></span>';
        } else {
            for (var i = 0; i < original_categories.length; i++) {
                var label = original_categories[i];
                if (URLify(label) === slug){
                    text = '<a href="http://'+ text +'">'+ text +'</a>';
                    break;
                }
            }
        }
        slug_preview.html("Category available at: " + text).show();
    }

    function validateLabelTag(label) {

        function setError(show) {
            var elem = tagit_el.tagitX('getTagInput');
            if (show) {
                elem.addClass("ui-state-error ui-corner-all");
            } else {
                elem.removeClass("ui-state-error ui-corner-all");
            }
        }

        if (!label) {
            setError(false);
            return true;
        }
        if (label.length < 3 || label.length > 30) {
            prevSlug("");
            setError(true);
            return false;
        }

        var slug = URLify(label);
        // show in preview no matter what
        prevSlug(slug);

        if (!slug) {
            setError(true);
            return false;
        }
        // check duplicate slugs
        var all_tags = tagit_el.tagitX("assignedTags");
        for (var i = 0; i < all_tags.length; i++) {
            var current_tag = all_tags[i];
            if (URLify(current_tag) == slug) {
                setError(true);
                tagit_el.tagitX('getTag', current_tag).stop(true, true).effect('highlight');
                return false;
            }
        }
        setError(false);
        return true;
    }

    function set_tags_inactive() {
        tagit_el.tagitX('allTags').each(function (i, tag) {
            $(tag).removeClass('active-tag');
        });
    }

    function set_tag_active(who) {
        var tag;
        if (!who) {
            tag = tagit_el.tagitX('lastTag');
        } else {
            tag = who;
        }
        set_tags_inactive();
        tag.addClass('active-tag');
        prevSlug(URLify(tagit_el.tagitX('tagLabel', tag)));
    }

    tagit_el.tagitX({
        allowSpaces: true,
        removeConfirmation: true,
        caseSensitive: false,
        placeholderText: 'Add categories...',
        preprocessTag: function (val) {
            if (!val) {
                return '';
            }
            val = val.toLowerCase();
            return val.replace(/^[\s\xA0]+|[\s\xA0]+$/g, '');
        },
        beforeTagAdded: function (event, ui) {
            if (!ui.duringInitialization) {
                return validateLabelTag(ui.tagLabel);
            } else {
                original_categories.push(ui.tagLabel);
            }
        },
        beforeTagRemoved: function (event, ui) {
            return confirm("Are you sure you want to remove this category? Some entries from this blog may remain uncategorized.");
        },
        afterTagAdded: function (event, ui) {
            set_tag_active(ui.tag);
        },
        afterTagRemoved: function (event, ui) {
            set_tag_active();
        },
        onTagClicked: function (event, ui) {
            set_tag_active(ui.tag);
        }
    }).tagitX('getTagInput').attr('maxlength', '30').on('keyup', function () {
        if ($(this).val()) {
            set_tags_inactive();
        } else if (tagit_el.tagitX('allTags').length === 0) {
            set_tags_inactive();
            slug_preview.hide();
        } else {
            set_tag_active();
        }
        validateLabelTag($(this).val());
    });
    original_categories = tagit_el.tagitX('assignedTags');
});
