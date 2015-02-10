# -*- coding: utf-8 -*-
import re
import datetime
from HTMLParser import HTMLParser
# from PyQt4.QtCore import QDate, QTime

__author__ = 'mmalkov'


class HTMLRipper(HTMLParser, object):
    u"""Класс-хэндлер для потрошения кода HTML
    с целью приведения его к правильному виду, а, самое главное,
    вычщение из него всей информации о начертании и кеглях
    шрифтов и подменой на заданные"""
    # Список запрещённых тегов. То есть ни сами эти теги, ни всё их содержимое выходить не будут
    disallowed_tags = ['style', 'link']
    # Список разрешённых тегов. Если список задан, то только эти теги будут оттранслированы в выхлоп
    allowed_tags = ['b', 'i', 'u', 's', 'div', 'span', 'p']
    # Список вычищаемых тегов. Аналогично запрещённым тегам, эти теги не попадают в выхлоп, но всё их
    # содержимое - попадает
    stripout_tags = ['html', 'body', 'head', 'meta']


    @staticmethod
    def ultimate_rip(data):
        """Вспомогательная функция вычищения тэгов. Оставляет ничего"""
        ripper = HTMLParser()
        from types import MethodType
        ripper.handle_data = MethodType(lambda self, d: self.fed.append(d), ripper, HTMLParser)
        ripper.get_data = MethodType(lambda self: u''.join(self.fed), ripper, HTMLParser)
        ripper.fed = []
        ripper.feed(data)
        return ripper.get_data()

    @staticmethod
    def hard_rip(data):
        """Вспомогательная функция вычищения тэгов. Оставляет только тэги <p> и <span>,
        оставляя в их стилях только размеры и гарнитуру шрифтов _по умолчанию_."""
        ripper = HTMLRipper()
        ripper.allowed_tags = ['p', 'span']
        ripper.feed(data)
        return replace_first_paragraph(ripper.to_string_no_html())

    @staticmethod
    def soft_rip(data):
        """Вспомогательная функция вычищения тэгов. Оставляет все тэги по умполчанию, изменяя
        в них только размеры и гарнитуру на значения по умпочанию"""
        ripper = HTMLRipper()
        ripper.feed(data)
        return replace_first_paragraph(ripper.to_string_no_html())

    @staticmethod
    def gentle_rip(data):
        """Вспомогательная функция вычищения тэгов. Оставляет все тэги,
        оставляя в их стилях только размеры и гарнитуру шрифтов _по умолчанию_."""
        ripper = HTMLRipper()
        ripper.allowed_tags = None
        ripper.feed(data)
        return ripper.to_string_no_html()

    def __init__(self, family = 'Times New Roman', size = 12):
        """\param family: font-family style attribute
        \param size: font-size style attribute
        Запуск преобразования производится методом feed()
        Результаты можно получить методами to_string() и
        to_string_no_html()"""
        super(HTMLRipper, self).__init__()
        self.__family = family
        self.__size = size
        self.__guts = []
        self.__current_element = []
        self.allowed_tags = HTMLRipper.allowed_tags
        self.disallowed_tags = HTMLRipper.disallowed_tags
        self.stripout_tags = HTMLRipper.stripout_tags
        self.style_function = self.style_stripFont

    def feed(self, data):
        # сохраняем на случай неудачи
        self.__fed_data = data
        super(HTMLRipper, self).feed(data)

    def style_stripFont(self, paramDict):
        """Функция, вырезающая из стиля тега кегль и гарнитуру шрифта
        @param paramDict: набор из названий параметра стиля и его значения
        @return новый стиль
        """
        params_result = {}
        for param, value in paramDict.iteritems():
            if param in (
                'text-decoration', 'font-style', 'font-weight',
                '-qt-paragraph-type', '-qt-block-indent',  'vertical-align',
                # 'text-indent', 'margin-top', 'margin-bottom', 'margin-left', 'margin-right',
            ):
                params_result[param] = value
        return params_result

    def style_changeFont(self, paramDict):
        """Функция, заменяющая в теге кегль и гарнитуру шрифта
        @param paramDict: набор из названий параметра стиля и его значения
        @return новый стиль
        """
        params_result = {}
        for param, value in paramDict.iteritems():
            if param == 'font-family':
                params_result['font-family'] = self.__family
            elif param == 'font-size':
                params_result['font-size'] = "%ipt" % self.__size
            else:
                params_result[param] = value
        return params_result

    def handle_starttag(self, name, attrs):
        """Обработка открывающего тэга"""
        name = name.lower()
        # Запрещенные теги учитывать, но не обрабатывать
        if name in self.disallowed_tags + self.stripout_tags:
            self.__current_element.append(name)
            return
        # Если мы в запрещённом теге, всё бросить, и сбежать
        if len(self.__current_element) > 0:
            if self.__current_element[-1] in self.disallowed_tags:
                return
        # <br /> тупо повторить
        if name == "br":
            self.__guts.append("<br />")
            return
        # Разбираемся с тем, пользуемся ли мы списком разрешённых тегов или нет
        if (self.allowed_tags is None) or (name in self.allowed_tags):
            self.__current_element.append(name)
            attrs = dict(attrs)
            # обрабатываем параметр "стиль", если он есть
            style = attrs.get("style", None)
            if style:
                # Шинкуем на отдельные параметры, разделяем на [key, value], и убираем лишние пробелы
                params = map(lambda w: w.split(':', 1), style.split(';'))
                params = map(lambda w: (w[0].strip(), w[1].strip() if len(w) == 2 else None), params)  # Фигачим туплы
                params_result = self.style_function(dict(params))
                # Формируем кишки опции style текущего тега
                attrs["style"] = '; '.join(map(lambda w: '%s: %s' % (w[0], w[1]) if w[1] else w[0],
                                               params_result.iteritems()))
                # Формируем кишки тега. Да, тут появляется лишний пробел, но, как-то, пофиг.
            gut = "<%s %s>" % (name, " ".join(map(lambda item: '%s="%s"' % (item[0], item[1]), attrs.iteritems())))
            self.__guts.append(gut)

    def handle_endtag(self, name):
        """Обработка закрывающего тэга"""
        name = name.lower()
        if name == 'br':
            return
        if len(self.__current_element) > 0:
            if self.__current_element[-1] in self.disallowed_tags + self.stripout_tags:
                if name == self.__current_element[-1]:
                    self.__current_element.pop()
                return
            else:
                if name == self.__current_element[-1]:
                    self.__current_element.pop()
        # Разбираемся с тем, пользуемся ли мы списком разрешённых тегов или нет
        if (self.allowed_tags is None) or (name in self.allowed_tags):
            gut = "</%s>" % name
            self.__guts.append(gut)

    def handle_entityref(self, name):
        """Обработка именованных сущностей типа &amp;"""
        self.__guts.append("&%s;" % name)

    def handle_charref(self, name):
        """Обработка именованных сущностей типа &amp;"""
        self.__guts.append("&#%s;" % name)

    def handle_data(self, ch):
        """Обработка текста внутри тэгов"""
        if len(self.__current_element) > 0:
            if not self.__current_element[-1] in self.disallowed_tags:
                self.__guts.append(ch.rstrip())

    def to_string(self):
        """Приведение к плоскому виду (строке)"""
        return '<html><head></head><body style="font-family: %s; font-size: %ipt">\n%s\n</body></html>' % \
            (self.__family, self.__size, "".join(self.__guts) if self.__guts else self.__fed_data)

    def to_string_no_html(self):
        """Приведение к строке"""
        result = "".join(self.__guts) if self.__guts else self.__fed_data
        return result


first_paragraph_re = re.compile('<p([\s>])', re.I)
first_paragraph_re2 = re.compile('</p>', re.I)


def replace_first_paragraph(string):
    return first_paragraph_re2.sub(
        '</span>',
        first_paragraph_re.sub(
            '<span\1',
            string,
            1),
        1)


def convenience_HtmlRip(value):
    ripper = HTMLRipper()
    ripper.allowed_tags = None
    ripper.feed(u'<html>%s</html>' % value)
    return ripper.to_string_no_html()


def escape(s):
    return unicode(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace('\'', '&#39;')


def escapenl(s):
    return escape(s).replace('\n', '<BR/>')


def date_toString(date, format):
    format = re.sub(r"dddd", r"%A", format)
    format = re.sub(r"ddd", r"%a", format)
    format = re.sub(r"dd", r"%d", format)
    format = re.sub(r"([^%d])d", r"\1%d", format)
    format = re.sub(r"MMMM", r"%B", format)
    format = re.sub(r"MMM", r"%b", format)
    format = re.sub(r"MM", r"%m", format)
    format = re.sub(r"([^%M])M", r"\1%m", format)
    format = re.sub(r"yyyy", r"%Y", format)
    format = re.sub(r"yy", r"%y", format)
    if date:
        date = date.strftime(format)
    return date


def time_toString(time, format):
    format = re.sub(r"HH", r"%H", format)
    format = re.sub(r"([^%H])H", r"\1%H", format)
    format = re.sub(r"hh", r"%H", format)
    format = re.sub(r"([^%h])h", r"\1%H", format)
    format = re.sub(r"mm", r"%M", format)
    format = re.sub(r"([^%m])m", r"\1%M", format)
    format = re.sub(r"ss", r"%S", format)
    format = re.sub(r"([^%s])s", r"\1%S", format)
    if time:
        time = time.strftime(format)
    return time


def addDays(date, num_of_days):
    return date + datetime.timedelta(days=num_of_days)
#
# def date_toString(object_QDate, format):
#     return QDate.toString(object_QDate, format)
#
#
# def time_toString(object_QTime, format):
#     return QTime.toString(object_QTime, format)
