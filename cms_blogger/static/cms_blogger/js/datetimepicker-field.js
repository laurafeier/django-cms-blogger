
// ugly way of extending datetimepicker to allow other buttons in the buttonpane
if (!$.datepicker.___super_updateDatepicker){
    $.datepicker.__super_updateDatepicker = $.datepicker._updateDatepicker;
    $.datepicker._updateDatepicker = function (inst) {
        this.__super_updateDatepicker(inst);
        var tp_inst = this._get(inst, 'timepicker');
        if(!tp_inst){
            return;
        }

        var buttons = tp_inst._defaults.buttons;
        var buttonPane = tp_inst.$input.find(".ui-datepicker-buttonpane").first();
        if (!buttons || !buttonPane){
            return;
        }

        for (var name in buttons) {
            var btn = $('<button />').addClass(
                'ui-state-default ui-priority-secondary ui-corner-all');
            btn.text(name).click(function(){
                return buttons[name]();
            });
            btn.appendTo(buttonPane);
        }

    };
}

function buildDatetimePickerField(picker_field, input_picker_field, initial){
    var picker_field = $(picker_field);
    var input_picker_field = $(input_picker_field);

    if(initial){
        initial = new Date(initial);
    } else {
        initial = null;
    }

    function _setDate(value){
        if (!value){
            // reset sliders first
            picker_field.datetimepicker('setDate', new Date(0,0,0,1,0,0));
            picker_field.datetimepicker('setDate', null);
            input_picker_field.val('')
        } else {
            picker_field.datetimepicker('setDate', value);
        }
    }

    picker_field.datetimepicker({
        altField: input_picker_field,
        alwaysSetTime:false,
        altFieldTimeOnly: false,
        timeFormat: 'hh:mm TT Z',
        buttons: {'Reset': function(){ _setDate(initial); return false;}}
    });

    _setDate(initial);

    // change calendar date when input changes
    input_picker_field.on('blur' , function () {
        _setDate($(this).val());
    });
    input_picker_field.keypress(function(event){
        var enter_key = 13;
        if(event.keyCode == enter_key){
            _setDate($(this).val());
        }
    });
}