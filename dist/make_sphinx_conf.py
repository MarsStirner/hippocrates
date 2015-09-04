#!/usr/bin/python
# coding: utf-8
import sys
import os
sys.path.append(os.path.join(os.getcwd(), '..'))
from config_local import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

params = {
    '%DB_HOST%': DB_HOST,
    '%DB_PORT%': DB_PORT,
    '%DB_USER%': DB_USER,
    '%DB_PASSWORD%': DB_PASSWORD,
    '%DB_NAME%': DB_NAME
}


def make_sphinx_conf():
    with open('sphinx.conf.new', 'w') as new_conf:
        with open('sphinx.conf', 'r') as skel:
            f = skel.read()
            for pattern, repl in params.iteritems():
                f = f.replace(pattern, str(repl))
            new_conf.write(f)


if __name__ == '__main__':
    make_sphinx_conf()