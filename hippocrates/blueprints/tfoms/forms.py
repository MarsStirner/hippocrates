# -*- coding: utf-8 -*-
from wtforms import TextField, BooleanField, IntegerField
from flask_wtf import Form
from wtforms.validators import Required
from models import Template


class CreateTemplateForm(Form):
    name = TextField('name', validators=[Required()], default="")
    archive = BooleanField('archive', default=True)

    def validate(self):
        rv = Form.validate(self)
        if not rv:
            return False

        template = Template.query.filter_by(name=self.name.data).all()

        if len(template):
            self.name.errors.append('Имена шаблонов должны быть уникальны')
            return False

        return True

