FROM alpine:3.15

RUN adduser -h /code -u 1000 -D imabot
COPY requirements.txt /requirements.txt

WORKDIR /code
ENV PATH="/code/.local/bin:${PATH}"
ENV TZ=Europe/Paris

RUN apk update --no-cache \
    && apk add --no-cache python3=~3.9 \
                          iputils=~20210722 \
                          openssh=~8.8 \
                          openssh-keygen=~8.8 \
                          tzdata=~2022 \
                          ansible=~4.8 \
    && apk add --no-cache --virtual .build-deps \
                                    gcc=~10.3 \
                                    libc-dev=~0.7 \
                                    python3-dev=~3.9 \
    && su imabot -c "python3 -m ensurepip --upgrade \
                     && pip3 install --user -U -r /requirements.txt" \
    && apk del .build-deps \
    && rm /requirements.txt

USER imabot
COPY --chown=imabot:imabot code/ansible      /code/ansible
COPY --chown=imabot:imabot code/imabot.py    /code/
COPY --chown=imabot:imabot code/subcommands  /code/subcommands
COPY --chown=imabot:imabot code/variables.py /code/

ENTRYPOINT ["/code/imabot.py"]
