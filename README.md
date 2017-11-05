# 🌊 fllow 🌊

## Setup

### Setup Database

    docker create --name db-data postgres
    docker network create fllow
    docker run --name db --net fllow --volumes-from db-data --restart always -d postgres
    docker run --rm --net fllow -i postgres psql -h db -U postgres < database.sql

### Insert Consumer Key and Secrets

Get a consumer key and secret from https://apps.twitter.com/

Update `CONSUMER_KEY` in `api.py`

Create the file `secret/__init__.py` with the contents:

    APP_SECRET = '<whatever-you-want>'  # for signing flask session cookies
    CONSUMER_SECRET = '<your-consumer-secret>'

### Run Fllow

    docker build --pull --tag fllow .
    docker run --name fllow --net fllow --restart always -d fllow
    docker run --name fllow-web --net fllow -p 5000:5000 --restart always -d fllow python web.py

### Setup Users

    docker run --rm --net fllow -it fllow python add_user.py
    docker run --rm --net fllow fllow python add_user_mentors.py <user_name> <mentor_name> <mentor_name> …
    …
    docker restart fllow


## Connect to Database

    docker run --rm --net fllow -it postgres psql -h db -U postgres


## Follow Logs

    docker logs -tf fllow


## Development

### If you change Dockerfile or requirements.txt

    docker build --pull --tag fllow .

### Run a script

    docker run --rm --net fllow -v $PWD:/usr/src/app -it fllow python <something>.py
