import psycopg2
import psycopg2.extras


def connect():
    return psycopg2.connect(host='db', user='postgres',
                            cursor_factory=psycopg2.extras.NamedTupleCursor)
