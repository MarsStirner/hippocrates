$('form').submit(function(){
    $('body').addClass("loading");
});
$(function() {
    $('#filter_report').keyup(function(){
        var phrase = $(this).val();
        $('.result_table').each(function(){
            filter(phrase, $(this).get(0));
        });
        $('#result_table').each(function(){
            filter(phrase, $(this).get(0));
        });
    });
});