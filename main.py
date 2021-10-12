import stageData as sd
import pullData as dp


"""
This script runs the main ETL functions including the pulling data to staging
environment in Dropbox, dropping and adding tables from database, ingesting
new data to database, and readying the database for users.

Steps running:
1. pullData.py --> extracts and processes data from Trello API
2. stageData.py --> loads processed data pull into Dropbox
3. stageDatabase.sql --> drops db tables and adds them back
4. loadData.py --> loads data from Dropbox staging environment into Postgres db
5. readyDatabase.sql --> creates db views and grants access readying db for use
"""

"""
Inserting start time of ETL into log file.
"""
elt_start = "ETL has started."
sd.update_log("start", elt_start)

"""
Importing the functions from pullData to be used in this script.
"""
try:
    board = dp.collectBoards(orgs=dp.included_org)
    include_board = board[board["board_included"] == True]
    comment_included = include_board[include_board["board_comment"] == True]
    brd_pll = dp.fromBoardPull(include_board)
    comment_pll = dp.fromBoardPull(comment_included)
    comment_data = dp.commentDataPull(comment_pll)
    card_data = dp.cardDataPull(brd_pll)
    list_data = dp.validListDataPull(brd_pll)
    label_data = dp.validLabelDataPull(brd_pll)
    member_data = dp.validMemberDataPull(brd_pll)
    validField_data = dp.validFieldDataPull(brd_pll)
    field_data = dp.fieldDataPull(brd_pll)
    checklist_data = dp.checklistDataPull(brd_pll)
    validFieldOption_data = dp.validFieldOptionDataPull(validField_data)
except Exception as err:
    trello_error = (
        "Looks like there was an error with one of the data pulls from Trello."
        + "\r\n"
        + str(err)
    )
    sd.update_log("start", trello_error)
else:
    """
    Data dictionary is created to be used downstream containing the database table
    name (key), the dropbox file path (index 0), and the dataPull function
    (index 1).
    """
    data_dict = dict(
        {
            "validboard": ["/validBoardData.csv", board],
            "card": ["/cardData.csv", card_data],
            "checklist": ["/checklistData.csv", checklist_data],
            "comment": ["/commentData.csv", comment_data],
            "field": ["/fieldData.csv", field_data],
            "validfield": ["/validFieldData.csv", validField_data],
            "validfieldoption": ["/validFieldOptionData.csv", validFieldOption_data],
            "validlabel": ["/validLabelData.csv", label_data],
            "validlist": ["/validListData.csv", list_data],
            "validmember": ["/validMemberData.csv", member_data],
        }
    )


"""
First the data pull occurrs and any errors are logged. If no errors are found,
the completion of the data pull and staging of the db are logged.
"""
try:
    sd.trello_to_db(data_dict)
except Exception as err:
    error_message = (
        "ERROR: trello_to_db() failed to run successfully." + "\r\n" + str(err)
    )
    sd.update_log("start", error_message)
else:
    sd.runScriptSQL("stageDatabase.sql")
    message = "Data pull is complete and database has been staged."
    sd.update_log("start", message)

"""
Once the data is staged in dropbox and the database has been staged, the data
is then readied and ingested into the db. Errors are logged. Barring any,
errors, the next step is to call some custom functions and stored procedure
to ready the database for the users.
"""
try:
    sd.load_data_db(data_dict)
except Exception as err:
    error_message = (
        "ERROR: load_data_db() failed to run successfully." + "\r\n" + str(err)
    )
    sd.update_log("start", error_message)
else:
    try:
        sd.runScriptSQL("readyDatabase.sql")
    except Exception as err:
        error_message = "ERROR: SQL script failed to run." + "\r\n" + str(err)
        sd.update_log("start", error_message)

"""
Inserting end time of ETL into log file.
"""
end_message = "ETL has completed running."
sd.update_log("end", end_message)
