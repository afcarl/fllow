# 🌊 fllow 🌊

## Setup

    docker create --name db-data postgres
    docker network create fllow
    docker run --name db --net fllow --volumes-from db-data [--restart always] -d postgres
    docker run --rm --net fllow -i postgres psql -h db -U postgres < database.sql


## Connect to Database

    docker run --rm --net fllow -it postgres psql -h db -U postgres


## Run a Script

### If you change Dockerfile or requirements.txt

    docker build --pull -t fllow .

### While you're developing

    docker run --rm --net fllow [-v $PWD:/usr/src/app] -it fllow python <something>.py
