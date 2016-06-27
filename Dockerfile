FROM debian:jessie

RUN apt-get update \
    && apt-get install --yes \
            curl \
            python3 \
            python3-psycopg2 \
    && curl https://bootstrap.pypa.io/get-pip.py | python3 \
    && apt-get autoremove --yes --purge curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt
COPY requirements.txt ./
RUN pip3 install -r requirements.txt
COPY ./ ./
