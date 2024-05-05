import inspect
import json
from os import environ

import dotenv
from fabric import task
from invoke import run as local

# TODO: upgrade invoke to 2.0
if not hasattr(inspect, "getargspec"):
    inspect.getargspec = inspect.getfullargspec


dotenv.read_dotenv()

IMAGE = "easy-deutsch-aws"
STAGE = "prod"

is_built = False

environ.update(
    # docker pip caching
    DOCKER_BUILDKIT="1",
    # bypass python version check
    ZAPPA_RUNNING_IN_DOCKER="True",
)


@task
def nb(c):
    """
    no build - skip build
    """
    global is_built
    is_built = True


@task
def build(c):
    """
    build docker image for zappa
    """
    global is_built
    if not is_built:
        # generate zappa_settings.py
        local(f"zappa save-python-settings-file {STAGE}", echo=True)

        # required from environment variables or .env
        build_args = [
            f"--build-arg {key.lower()}={environ[key]}"
            for key in (
                "AWS_ACCESS_KEY_ID",
                "AWS_SECRET_ACCESS_KEY",
                "AWS_DEFAULT_REGION",
                "TELEGRAM_BOT_TOKEN",
                "TELEGRAM_BOT_CHANNEL_ID",
            )
        ]

        # docker build
        progress = environ.get("DOCKER_PROGRESS")  # possible value: plain
        cmd_list = [
            "docker buildx build --platform linux/amd64 --provenance false",
            "-f deploy/Dockerfile",
            *build_args,
            f"-t {IMAGE}:latest",
        ]
        if progress:
            cmd_list.append(f"--progress={progress}")

        cmd_list.append(".")
        local(" ".join(cmd_list))

        is_built = True


@task
def run(c, command=""):
    """
    run command in docker image
    """
    local(f"docker run -it --rm --entrypoint bash {IMAGE}:latest {command}")


def _create_ecr_repo(c):
    aws_default = f"aws --output json ecr"
    local(f"{aws_default} create-repository --repository-name {IMAGE} --image-scanning-configuration scanOnPush=true")

    set_ecr_lifecycle(c, force=False)


def _deploy_with_ecr(c, update=True):
    # https://ianwhitestone.work/zappa-serverless-docker/
    # https://docs.aws.amazon.com/lambda/latest/dg/images-create.html

    build(c)

    aws_default = f"aws --output json ecr"

    # get repository url
    for try_create in (True, False):
        result = local(f"{aws_default} describe-repositories --repository-names {IMAGE}", warn=True)

        if result:
            break

        if try_create:
            _create_ecr_repo(c)

    result_dict = json.loads(result.stdout)
    repo_url = result_dict["repositories"][0]["repositoryUri"]

    # re-tag
    local(f"docker tag {IMAGE}:latest {repo_url}:latest")

    # get authenticated to push to ECR
    local(f"{aws_default} get-login-password | docker login --username AWS --password-stdin {repo_url}")

    # push it
    local(f"docker push {repo_url}:latest")

    # deploy (first time) or update
    command = "update" if update else "deploy"
    local(f"zappa {command} {STAGE} -d {repo_url}:latest", echo=True)


@task
def set_ecr_lifecycle(c, force=True):
    """set Elastic Container Registry lifecycle"""
    aws_default = f"aws --output json ecr"

    result = local(f"{aws_default} get-lifecycle-policy --repository-name {IMAGE}", warn=True)

    if force or result.exited != 0:
        local(
            f"{aws_default} put-lifecycle-policy --repository-name {IMAGE} --lifecycle-policy-text file://./deploy/ecr_lifecycle_policy.json"
        )


@task
def setup(c):
    """
    first deploy to AWS lambda & API gateway
    """
    _deploy_with_ecr(c, update=False)


@task
def deploy(c):
    """
    deploy to AWS lambda & API gateway
    """
    _deploy_with_ecr(c, update=True)


def _zappa_run(c, operation=None, args=""):
    if not operation:
        raise ValueError("operation required")

    command = f"zappa {operation} {STAGE}"
    if args:
        command += f' "{args}"'

    local(command, echo=True)


@task
def tail(c):
    """
    tail logs
    """
    _zappa_run(c, "tail")


@task
def status(c):
    """
    show status
    """
    _zappa_run(c, "status")


@task
def rollback(c, n=1):
    """
    rollback to previous deployment
    """
    _zappa_run(c, "rollback", f"-n {n}")


@task
def collectstatic(c):
    """
    run collectstatic command to upload static files to S3
    """
    _zappa_run(c, "manage", "collectstatic --noinput")


@task
def schedule(c):
    """
    schedule functions
    """
    _zappa_run(c, "schedule")


@task
def migrate(c):
    """
    run migrate command to apply DB migrations
    """
    _zappa_run(c, "manage", "migrate --noinput")


@task
def setup_ssl(c):
    """
    setup ssl
    """
    _zappa_run(c, "certify")
