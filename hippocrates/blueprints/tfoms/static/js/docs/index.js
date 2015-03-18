function modIntro(){
    var steps = [];
    if ($('#index').length){
        steps.push({
            element: '#index',
            intro: "Главная страница подсистемы выгрузки в ТФОМС",
            position: 'bottom'
        });
    }
    if ($('#download').length){
        steps.push({
            element: '#download',
            intro: "Формирование файлов выгрузки для выбранных реестров",
            position: 'bottom'
        });
    }
    if ($('#upload').length){
        steps.push({
            element: '#upload',
            intro: "Загрузка подтвержденных и/или исправленных реестров, полученных из ТФОМС",
            position: 'bottom'
        });
    }
    if ($('#reports').length){
        steps.push({
            element: '#reports',
            intro: "Просмотр и печать отчетов по осуществленным выгрузкам",
            position: 'bottom'
        });
    }
    if ($('#mod_settings').length){
        steps.push({
            element: '#mod_settings',
            intro: "Настройка модуля. Настройка шаблонов выгрузки",
            position: 'bottom'
        });
    }

    intro.setOptions({
        steps: steps
    });
}