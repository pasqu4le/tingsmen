$(document).ready(function() {
    $( "#add_law_form" ).click(function() {
        // clone the list field last child
        $('#new-law-form-container').children().last().clone().appendTo('#new-law-form-container')
        nw = $('#new-law-form-container').children().last()
        // get the progressive number in his id
        rn = nw.children().first().attr("id").match(/\d+/);
        rn = rn * 1 + 1
        // set next number his input's attributes
        nw.find('input, textarea').each(function(){
            $(this).attr("name", $(this).attr("name").replace(/\d+/, rn) );
            $(this).attr("id", $(this).attr("id").replace(/\d+/, rn) );
            $(this).val("")
        });
    });
    $( "#remove_law" ).click(function() {
        // clone the list field last child
        $('#remove-law-container').children().last().clone().appendTo('#remove-law-container')
        nw = $('#remove-law-container').children().last()
        // get the progressive number in his id
        rn = nw.children().first().children().first().attr("id").match(/\d+/);
        rn = rn * 1 + 1
        // set next number his input's attributes
        nw.find('input').each(function(){
            $(this).attr("name", $(this).attr("name").replace(/\d+/, rn) );
            $(this).attr("id", $(this).attr("id").replace(/\d+/, rn) );
            $(this).val("")
        });
    });
});