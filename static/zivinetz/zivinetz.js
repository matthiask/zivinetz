$(function() {
    $.datepicker.setDefaults({
        changeYear: true,
        changeMonth: true,
        dateFormat: 'dd.mm.yy',
        firstDay: 1
    });

    $('input.dateinput').datepicker();
});
