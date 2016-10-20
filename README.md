# 🌺 Fllowers 🌺

## Setup

    docker create --name db-data postgres
    docker network create fllowers
    docker run --name db --net fllowers --volumes-from db-data -d postgres
    docker run --rm --net fllowers -i postgres psql -h db -U postgres < database.sql


## Connect to Database

    docker run --rm --net fllowers -it postgres psql -h db -U postgres


## Run a Script

### If you change Dockerfile or requirements.txt

    docker build -t fllowers .

### While you're developing

    docker run --rm --net fllowers [-v $PWD:/usr/src/app] -it fllowers python <something>.py
