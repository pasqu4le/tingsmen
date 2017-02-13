function hide_comments(post_id, depth) {
    // hide every comment of post_id
    $('#post-' + post_id + '-comments').html("");
    // change button to show comment if pressed again
    $("#load_comment_button_" + post_id).attr("onclick", "Sijax.request('load_comments', [" + post_id + ", " + depth + "]);");
}