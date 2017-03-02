# 🌊 fllow 🌊

## Setup

### Setup Database

    docker create --name db-data postgres
    docker network create fllow
    docker run --name db --net fllow --volumes-from db-data --restart always -d postgres
    docker run --rm --net fllow -i postgres psql -h db -U postgres < database.sql
    
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
