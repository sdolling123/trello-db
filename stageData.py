import dropbox as db
import psycopg2
from psycopg2 import extras
import pandas as pd
import io
import numpy as np
import datetime
import os

"""
Setting up dropbox credential.
"""
dropbox_config = {"access_token": os.environ.get("DROPBOX_ACCESS")}

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
Creates the connection with dropbox API.
"""
dbx = db.Dropbox(os.environ.get("DROPBOX_ACCESS"))

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


def update_log(type, message=""):
    """
    This inserts a comment into the log file for the etl should there be an
    error processing one of the arms of the etl. It will log the function,
    the table (if applicable), the file (if applicable), and the date and
    time the error occurred. It will also log the start and stop time of the
    etl.
    """
    today = datetime.datetime.now().strftime("%m/%d/%Y %I:%M %p")
    _, res = dbx.files_download("/ETL_log/trello_log.txt")
    res.raise_for_status()
    with io.BytesIO(res.content) as stream:
        txt = stream.read().decode()
        if type == "start":
            text = "\r\n" + str(today) + " -> " + message
        elif type == "end" and message != "":
            text = (
                "\r\n"
                + str(today)
                + " -> "
                + message
                + (
                    "\r\n"
                    + "********************************************************************************************"
                )
            )
        elif type == "end" and message == "":
            text = (
                "\r\n"
                + "********************************************************************************************"
            )
    new_message = txt + text
    with io.BytesIO(new_message.encode()) as stream:
        stream.seek(0)
        dbx.files_upload(
            stream.read(), "/ETL_log/trello_log.txt", mode=db.files.WriteMode.overwrite
        )
    return


def trello_to_db(data_payload):
    """
    This takes in the dictionary of tables (keys), path, and trello function and
    uploads it to Dropbox as a CSV file. File name comes from the path and the
    dataframe object is supplied by the function in the dictionary.
    """
    for key, value in data_payload.items():
        try:
            df = value[1]
            path = value[0]
            df_string = df.to_csv(index=False)
            db_bytes = bytes(df_string, "utf8")
            dbx.files_upload(f=db_bytes, path=path, mode=db.files.WriteMode.overwrite)
        except:
            error_message = (
                "ERROR: " + "Trello data pull for file " + value[0] + " failed."
            )
            update_log("start", error_message)
    return


def readyDropboxFile(file_name):
    """
    This function uses the dropbox sdk to retrieve a CSV file and ready it for
    database ingestion. Required is the dbx instance and the file name to be
    prepped for ingestion. File name should include '/' as prefix to actual
    name.
    """
    try:
        _, response = dbx.files_download(file_name)
        with io.BytesIO(response.content) as stream:
            df = pd.read_csv(stream)
            df = df.fillna(np.nan)
            df = df.replace({np.nan: None})
        return df
    except:
        error_message = "ERROR: readyDropboxFile() failed to run successfully."
        update_log("start", error_message)


def db_to_postgres(df, table):
    """
    This will insert the data into the respective table within the postgres
    database.
    """
    # Create a list of tupples from the dataframe values
    tuples = [tuple(x) for x in df.to_numpy()]
    # Comma-separated dataframe columns
    cols = ",".join(list(df.columns))
    # SQL quert to execute
    query = "INSERT INTO %s(%s) VALUES %%s" % (table, cols)
    cursor = conn.cursor()
    try:
        extras.execute_values(cursor, query, tuples)
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        update_log("start", "Error: %s" % error)
        conn.rollback()
        cursor.close()
        return 1
    cursor.close()


def load_data_db(data_payload):
    """
    This calls the readyDropboxFile and the db_to_progress functions to pull
    the files from DB, ready them, and insert into Postgres db. Provide list
    of the file names (in this case it comes as a dictionary), the dbx instance
    and the conn connection.
    """
    for key, value in data_payload.items():
        try:
            fl = readyDropboxFile(value[0])
            db_to_postgres(fl, key)
        except:
            error_message = (
                "ERROR: File " + value[0] + " failed to load into table " + key + "."
            )
            update_log("start", error_message)


def checkFiles():
    """
    This checks to see if the modified date of the given file set matches
    today. This will be used in the future to check the trello data pull
    was successful and if not, insert/update error log.
    """
    today = datetime.datetime.now().date()
    result = dbx.files_list_folder(path="")
    for i in result.entries:
        if i.name.endswith(".csv") == True:
            if i.server_modified.date() - datetime.timedelta(hours=5) == today:
                print(i.name)
            else:
                print(i.name + " upload date does not match today")
        else:
            continue


def runScriptSQL(sql):
    cursor = conn.cursor()
    file = open(sql, "r")
    cursor.execute(file.read())
    conn.commit()
    return cursor.close()
