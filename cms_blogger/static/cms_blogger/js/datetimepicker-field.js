
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
        //use moment.js to format date appropriately for IE8
        initial = new Date(moment(initial));
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
            picker_field.datetimepicker('setDate', new Date(value));
        }
    }

    // used for parsing the date from the visible input;
    // currently this has an invalid format
    function parseDate(d){
        // d should be in the following format : 5/22/2014 13:00 AM
        // returns Date object
        // fallback to current time if something goes wrong or invalid

        if (!d || typeof d !== 'string'){
            return new Date();
        }

        d = d.split(" ");
        var date = d[0];
        var time = d[1];
        var tt = d[2];

        if(!date || !time || !tt){
            return new Date();
        }

        //use only 12H format
        if(parseInt(time.split(":")[0], 10) > 12){
            return new Date();
        }else{
            if(tt.toUpperCase() == "PM"){
                time = time.split(":");
                time[0] = (time[0] === "12" ? "00" : parseInt(time[0], 10) + 12+"");
                time = time.join(":");
            }
            return new Date(date +" "+time);
        }
    }

    picker_field.datetimepicker({
        altField: input_picker_field,
        alwaysSetTime:false,
        altFieldTimeOnly: false,
        timeFormat: 'hh:mm TT',
        buttons: {'Reset': function(){ _setDate(initial); return false;}}
    });

    _setDate(initial);

    //remove all event handlers; IE8 wierd bug (lose focus when clicking inside input)
    input_picker_field.off();
    // change calendar date when input changes
    input_picker_field.on('blur' , function () {
        _setDate(parseDate($(this).val()));
    });

    input_picker_field.keypress(function(event){
        var enter_key = 13;
        if(event.keyCode == enter_key){
            _setDate(parseDate($(this).val()));
            event.preventDefault(); //prevent form submission
        }
    });
}
