function paginate_table(obj, container) {
    var currentPage = 0;
    var numPerPage = 100;
    var $table = obj;
    $table.bind('repaginate', function() {
        $table.find('tbody tr').hide().slice(currentPage * numPerPage, (currentPage + 1) * numPerPage).show();
    });
    $table.trigger('repaginate');
    var numRows = $table.find('tbody tr').length;
    var numPages = Math.ceil(numRows / numPerPage);
    var $pager = $('<div class="pagination pagination-mini pagination-centered"></div>');
    var $ul = $('<ul></ul>');
    $ul.appendTo($pager);
    for (var page = 0; page < numPages; page++) {
        $('<li><a href="javascript:void(0);">' + (page + 1) + '</a></li>').bind('click', {
            newPage: page
        }, function(event) {
            currentPage = event.data['newPage'];
            $table.trigger('repaginate');
            $(this).addClass('active').siblings().removeClass('active');
        }).appendTo($ul);
    }
    $pager.find('li:first').addClass('active');
    $pager.appendTo(container);
}