$(function() {
    $.datepicker.setDefaults({
        changeYear: true,
        changeMonth: true,
        dateFormat: 'dd.mm.yy',
        firstDay: 1,
        yearRange: 'c-40:c+40'
    });

    $('input.dateinput').datepicker();


    var searchbox = $('.searchbox');
    var query_input = searchbox.find('input[name=query]');
    if(searchbox.hasClass('searching')) {
        query_input.focus();
    } else {
        searchbox.find('table').hide();
        query_input.focus(function(){
            searchbox.find('table').slideDown();
        }).click(function(){
            searchbox.find('table').slideDown();
        }).keyup(function(event){
            if(event.keyCode==27)
                searchbox.find('table').slideUp();
        });
    }

});
