# -*- coding: utf-8 -*-
import os
from flask import Flask, jsonify
from flask.ext.principal import Principal
from flask.ext.babel import Babel
from flask.ext.login import LoginManager, current_user
from flask_beaker import BeakerSession
import pytz
from werkzeug.contrib.profiler import ProfilerMiddleware
from application.middleware import Gzip
from systemwide import db, cache
from autoload import load_blueprints
import config

app = Flask(__name__)
app.config.from_object(config)

db.init_app(app)
from models import *

babel = Babel(app)


login_manager = LoginManager(app)
Principal(app)

BeakerSession(app)


cache.init_app(app)


@app.context_processor
def enum():
    from application.lib.enum import Enum
    return {
        'Enum': Enum,
    }


@babel.timezoneselector
def get_timezone():
    return pytz.timezone(app.config['TIME_ZONE'])

#Register blueprints
blueprints_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', app.config['BLUEPRINTS_DIR']))
load_blueprints(app, apps_path=blueprints_path)

# Import all views
from views import *

if app.config['PROFILE']:
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])

Gzip(app)