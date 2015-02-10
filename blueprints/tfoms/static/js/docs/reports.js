/**
 * Created with PyCharm.
 * User: santipov
 * Date: 12.08.13
 * Time: 14:41
 * To change this template use File | Settings | File Templates.
 */
function modIntro(){
    var steps = [];
    if ($('#filter').length){
        steps.push({
            element: '#filter',
            intro: "Форма фильтрации реестров по датам.<br>В отчёте отображаются реестры, согласно указанным датам.",
            position: 'bottom'
        });
    }
    if ($('#reports_table').length){
        steps.push({
            element: '#reports_table',
            intro: "Таблица с перечнем выгруженных реестров. При нажатии на номер реестра отображается информации по конкретному реестру.",
            position: 'bottom'
        });
    }
    if ($('#summary').length){
        steps.push({
            element: '#summary',
            intro: "Итоговая информация по количеству выгруженных реестров и суммах оплаты.",
            position: 'bottom'
        });
    }
    if ($('#print').length){
        steps.push({
            element: '#print',
            intro: "Печать отчёта по выгруженным реестрам за указанный период",
            position: 'right'
        });
    }

    intro.setOptions({
        steps: steps
    });
}