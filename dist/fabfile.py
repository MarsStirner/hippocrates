#-*- coding: utf-8 -*-
import sys
import os
import getpass
from fabric.api import local, settings, abort, lcd, env, run
from fabric.context_managers import prefix
from fabric import operations
from fabric.colors import yellow, red, green

from config import *

project_dir_path = os.path.abspath('..')
project_dir_name = os.path.basename(os.path.abspath('..'))
code_dir_path = os.path.abspath('.')

virtualenv = '.virtualenv'
virtualenv_bin_path = os.path.join(project_dir_path, virtualenv, 'bin')


def prepare_virtual_env():
    #Установка виртуального окружения и инструмента работы с пакетами Python
    local('easy_install virtualenv')
    #Создаём и активируем виртульное окружение для проекта
    with lcd(project_dir_path):
        with settings(warn_only=True):
            local('rm -R  %s' % virtualenv)
        local('virtualenv %s' % virtualenv)
        local('%s pip' % os.path.join(virtualenv_bin_path, 'easy_install'))
        # local(os.path.join(virtualenv_bin_path, 'activate'))


def _configure_mysql():
    queries = []
    user = operations.prompt(yellow("Specify MySQL admin login:"))
#    password = getpass.getpass("Please specify MySQL admin password: ")
    queries.append("CREATE DATABASE IF NOT EXISTS %s DEFAULT CHARACTER SET utf8;" % DB_NAME)
    #Создаём пользователя для работы с БД
    db_user_host = DB_HOST
    if db_user_host not in ('localhost', '127.0.0.1'):
        db_user_host = '%'
    if DB_USER != 'root':
        #Создаём пользователя и выдаём ему привилегии на работу с БД
        queries.append(
            '''GRANT ALL PRIVILEGES ON %s.* TO '%s'@'%s' IDENTIFIED BY '%s';''' %
            (DB_NAME, DB_USER, db_user_host, DB_PASSWORD)
        )
    queries.append("FLUSH PRIVILEGES;")
    local('echo "%s" | mysql -h %s -u %s -p' % (' '.join(queries), DB_HOST, user))


def _run_as_pg(command):
    """
    Run command as 'postgres' user
    """
    with lcd('/var/lib/postgresql'):
        return local('sudo -u postgres %s' % command)


def _configure_postgres():
    queries = list()

    queries.append("CREATE USER %s WITH NOCREATEDB NOCREATEUSER ENCRYPTED PASSWORD '%s';" % (DB_USER, DB_PASSWORD))
    queries.append("CREATE DATABASE %s WITH OWNER %s;" % (DB_NAME, DB_USER))

    _run_as_pg('psql -c %s' % (' '.join(queries),))


def configure_db():
    if DB_DRIVER == 'mysql':
        _configure_mysql()
    elif DB_DRIVER == 'postgresql+psycopg2':
        _configure_postgres()
    else:
        print red(u"DB_DRIVER в config_local.py указан неверно, исправьте и запустите установку заново")


def prepare_directories():
    with lcd(project_dir_path):
        local('mkdir -p logs')
        local('mkdir -p run/eggs')


def create_system_user():
    #Создаём системного пользователя
    with settings(warn_only=True):
        local('/usr/sbin/useradd --system --no-create-home --home-dir %s --user-group %s' %
              (project_dir_path, SYSTEM_USER))
        local('chsh -s /bin/bash %s' % SYSTEM_USER)
    local('chown -R %s:%s %s' % (SYSTEM_USER, SYSTEM_USER, project_dir_path))


def _get_apache_config_dir():
    for _dir in ('/etc/httpd2/conf/sites-available', '/etc/apache2/sites-available', '/etc/http/conf.d'):
        if os.path.isdir(_dir):
            return _dir
    _dir = operations.prompt(yellow("Specify Apache configs dir:"))
    while not os.path.isdir(_dir):
        print red("Directory doesn't exists. Try again.")
        _dir = operations.prompt(yellow("Please, specify Apache configs dir:"))
    return _dir


def _enable_configs(config_dir, project_dir_name):
    if config_dir.find('sites-available') > -1:
        enable_config_dir = config_dir.replace('sites-available', 'sites-enabled')
        with settings(warn_only=True):
            local('ln -s %s/%s.conf %s/%s.conf' % (config_dir, project_dir_name, enable_config_dir, project_dir_name))


def configure_webserver():
    #Создаём конфиги apache на основе имеющихся шаблонов и заданыых настроек
    with lcd(project_dir_path):

        apache_configs_dir = _get_apache_config_dir()

        config_file = open('%s/fabric_inc/application.conf' % code_dir_path, 'r')
        config = _parse_config(config_file.read())
        config_file.close()
        apache_config_file = open('%s/%s.conf' % (apache_configs_dir, project_dir_name), 'w')
        apache_config_file.write(config)
        apache_config_file.close()

        _enable_configs(apache_configs_dir, project_dir_name)


def configure_supervisor():
    with lcd(project_dir_path):
        config_file = open('%s/fabric_inc/supervisord.conf' % code_dir_path, 'r')
        config = _parse_config(config_file.read())
        config_file.close()
        supervisor_config_file = open('%s/supervisord.conf' % code_dir_path, 'w')
        supervisor_config_file.write(config)
        supervisor_config_file.close()
        local('supervisord -c %s/supervisord.conf' % code_dir_path)


def _parse_config(s):
    #Заменяем в шаблонах конфигов апача метки переменных на значения, заданные в settings
    edits = [('%SERVER_HOST%', SERVER_HOST),
             ('%SERVER_PORT%', str(SERVER_PORT)),
             ('%PROJECT_ROOT%', project_dir_path),
             ('%PROJECT_NAME%', project_dir_name),
             ('%PROJECT_CODE_ROOT%', code_dir_path),
             ('%SYSTEM_USER%', SYSTEM_USER),
             ('%VIRTUALENV_BIN%', virtualenv_bin_path),
             ('%PYTHON_VERSION%', _get_python_version())]
    for search, replace in edits:
        s = s.replace(search, replace)
    return s


def _get_python_version():
    return '%s.%s' % (sys.version_info[0], sys.version_info[1])


def activate_web_config():
    #Активируем конфигурации и перезапускаем apache
    with settings(warn_only=True):
        out = local('service httpd2 restart')
        if out.failed:
            out = local('service httpd restart')
            if out.failed:
                print red('''!Couldn't restart Apache service. Please do it manually.''')


def install_requirements():
    #Устанавливаем необходимые модули python
    with settings(warn_only=True):
        local('apt-get install python-mysqldb')
    with settings(warn_only=True):
        local('apt-get install python-module-MySQLdb')
    with lcd(code_dir_path):
        if DB_DRIVER == 'mysql':
            local('%s install -r requirements\mysql.txt' % os.path.join(virtualenv_bin_path, 'pip'))
        elif DB_DRIVER == 'postgresql+psycopg2':
            local('%s install -r requirements\pgsql.txt' % os.path.join(virtualenv_bin_path, 'pip'))


def restore_database():
    #Создаём таблицы в БД на основе модели
    with lcd(code_dir_path):
        local('alembic upgrade head')


def deploy():
    prepare_virtual_env()
    configure_db()
    prepare_directories()
    create_system_user()
    configure_webserver()
    activate_web_config()
    install_requirements()
    restore_database()
    print green(u'Установка прошла успешно!')


def alt_deploy():
    configure_db()
    prepare_directories()
    create_system_user()
    configure_webserver()
    activate_web_config()
    restore_database()
    print green(u'Установка прошла успешно!')


def update_db():
    restore_database()
    print green(u'Обновление базы данных прошло успешно!')
