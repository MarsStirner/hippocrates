#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 31.03.2016

"""

# usage:
# import sqlparse
# from hippocrates.blueprints.risar.lib.snippets import get_sqlaclchemy_query_text
# sql_text = get_sqlaclchemy_query_text(data)
# sqlparse.format(sql_text, reindent=True, keyword_case='upper')


# or use the appropiate escape function from your db driver
def get_sqlaclchemy_query_text(query):
    """
    Печатает текст запроса из SQLAlchemy
    Реализация для PostgreSQL
    """
    from sqlalchemy.sql import compiler
    # from psycopg2.extensions import adapt as sqlescape
    # from nemesis.systemwide import db
    # conn = db.session.connection
    # sqlescape = conn().escape
    # from pymysql import Connection
    # sqlescape = Connection().escape

    dialect = query.session.bind.dialect
    statement = query.statement
    comp = compiler.SQLCompiler(dialect, statement)
    comp.compile()
    enc = dialect.encoding
    params = {}
    for k,v in comp.params.iteritems():
        if isinstance(v, unicode):
            v = v.encode(enc)
        # params[k] = sqlescape(v)
        params[k] = v
    return (comp.string.encode(enc) % params).decode(enc)
