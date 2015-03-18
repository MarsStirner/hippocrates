function modIntro(){
    var steps = [];
    if ($('form').length){
        steps.push({
            element: 'form',
            intro: "Форма редактирования настроек модуля",
            position: 'bottom'
        });
    }

    intro.setOptions({
        steps: steps
    });
}