import psycopg2
import os

"""
Setting up postgres credentials.
"""
postgres_config = {
    "host": os.environ.get("AWS_POSTGRES_HOST"),
    "dbname": os.environ.get("AWS_POSTGRES_DB"),
    "user": os.environ.get("AWS_POSTGRES_USER"),
    "password": os.environ.get("AWS_POSTGRES_PW"),
}

"""
Creates the connection with Postgres database.
"""
conn = psycopg2.connect(
    "host="
    + postgres_config["host"]
    + " dbname="
    + postgres_config["dbname"]
    + " user="
    + postgres_config["user"]
    + " password="
    + postgres_config["password"]
)


def runScriptSQL(sql):
    cursor = conn.cursor()
    file = open(sql, "r")
    cursor.execute(file.read())
    conn.commit()
    return cursor.close()


runScriptSQL("readyDatabase.sql")
