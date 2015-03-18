function modIntro(){
    var steps = [];
    if ($('#tpl_types').length){
        steps.push({
            element: '#tpl_types',
            intro: "Типы настраиваемых шаблонов, по которым в дальнейшем будет производится выгрузка",
            position: 'bottom'
        });
    }
    if ($('#exists').length){
        steps.push({
            element: '#exists',
            intro: "Перечень созданных шаблонов.<br>Для редактирования существующего шаблона необходимо кликнуть по его названию.<br>Шаблон, помеченный выбранным радиобаттоном/чекбоксом доступен для выгрузки в интерфейсе выгрузки данных для ТФОМС.",
            position: 'right'
        });
    }
    var $choose = $('input.is_active');
    if ($choose.length){
        steps.push({
            element: $choose.get(0),
            intro: "Выбор шаблона(ов), который будет доступен для выгрузки в интерфейсе выгрузки данных для ТФОМС.",
            position: 'right'
        });
    }
    var $add = $('#exists').find('.btn');
    if ($add.length){
        steps.push({
            element: $add.get(0),
            intro: "Создание нового шаблона",
            position: 'right'
        });
    }
    var $main_form = $('#main_form');
    if ($main_form.length){
        steps.push({
            element: $main_form.get(0),
            intro: "Форма для указания параметров шаблона: <ul><li>названия шаблона</li><li>признака архивации (если установлен выгруженный файл будет помещён в архив)</li><li>тегов, составляющих структуру выгружаемого файла</li></ul>",
            position: 'left'
        });
    }
    var $used = $main_form.find('#used');
    if ($used.length){
        steps.push({
            element: $used.get(0),
            intro: 'Теги описывают структуру выгружаемого файла (набор, вложенность и порядок следования тегов).<br>Теги можно перемещать с помощью "мыши".',
            position: 'left'
        });
    }
    var $unused = $main_form.find('#unused');
    if ($unused.length){
        steps.push({
            element: $unused.get(0),
            intro: 'Теги, перемещённые в колонку "Не используются", не участвуют в формировании выгружаемых файлов. С помощью "мыши" тег можно вернуть в колонку "Попадают в реестр".',
            position: 'left'
        });
    }
    var $del_btn = $main_form.find('#confirm-delete');
    if ($del_btn.length){
        steps.push({
            element: $del_btn.get(0),
            intro: "Удаление текущего (выбранного) шаблона",
            position: 'top'
        });
    }
    var $save_as_new = $main_form.find('#Save_as_new');
    if ($save_as_new.length){
        steps.push({
            element: $save_as_new.get(0),
            intro: "Создание нового шаблона на основе текущего, с сохранением указанного набора и порядка следования тегов.<br>Для нового шаблона необходимо задать уникальное имя.",
            position: 'top'
        });
    }
    var $save = $main_form.find('#Save');
    if ($save.length){
        steps.push({
            element: $save.get(0),
            intro: "Создать новый шаблон или сохранить изменения в редактируемом шаблоне",
            position: 'left'
        });
    }

    intro.setOptions({
        steps: steps
    });
}