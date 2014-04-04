$(document).ready(function () {
    $("body").on({
        ajaxStart: function() {
            $(this).addClass("loading");
        },
        ajaxStop: function() {
            $(this).removeClass("loading");
        }
    });
});