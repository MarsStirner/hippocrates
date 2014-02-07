Hippocrates
===========

WebMIS 2

Установка проекта
-----------

1. ```git clone```
2. ```git pull && git submodule init && git submodule update && git submodule status``` - получаем подмодули (simplelogs)
3. Создать и активировать virtualenv 
4. Установить зависимости ```pip install -r requirements/mysql.txt```
5. Скопировать предоставляемый конфиг в корень проекта ```cp dicst/config_local.py_mysql config_local.py```
6. Отредактировать локальный конфиг config_local.py (в частности, прописать параметры подключения к БД)

**Старт проекта**

Run wsgi.py

Login: admin

Password: admin


Структура проекта
-----------

**application/** - директория приложения, содержит в себе пакеты и модули, обеспечивающие функционирование приложения, а также вспомогательные утилиты для автоподключения блюпринтов, тестов; каркас шаблонов и систему авторизации.

**application/static/** - содержит js/css/img, используемые во всём приложении, такие как bootstrap, jquery, angularjs. Нет необходимости держать их в каждом отдельном блюпринте, они подключаются в базовом шаблоне приложения

**application/templates/** - базовые шаблоны приложения, от которых наследуются шаблоны всех модулей, шаблоны уже содержат в себе подключение необходимых стилей, js-библиотек, реализуют каркас интерфейсов для всех страниц


**blueprints/** - директория, из которой подключаются блюпринты. Flask-приложение автоматически подцепляет блюпринты из этой директории.

**blueprints/sample/** - пример блюпринта (модуля приложения), который необходимо взять за основу, при разработке своих модулей

**blueprints/sample/app.py** - создание flask-blueprint, реализующего текущий модуль

**blueprints/sample/config.py** - настройки модуля, например русское имя, которое будет фигурировать в главном меню

**blueprints/sample/models.py** - sqla-модели текущего модуля. В проекте используется Flask-SqlAlchemy, поэтому при описании своих моделей удобно использовать объект db
(http://pythonhosted.org/Flask-SQLAlchemy/quickstart.html#simple-relationships)

**blueprints/sample/lib/** - складывайте все утилитарные или вспомагательные python-классы в директорию lib

**blueprints/sample/static/** - дополнительные js/css/img, используемые только в данном блюпринте. Разрабатывайте js-скрипты и css-стили для своего модуля внутри этой директории. При подключении в шаблонах модуля используйте относительный путь ".static":

```
<link href="{{ url_for('.static', filename='css/style.css') }}" media="screen" rel="stylesheet">
```

**blueprints/sample/templates/** - jinja2-шаблоны, используемые в текущем блюпринте. Для того, чтобы избежать конфликтов подключения с шаблонами других модулей необходимо шаблоны модуля помещать во вложенную директорию, для простоты можно именовать её так же, как сам модуль: **blueprints/sample/templates/sample/**, тогда во view при рендере шаблона указывается относительный путь: 

```
render_template('sample/index.html')
```

**blueprints/sample/templates/sample/base.html** - базовый шаблон модуля, наследуется от blueprints/application/templates/base.html, т.е. содержит в себе общие для приложения js/css/img, за счёт чего обеспечивается единый вид интерфейсов. Сам блюпринт работает только с центральной частью страницы, шапка и подвал являются общими для всех интерфейсов приложения. 
Все шаблоны модуля удобно наследовать от blueprints/sample/templates/sample/base.html:

```
{% extends 'sample/base.html' %}
```

Тогда сам шаблон конкретного интерфейса содержит только:

```
{% extends 'sample/base.html' %}

{% block main %}
    <legend>Пример</legend>
    <div class="">
    {{ lipsum(5) }}
    </div>
{% endblock %}
```

Весь код интерфейса содержится внутри блока *main*.

В случае, если вам необходимо писать inline-js или подключить отдельный скрипт для данного интерфейса воспользуйтесь блоком **{% block modules_js %}**:

```
{% block modules_js %}
    {{ super() }}
    <script type="text/javascript">
        $(function() {

        });
    </script>
{% endblock %}
```

Тогда скрипт будет подключаться в конце страницы и не будет вносить задержку в первоначальную отрисовку html-элементов при загрузке страницы.

Для подключения дополнительных стилей можно воспользоваться блоком **{% block modules_css %}**

```
{% block modules_css %}

{{ super() }}

<link href="{{ url_for('.static', filename='css/style.css') }}" media="screen" rel="stylesheet">
<link href="{{ url_for('.static', filename='css/print.css') }}" media="print" rel="stylesheet">
{% endblock %}
```

Тогда стили будут подключены в ```<head></head>``` страницы, что гарантирует отображение html-элементов в необходимом виде сразу же при первоначальной отрисовке страницы.
