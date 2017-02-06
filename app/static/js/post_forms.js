// buttons that will close the collapsable post form should have the .collapser class
$(document).on("click", ".collapser", function(event) {
    var button = $(event.target)
    var autofill = button.data('autofill');
    var post_form = $('#collapsable_post_form');

    // collapse immediately:
    post_form.attr('class', 'collapse');

    // move in the correct position:
    post_form.appendTo(autofill.destination);

    // reset or set data:
    post_form.find('#content').val("");
    if (autofill.id != null){
        post_form.find('#parent_id').val(autofill.id);
    } else {
        post_form.find('#parent_id').val("");
    }
    if (autofill.topics != null){
        post_form.find('#topics').val(autofill.topics);
    } else {
        post_form.find('#topics').val("");
    }

    // finally de-collapse
    post_form.collapse('show');
});