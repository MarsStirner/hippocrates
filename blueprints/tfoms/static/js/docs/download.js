function modIntro(){
    var steps = [];
    if ($('#download_xml').length){
        steps.push({
            element: '#download_xml',
            intro: "Формирование файлов выгрузки реестров в формате XML",
            position: 'bottom'
        });
    }
    if ($('#download_dbf').length){
        steps.push({
            element: '#download_dbf',
            intro: "Формирование файлов выгрузки реестров в формате DBF",
            position: 'bottom'
        });
    }
    if ($('#download_form').length && $("#download_form").is(":visible")){
        steps.push({
            element: '#download_form',
            intro: "Форма для указания параметров выгрузки (периода и шаблонов выгрузки)",
            position: 'top'
        });
    }
    if ($('#download_dates').length){
        steps.push({
            element: '#download_dates',
            intro: "Указание периода выгрузки.<br>Реестры оказанных услуг формируются за указанные даты.",
            position: 'right'
        });
    }
    if ($('#download_templates').length){
        steps.push({
            element: '#download_templates',
            intro: "Выбор шаблонов для выгрузки.<br><b>Замечание: </b>Для первоначальной выгрузки услуг необходимо совместно выгрузить и пациентов.",
            position: 'right'
        });
    }
    var $btn = $('form#download_form').find('.btn');
    if ($btn.length){
        steps.push({
            element: $btn.get(0),
            intro: "Запуск процесса генерации файлов с выбранными реестрами.<br>По завершению генерации на месте формы появятся ссылки для скачивания файлов.<br><b>Замечание: </b>Процесс генерации файлов занимает несколько минут, необходимо дождаться его завершения.",
            position: 'right'
        });
    }
    if ($('#download_result').length && $("#download_result").is(":visible")){
        steps.push({
            element: '#download_result',
            intro: "Сформированные файлы, доступные для скачивания",
            position: 'right'
        });
    }

    intro.setOptions({
        steps: steps
    });
}