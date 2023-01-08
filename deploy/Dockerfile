FROM python:3.11-bullseye

RUN apt-get update && apt-get install -y unzip awscli jq && rm -rf /var/lib/apt/lists/*

# Install docker for deployment
RUN curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh && rm -fv get-docker.sh

ENV ZAPPA_RUNNING_IN_DOCKER=True

ENV PYTHONUNBUFFERED=1

# Define function directory
ARG FUNCTION_DIR="/function"

# Create function directory
RUN mkdir -p ${FUNCTION_DIR}

# Set working directory to function root directory
WORKDIR ${FUNCTION_DIR}

RUN python -m venv venv_deploy
ENV PATH ${FUNCTION_DIR}/venv_deploy/bin:$PATH

RUN pip install --no-cache-dir -U pip==22.3.1 setuptools==65.6.3 && pip -V

ARG PACKAGE_FILE=requirements.txt

COPY ${PACKAGE_FILE} ./

# Install packages with cache
RUN --mount=type=cache,target=/venv_cache,id=${PACKAGE_FILE}.easy.deutsch \
    cp -a /venv_cache/* ${FUNCTION_DIR}/venv_deploy/; \
    pip install --no-cache-dir -r ${PACKAGE_FILE} && zappa -v; \
    cp -a ${FUNCTION_DIR}/venv_deploy/* /venv_cache

# AWS confidential from arguments to run 'aws secretsmanager'
ARG aws_access_key_id
ENV AWS_ACCESS_KEY_ID ${aws_access_key_id}
ARG aws_secret_access_key
ENV AWS_SECRET_ACCESS_KEY ${aws_secret_access_key}
ARG aws_default_region
ENV AWS_DEFAULT_REGION ${aws_default_region}

COPY ./ ./

# Grab the zappa handler.py and put it in the working directory
RUN ZAPPA_HANDLER_PATH=$(python -c "from zappa import handler; print (handler.__file__)") \
    && echo $ZAPPA_HANDLER_PATH \
    && cp $ZAPPA_HANDLER_PATH ./

RUN cp -a ${FUNCTION_DIR}/deploy/aws-lambda-rie /usr/local/bin/; cp -a ${FUNCTION_DIR}/deploy/entrypoint.sh /

ENTRYPOINT [ "/entrypoint.sh" ]

CMD ["handler.lambda_handler"]
