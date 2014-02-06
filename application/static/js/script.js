function filter(phrase, table){
    var words = phrase.toLowerCase().split(" ");
    var ele;
    if (table.tBodies.length > 0){
        table = table.tBodies[0];
    }
    for (var r = 0; r < table.rows.length; r++){
        ele = table.rows[r].innerHTML.replace(/<[^>]+>/g,"");
        var displayStyle = 'none';
        for (var i = 0; i < words.length; i++) {
            if (ele.toLowerCase().indexOf(words[i])>=0){
                displayStyle = '';
            }else {
                displayStyle = 'none';
                break;
            }
        }
        table.rows[r].style.display = displayStyle;
    }
}