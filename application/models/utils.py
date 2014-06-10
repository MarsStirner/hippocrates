# -*- coding: utf-8 -*-
from flask.ext.login import current_user

def safe_current_user_id():
    return current_user.get_id() if current_user else None