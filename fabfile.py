from fabric.api import local

IMAGE = 'easy_deutsch/zappa'
ACCESS_KEY = local("aws --profile sebatyler configure get aws_access_key_id", capture=True)
SECRET_KEY = local("aws --profile sebatyler configure get aws_secret_access_key", capture=True)

is_built = False


def nb():
    """
    no build - skip build
    """
    global is_built
    is_built = True


def build():
    """
    build docker image for zappa
    """
    global is_built
    if not is_built:
        local(f"docker build -t {IMAGE} .")
        is_built = True


def run(command=''):
    """
    run command in docker image
    """
    local(f"docker run -ti -e"
          f" AWS_ACCESS_KEY_ID={ACCESS_KEY} -e AWS_SECRET_ACCESS_KEY={SECRET_KEY}"
          f" --rm {IMAGE} {command}")


def _zappa_run(operation=None, args='', docker=True):
    if not operation:
        raise ValueError('operation required')

    command = f"zappa {operation}"
    if args:
        command += f' "{args}"'

    if docker:
        run(command)
    else:
        local(command)


def tail():
    """
    tail logs
    """
    _zappa_run('tail')


def status():
    """
    show status
    """
    _zappa_run('status')


def deploy():
    """
    deploy to AWS lambda & API gateway
    """
    build()
    _zappa_run('update')


def rollback(n=1):
    """
    rollback to previous deployment
    """
    _zappa_run('rollback', f'-n {n}')


def collectstatic():
    """
    run collectstatic command to upload static files to S3
    """
    build()
    _zappa_run('manage', 'collectstatic --noinput')


def schedule():
    """
    schedule functions
    """
    build()
    _zappa_run('schedule')


def migrate():
    """
    run migrate command to apply DB migrations
    """
    _zappa_run('manage', 'migrate --noinput')


def setup():
    """
    setup test for current developer
    """
    build()
    _zappa_run('deploy')


def setup_ssl():
    """
    setup ssl
    """
    build()
    _zappa_run('certify')
