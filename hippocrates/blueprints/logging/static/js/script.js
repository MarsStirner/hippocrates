$(function() {
    $('#filter_result').keyup(function(){
        var phrase = $(this).val();
        $('.result_table').each(function(){
            filter(phrase, $(this).get(0));
        });
        $('#result_table').each(function(){
            filter(phrase, $(this).get(0));
        });
    });
});