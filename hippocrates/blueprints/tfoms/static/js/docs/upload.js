function modIntro(){
    var steps = [];
    var $file_btn = $('form#upload_form').find('.fileinput-button');
    if ($file_btn.length){
        steps.push({
            element: $file_btn.get(0),
            intro: "Выбор файла из файловой системы, содержащего данные для загрузки из ТФОМС",
            position: 'bottom'
        });
    }
    if ($('#upload_submit').length){
        steps.push({
            element: '#upload_submit',
            intro: "Запуск процесса загрузки данных, полученных из ТФОМС",
            position: 'bottom'
        });
    }

    intro.setOptions({
        steps: steps
    });
}