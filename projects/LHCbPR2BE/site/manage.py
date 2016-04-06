#!/usr/bin/env python
import os
import sys
import dotenv

BASE_DIR = os.path.join(os.path.dirname(__file__), os.pardir)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
os.environ.setdefault("ENV", "default")


def run_gunicorn_server(addr, port):
    """run application use gunicorn http server
    """
    from gunicorn.app.base import Application
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()

    class DjangoApplication(Application):

        def init(self, parser, opts, args):
            return {
                'bind': '{0}:{1}'.format(addr, port),
                'workers': 4,
                'accesslog': '-'
            }

        def load(self):
            return application

    DjangoApplication().run()

if __name__ == "__main__":
    from django.core.management import execute_from_command_line

    env_file = os.path.abspath(
        os.path.join('%s/envs' % BASE_DIR, "%s.env" % os.getenv('ENV')))
    print('*' * 80)
    print("Read environment from '{}'".format(env_file))
    print('*' * 80)
    dotenv.read_dotenv(env_file)

    addr = os.getenv('DJANGO_HTTP_ADDR', '127.0.0.1')
    port = os.getenv('DJANGO_HTTP_PORT', '8000')
    server_type = os.getenv('DJANGO_SERVER_TYPE', 'dev')

    if(len(sys.argv) == 2 and sys.argv[1] == 'runserver'):
        if server_type != 'dev':
            run_gunicorn_server(addr=addr, port=port)
            sys.exit(0)
        sys.argv.append('%s:%s' % (addr, port))

    execute_from_command_line(sys.argv)
