/* http://github.com/mindmup/bootstrap-wysiwyg */
/*global jQuery, $, FileReader*/
/*jslint browser:true*/
'use strict';
angular.module('WebMis20.directives.wysiwyg', [])
.directive('wysiwyg', ['$q', '$compile', '$templateCache', function ($q, $compile, $templateCache) {
    var readFileIntoDataUrl = function (fileInfo) {
        var loader = $q.defer(),
            fReader = new FileReader();
        fReader.onload = function (e) {
            loader.resolve(e.target.result);
        };
        fReader.onerror = loader.reject;
        fReader.onprogress = loader.notify;
        fReader.readAsDataURL(fileInfo);
        return loader.promise;
    };
    var cleanHtml = function (html) {
        return html && html.replace(/(<br>|\s|<div><br><\/div>|&nbsp;)*$/, '');
    };
    var defaults = {
        hotKeys: {
            'ctrl+b meta+b': 'bold',
            'ctrl+i meta+i': 'italic',
            'ctrl+u meta+u': 'underline',
            'ctrl+z meta+z': 'undo',
            'ctrl+y meta+y meta+shift+z': 'redo',
            'ctrl+l meta+l': 'justifyleft',
            'ctrl+r meta+r': 'justifyright',
            'ctrl+e meta+e': 'justifycenter',
            'ctrl+j meta+j': 'justifyfull',
            'shift+tab': 'outdent',
            'tab': 'indent'
        },
        toolbarSelector: '[data-role=editor-toolbar]',
        commandRole: 'edit',
        activeToolbarClass: 'btn-info',
        selectionMarker: 'edit-focus-marker',
        selectionColor: 'darkgrey',
        dragAndDropImages: true,
        fileUploadError: function (reason, detail) {
            console.log("File upload error", reason, detail);
        }
    };
    return {
        restrict: 'E',
        scope: {
            userOptions: '='
        },
        require: '^ngModel',
        link: function (scope, element, attributes, ngModel) {
            scope.$model = ngModel;
            var toolbar = $($templateCache.get('/WebMis20/wysiwyg-toolbar.html'));
            var editor = $('<div style="padding: 10px; overflow: scroll;"></div>');
            var replace = $('<div class="panel panel-default" style="padding: 0"></div>');
            toolbar.find('.dropdown-menu input')
                .click(function() {return false;})
                .change(function () {$(this).parent('.dropdown-menu').siblings('.dropdown-toggle').dropdown('toggle');})
                .keydown('esc', function () {this.value='';$(this).change();});
            toolbar.find('[data-role=magic-overlay]')
                .each(function () {
                    var overlay = $(this), target = $(overlay.data('target'));
                    overlay.css('opacity', 0).css('position', 'absolute').offset(target.offset()).width(target.outerWidth()).height(target.outerHeight());
                });
            var selectedRange,
                options,
                toolbarBtnSelector,
                updateToolbar = function () {
                    if (options.activeToolbarClass) {
                        toolbar.find(toolbarBtnSelector).each(function () {
                            var command = $(this).data(options.commandRole);
                            if (document.queryCommandState(command)) {
                                $(this).addClass(options.activeToolbarClass);
                            } else {
                                $(this).removeClass(options.activeToolbarClass);
                            }
                        });
                    }
                },
                execCommand = function (commandWithArgs, valueArg) {
                    var commandArr = commandWithArgs.split(' '),
                        command = commandArr.shift(),
                        args = commandArr.join(' ') + (valueArg || '');
                    document.execCommand(command, 0, args);
                    updateToolbar();
                },
                getCurrentRange = function () {
                    var sel = window.getSelection();
                    if (sel.getRangeAt && sel.rangeCount) {
                        return sel.getRangeAt(0);
                    }
                },
                saveSelection = function () {
                    selectedRange = getCurrentRange();
                },
                restoreSelection = function () {
                    var selection = window.getSelection();
                    if (selectedRange) {
                        try {
                            selection.removeAllRanges();
                        } catch (ex) {
                            document.body.createTextRange().select();
                            document.selection.empty();
                        }

                        selection.addRange(selectedRange);
                    }
                },
                insertFiles = function (files) {
                    editor.focus();
                    $.each(files, function (idx, fileInfo) {
                        if (/^image\//.test(fileInfo.type)) {
                            readFileIntoDataUrl(fileInfo).then(
                                function (dataUrl) {execCommand('insertimage', dataUrl);},
                                function (e) {options.fileUploadError("file-reader", e);}
                            );
                        } else {
                            options.fileUploadError("unsupported-file-type", fileInfo.type);
                        }
                    });
                },
                markSelection = function (input, color) {
                    restoreSelection();
                    if (document.queryCommandSupported('hiliteColor')) {
                        document.execCommand('hiliteColor', 0, color || 'transparent');
                    }
                    saveSelection();
                    input.data(options.selectionMarker, color);
                },
                bindToolbar = function (toolbar, options) {
                    toolbar.find(toolbarBtnSelector).click(function () {
                        restoreSelection();
                        editor.focus();
                        execCommand($(this).data(options.commandRole));
                        saveSelection();
                    });
                    toolbar.find('[data-toggle=dropdown]').click(restoreSelection);

                    toolbar.find('input[type=text][data-{0}]'.format(options.commandRole)).on('webkitspeechchange change', function () {
                        var newValue = this.value;
                        /* ugly but prevents fake double-calls due to selection restoration */
                        this.value = '';
                        restoreSelection();
                        if (newValue) {
                            editor.focus();
                            execCommand($(this).data(options.commandRole), newValue);
                        }
                        saveSelection();
                    }).on('focus', function () {
                        var input = $(this);
                        if (!input.data(options.selectionMarker)) {
                            markSelection(input, options.selectionColor);
                            input.focus();
                        }
                    }).on('blur', function () {
                        var input = $(this);
                        if (input.data(options.selectionMarker)) {
                            markSelection(input, false);
                        }
                    });
                    toolbar.find('input[type=file][data-{0}]'.format(options.commandRole)).change(function () {
                        restoreSelection();
                        if (this.type === 'file' && this.files && this.files.length > 0) {
                            insertFiles(this.files);
                        }
                        saveSelection();
                        this.value = '';
                    });
                },
                initFileDrops = function () {
                    editor.on('dragenter dragover', false)
                        .on('drop', function (e) {
                            var dataTransfer = e.originalEvent.dataTransfer;
                            e.stopPropagation();
                            e.preventDefault();
                            if (dataTransfer && dataTransfer.files && dataTransfer.files.length > 0) {
                                insertFiles(dataTransfer.files);
                            }
                        });
                };
            options = angular.extend({}, defaults, scope.userOptions);
            toolbarBtnSelector = 'a[data-{0}],button[data-{0}],input[type=button][data-{0}]'.format(options.commandRole);
            if (options.dragAndDropImages) {
                initFileDrops();
            }
            bindToolbar(toolbar, options);
            editor.attr('contenteditable', true);
            editor.on('mouseup keyup mouseout', function () {
                if (editor.is(':focus')) {
                    saveSelection();
                    updateToolbar();
                    ngModel.$setViewValue(cleanHtml(editor.html()));
                    ngModel.$render();
                }
            });
            editor.height('200px');

            scope.$watch('$model.$modelValue', function (n, o) {
                if (angular.equals(n, o)) return;
                editor.html(n);
                return n;
            });

            scope.$on('$destroy', function () {
                editor.unbind();
                toolbar.find().each(function () {$(this).unbind()})
            });

            $(window).bind('touchend', function (e) {
                var isInside = (editor.is(e.target) || editor.has(e.target).length > 0),
                    currentRange = getCurrentRange(),
                    clear = currentRange && (currentRange.startContainer === currentRange.endContainer && currentRange.startOffset === currentRange.endOffset);
                if (!clear || isInside) {
                    saveSelection();
                    updateToolbar();
                }
            });
            replace.append(toolbar);
            replace.append(editor);
            $(element).replaceWith(replace);
            $compile(replace)(scope);
        }
    };
}])
.run(['$templateCache', function ($templateCache) {
    var fonts = ['Serif', 'Sans', 'Arial', 'Arial Black', 'Courier', 'Courier New', 'Comic Sans MS', 'Helvetica', 'Impact', 'Lucida Grande', 'Lucida Sans', 'Tahoma', 'Times', 'Times New Roman', 'Verdana'];
    var makeFontSelector = function (fontName) {
        return '<li><a data-edit="fontName {0}" style="font-family:\'{0}\'">{0}</a></li>'.format(fontName)
    };
    $templateCache.put('/WebMis20/wysiwyg-toolbar.html',
        '<div class="btn-toolbar" data-role="editor-toolbar" data-target="#editor">\
            <div class="btn-group">\
                <a class="btn dropdown-toggle" data-toggle="dropdown" title="Font"><i class="icon-font"></i><b class="caret"></b></a>\
                <ul class="dropdown-menu">{0}</ul>\
            </div>\
            <div class="btn-group">\
                <a class="btn dropdown-toggle" data-toggle="dropdown" title="Font Size"><i class="icon-text-height"></i>&nbsp;<b class="caret"></b></a>\
                <ul class="dropdown-menu">\
                    <li><a data-edit="fontSize 4"><font size="4">Крупный</font></a></li>\
                    <li><a data-edit="fontSize 3"><font size="3">Нормальный</font></a></li>\
                    <li><a data-edit="fontSize 2"><font size="2">Мелкий</font></a></li>\
                </ul>\
            </div>\
            <div class="btn-group">\
                <a class="btn" data-edit="bold" title="Bold (Ctrl/Cmd+B)"><i class="icon-bold"></i></a>\
                <a class="btn" data-edit="italic" title="Italic (Ctrl/Cmd+I)"><i class="icon-italic"></i></a>\
                <a class="btn" data-edit="strikethrough" title="Strikethrough"><i class="icon-strikethrough"></i></a>\
                <a class="btn" data-edit="underline" title="Underline (Ctrl/Cmd+U)"><i class="icon-underline"></i></a>\
            </div>\
            <div class="btn-group">\
                <a class="btn" data-edit="insertunorderedlist" title="Bullet list"><i class="icon-list-ul"></i></a>\
                <a class="btn" data-edit="insertorderedlist" title="Number list"><i class="icon-list-ol"></i></a>\
                <a class="btn" data-edit="outdent" title="Reduce indent (Shift+Tab)"><i class="icon-indent-left"></i></a>\
                <a class="btn" data-edit="indent" title="Indent (Tab)"><i class="icon-indent-right"></i></a>\
            </div>\
            <div class="btn-group">\
                <a class="btn" data-edit="justifyleft" title="Align Left (Ctrl/Cmd+L)"><i class="icon-align-left"></i></a>\
                <a class="btn" data-edit="justifycenter" title="Center (Ctrl/Cmd+E)"><i class="icon-align-center"></i></a>\
                <a class="btn" data-edit="justifyright" title="Align Right (Ctrl/Cmd+R)"><i class="icon-align-right"></i></a>\
                <a class="btn" data-edit="justifyfull" title="Justify (Ctrl/Cmd+J)"><i class="icon-align-justify"></i></a>\
            </div>\
            <div class="btn-group">\
                <a class="btn dropdown-toggle" data-toggle="dropdown" title="Hyperlink"><i class="icon-link"></i></a>\
                <div class="dropdown-menu input-append">\
                    <input class="form-control" placeholder="URL" type="text" data-edit="createLink"/>\
                    <button class="btn" type="button">Add</button>\
                </div>\
                <a class="btn" data-edit="unlink" title="Remove Hyperlink"><i class="icon-cut"></i></a>\
            </div>\
            <div class="btn-group">\
                <a class="btn" title="Insert picture (or just drag & drop)" id="pictureBtn"><i class="icon-picture"></i></a>\
                <input type="file" data-role="magic-overlay" data-target="#pictureBtn" data-edit="insertImage" />\
            </div>\
            <div class="btn-group">\
                <a class="btn" data-edit="undo" title="Undo (Ctrl/Cmd+Z)"><i class="icon-undo"></i></a>\
                <a class="btn" data-edit="redo" title="Redo (Ctrl/Cmd+Y)"><i class="icon-repeat"></i></a>\
            </div>\
        </div>'.format(fonts.map(makeFontSelector).join('')))
}])
;


