# trello-db

This repo holds the source files for the trello ETL data pipeline.

An example config.py file is present to provide some examples on how that file is set up and is used downstream in the code. A SQL file containing the source for custom functions and stored procedures is not present as it contains structural information on the database and is less relevant to the ETL for general purposes.

pullData.py uses information stored in the config.py file and environment variables to package a series of API calls pulling data from Trello. The outcome is a set of dataframes for each of the tables to be used in the database. These dataframes contain the information needed for reporting. There is a function for each of the dataframes. The process starts out with pulling in only the boards intended and sets up "flag" columns used to make decisions on what data to pull in the latter functions.

stageData.py is responsible for taking those dataframes and ingesting them to a staging environment. Before ingesting the data to the database, the tables are dropped and re-added. In case the trello data pull fails, the data from the last successful pull will still be in the staging environment so that users are not met with reports and dashboards riddled with errors from failed refreshes. In addition, should new fields be required from the users, this reduces the amount of lines needing to be update to accommodate it.

main.py initiates the trello pull and insertion into staging environment. The tables are then dropped and re-added from the database. The data is then readied as buffers to import into the database. Once the data is imported a final SQL script is run that does some final processing and creates views for the various schemas. It also grabs the users for those schemas and grant "select" for the respective schema views.

Any errors are attempted to be caught and logged.
