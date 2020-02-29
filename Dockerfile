FROM lambci/lambda:build-python3.6

WORKDIR /var/task

ENV BASH_ENV /root/.bashrc

# Fancy prompt to remind you are in zappashell
RUN echo 'export PS1="\[\e[36m\]zappashell>\[\e[m\] "' >> $BASH_ENV

RUN virtualenv venv
RUN echo ". /var/task/venv/bin/activate" >> $BASH_ENV

SHELL ["/bin/bash", "-c"]

RUN pip install zappa==0.50.0

ADD requirements.txt ./
RUN pip install -r requirements.txt

ADD zappa_settings.json ./
RUN zappa package

ADD . ./

COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

CMD ["bash"]
