
function buildDatetimePickerField(picker_field, input_picker_field, initial){
    var picker_field = $(picker_field);
    var input_picker_field = $(input_picker_field);
    picker_field.datetimepicker({
        altField: input_picker_field,
        alwaysSetTime:false,
        altFieldTimeOnly: false,
        timeFormat: 'hh:mm TT Z',
    });

    function _setDate(value){
        if (!value){
            picker_field.datetimepicker('setDate', null);
            input_picker_field.val('')
        }
        else{
            picker_field.datetimepicker('setDate', value);
        }
    }
    // clear whatever values exists
    _setDate(null);

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

    //set initial value (passed as string from the server)
    if(initial){
        picker_field.datetimepicker('setDate', new Date(initial));
    }
}
