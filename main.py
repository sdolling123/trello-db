import requests
import pandas as pd
import csv
import config
from io import StringIO
import numpy as np
import re

boardBase = config.boardBase
organizationBase = config.organizationBase
organizationParams = config.organizationParams
cardsBase = config.cardsBase
membersParams = config.membersParams
listParams = config.listParams
labelParams = config.labelParams
customFieldParams = config.customFieldParams
cardsParams = config.cardsParams
checklistParams = config.checklistParams
customFieldBase = config.customFieldBase
query = config.query
excluded_boards = config.excluded_boards
comments_included = config.comments_included
included_org = config.included_org


def getBuffer(df):
    textStream = StringIO()
    df.to_csv(textStream, header=False, index=False)
    return textStream.getvalue()


class TrelloCall:
    def __init__(self):
        """provide the key and token, base, and counter"""
        self.key = query["key"]
        self.token = query["token"]
        self.base = "https://trello.com/1/"
        self.counter = 0
        self.k = []
        self.jk = []

    def make_call(self, base):
        """this is what will make the call and requires the url"""
        self.url_provided = base
        params_key_and_token = {"key": self.key, "token": self.token}
        response = requests.get(self.url_provided, params=params_key_and_token)
        r = response.json()
        return r


def collectBoards(orgs):
    """This function accepts a list of dictionaries containing organization IDs as well as whether to run
    that particular org. In return, a list of dictionaries is provided containing board name, board id,
    and whether that board is closed."""
    board_list = []
    for item in orgs:
        if item["include"] == False:
            continue
        else:
            call = TrelloCall()
            r = call.make_call(organizationBase + item["orgId"] + organizationParams)
            for index, element in enumerate(r):
                if element["id"] in excluded_boards:
                    board_list.append(
                        {
                            "board_name": element["name"],
                            "board_id": element["id"],
                            "board_closed": element["closed"],
                            "board_included": False,
                            "board_comment": False,
                        }
                    )
                else:
                    if element["id"] in comments_included:
                        board_list.append(
                            {
                                "board_name": element["name"],
                                "board_id": element["id"],
                                "board_closed": element["closed"],
                                "board_included": True,
                                "board_comment": True,
                                "schema_name": re.sub(
                                    "[^A-Za-z]", "", element["name"]
                                ).lower()[:12],
                            }
                        )
                    else:
                        board_list.append(
                            {
                                "board_name": element["name"],
                                "board_id": element["id"],
                                "board_closed": element["closed"],
                                "board_included": True,
                                "board_comment": False,
                                "schema_name": re.sub(
                                    "[^A-Za-z]", "", element["name"]
                                ).lower()[:12],
                            }
                        )

    board_frame = pd.DataFrame(board_list)
    board_frame["board_closed"] = board_frame["board_closed"].astype("bool")
    board_frame["board_included"] = board_frame["board_included"].astype("bool")
    board_frame["board_comment"] = board_frame["board_comment"].astype("bool")
    board_frame["schema_name"] = board_frame["schema_name"].fillna(np.nan)
    board_frame["schema_name"] = board_frame["schema_name"].replace({np.nan: None})
    return board_frame


def collectMembers(brds):
    """This function accepts a dictionary of boards and uses the IDs to loop through an API
    call grabbing members and their IDs. Duplicates are checked for and sorted out. The
    result is a dataframe of members, their ids, and usernames."""
    full_list = []
    filtered = brds[brds["board_included"] == True]
    for item in filtered["board_id"]:
        call = TrelloCall()
        r = call.make_call(boardBase + item + membersParams)
        for element in r:
            if element["id"] in full_list:
                continue
            else:
                full_list.append(
                    {
                        "member_id": element["id"],
                        "member_name": element["fullName"],
                        "member_username": element["username"],
                    }
                )
    member_frame = pd.DataFrame(full_list).drop_duplicates(inplace=False)
    return member_frame


def collectLists(brds):
    """Passing board ids here and grabbing the lists associated with them."""
    # list_frame = pd.DataFrame()
    list_dict = []
    filtered = brds[brds["board_included"] == True]
    for item in filtered["board_id"]:
        call = TrelloCall()
        r = call.make_call(boardBase + item + listParams)
        for element in r:
            list_dict.append(
                {
                    "list_id": element["id"],
                    "list_name": element["name"],
                    "board_id": element["idBoard"],
                    "list_closed": element["closed"],
                }
            )
    list_frame = pd.DataFrame(list_dict)
    list_frame["list_closed"] = list_frame["list_closed"].astype("bool")
    return list_frame


def collectLabels(brds):
    """This function accepts a dictionar of boards and uses the IDs to loop through an API
    call grabbing labels and their IDs. Duplicates are checked for and sorted out. The
    result is a dictionary of labels, their ids, and colors."""
    label_list = []
    filtered = brds[brds["board_included"] == True]
    for item in filtered["board_id"]:
        call = TrelloCall()
        r = call.make_call(boardBase + item + labelParams)
        for element in r:
            label_list.append(
                {
                    "label_id": element["id"],
                    "label_name": element["name"],
                    "board_id": element["idBoard"],
                    "label_color": element["color"],
                }
            )
    label_frame = pd.DataFrame(label_list)
    return label_frame


def collectFields(brds):
    """This returns a valid/dimensional data set of custom fields for a
    given board."""
    field_list = []
    filtered = brds[brds["board_included"] == True]
    for item in filtered["board_id"]:
        call = TrelloCall()
        r = call.make_call(boardBase + item + customFieldParams)
        for element in r:
            field_list.append(
                {
                    "field_id": element["id"],
                    "field_name": element["name"],
                    "board_id": element["idModel"],
                    "field_type": element["type"],
                }
            )
    field_frame = pd.DataFrame(field_list)
    return field_frame


def cardCreated(id):
    """This gets used inline with the card function to calculate the date a
    given card was created."""
    return pd.to_datetime(int(id[:8], 16), unit="s").date()


def collectCards(brds):
    """Uses a filtered list of board ids to grab cards for a given board."""
    card_list = []
    filtered = brds[brds["board_included"] == True]
    for item in filtered["board_id"]:
        call = TrelloCall()
        r = call.make_call(boardBase + item + cardsParams)
        for element in r:
            card_list.append(
                {
                    "card_id": element["id"],
                    "card_creation": cardCreated(element["id"]),
                    "card_name": element["name"],
                    "board_id": element["idBoard"],
                    "list_id": element["idList"],
                    "card_last_active": element["dateLastActivity"],
                    "label_id": element["idLabels"],
                    "member_id": element["idMembers"],
                    "card_number": element["idShort"],
                    "card_link": element["shortLink"],
                    "card_url": element["shortUrl"],
                    "card_closed": element["closed"],
                }
            )
    card_frame = pd.DataFrame(card_list)
    card_frame["card_last_active"] = pd.to_datetime(
        card_frame["card_last_active"]
    ).dt.date
    card_frame["card_closed"] = card_frame["card_closed"].astype("bool")
    return card_frame


def collectComments(brds):
    """Using a filtered list of board ids, this grabs all the comments for
    the passing board."""
    comment_list = []
    filtered = brds[brds["board_comment"] == True]
    for value in filtered["board_id"]:
        call = TrelloCall()
        crds = call.make_call(boardBase + value + "/cards?field=id,name")
        for item in crds:
            rr = call.make_call(cardsBase + item["id"] + "/actions?filter=commentCard")
            for element in rr:
                comment_list.append(
                    {
                        "card_id": item["id"],
                        "member_id": element["idMemberCreator"],
                        "card_comment": element["data"]["text"],
                        "comment_date": element["date"],
                    }
                )
    comment_frame = pd.DataFrame(comment_list)
    comment_frame["comment_date"] = pd.to_datetime(
        comment_frame["comment_date"]
    ).dt.date
    return comment_frame


def collectCheckLists(brds):
    """Using a filtered list of boards (done within) this grabs all the
    checklists and their items and combines them for the output."""
    item_list = []
    check_list = []
    filtered = brds[brds["board_included"] == True]
    for value in filtered["board_id"]:
        call = TrelloCall()
        r = call.make_call(boardBase + value + checklistParams)
        for element in r["checklists"]:
            check_list.append(
                {
                    "checklist_id": element["id"],
                    "checklist_name": element["name"],
                    "card_id": element["idCard"],
                    "board_id": element["idBoard"],
                }
            )
        for index in range(len(r["checklists"])):
            for i in r["checklists"][index]["checkItems"]:
                item_list.append(
                    {
                        "checklist_id": i["idChecklist"],
                        "item_state": i["state"],
                        "item_id": i["id"],
                        "item_name": i["name"],
                        "item_member": i["idMember"],
                    }
                )
    item_frame = pd.DataFrame(item_list)
    check_frame = pd.DataFrame(check_list)
    full_checklist = pd.merge(
        item_frame,
        check_frame,
        how="right",
        on="checklist_id",
        left_index=False,
        right_index=False,
    )
    full_checklist["item_id"] = full_checklist["item_id"].fillna(np.nan)
    full_checklist["item_id"] = full_checklist["item_id"].replace({np.nan: None})
    full_checklist["item_state"] = full_checklist["item_state"].fillna(np.nan)
    full_checklist["item_state"] = full_checklist["item_state"].replace({np.nan: None})
    full_checklist["item_name"] = full_checklist["item_name"].fillna(np.nan)
    full_checklist["item_name"] = full_checklist["item_name"].replace({np.nan: None})
    full_checklist["item_member"] = full_checklist["item_member"].fillna(np.nan)
    full_checklist["item_member"] = full_checklist["item_member"].replace(
        {np.nan: None}
    )
    return full_checklist


def collectCardFields(brds):
    """Provide a list of board ids with a column of whether to include them and
    this will capture all of the fields and their values for the given card. Two
    API functions are running: one to grab the list of cards for the given board
    and one for grabbing the ids. Note that the ids will be the actual value for
    some and an id referring to a value for others. This will be used to join
    downstream."""
    card_fields = []
    filtered = brds[brds["board_included"] == True]
    for value in filtered["board_id"]:
        call = TrelloCall()
        crds = call.make_call(boardBase + value + "/cards?field=id,name")
        for item in crds:
            rr = call.make_call(cardsBase + item["id"] + "/customFieldItems?")
            for element in rr:
                if "idValue" in element:
                    card_fields.append(
                        {
                            "field_id": element["idCustomField"],
                            "card_id": element["idModel"],
                            "field_value_id": element["idValue"],
                        }
                    )
                elif "date" in element["value"]:
                    card_fields.append(
                        {
                            "field_id": element["idCustomField"],
                            "card_id": element["idModel"],
                            "field_date": element["value"]["date"],
                        }
                    )
                elif "text" in element["value"]:
                    card_fields.append(
                        {
                            "field_id": element["idCustomField"],
                            "card_id": element["idModel"],
                            "field_text": element["value"]["text"],
                        }
                    )
                elif "checked" in element["value"]:
                    card_fields.append(
                        {
                            "field_id": element["idCustomField"],
                            "card_id": element["idModel"],
                            "field_checked": element["value"]["checked"],
                        }
                    )
    cardField_frame = pd.DataFrame(card_fields)
    cardField_frame["field_date"] = pd.to_datetime(
        cardField_frame["field_date"]
    ).dt.date
    cardField_frame["field_date"] = cardField_frame["field_date"].astype(str)
    cardField_frame["field_date"] = cardField_frame["field_date"].apply(
        lambda x: None if x == "NaT" else x
    )
    cardField_frame["field_text"] = cardField_frame["field_text"].fillna(np.nan)
    cardField_frame["field_text"] = cardField_frame["field_text"].replace(
        {np.nan: None}
    )
    cardField_frame["field_value_id"] = cardField_frame["field_value_id"].fillna(np.nan)
    cardField_frame["field_value_id"] = cardField_frame["field_value_id"].replace(
        {np.nan: None}
    )
    return cardField_frame


def collectFieldOptions(flds):
    """This takes in a list of custom fields, filters them for type = list and
    makes API calls to grab the valid options and their ids. The ids can then
    be joined to the table that stores the value ids at the card level."""
    option_list = []
    filtered = flds[flds["field_type"] == "list"]
    for value in filtered["field_id"]:
        call = TrelloCall()
        options = call.make_call(customFieldBase + value + "/options")
        for item in options:
            option_list.append(
                {
                    "field_option_id": item["_id"],
                    "field_option_value": item["value"]["text"],
                    "field_option_color": item["color"],
                }
            )
    option_frame = pd.DataFrame(option_list)
    return option_frame


def tempBoard():
    temp = []
    temp.append(
        {
            "board_id": "5ba4e05a61a70d2da1c1cea0",
            "board_comment": True,
            "board_included": True,
        }
    )
    df = pd.DataFrame(temp)
    return df


# validboard = collectBoards(orgs=included_org)
# validlist = collectLists(brds=validboard)
# validmember = collectMembers(brds=validboard)
# validlabel = collectLabels(brds=validboard)
# validfield = collectFields(brds=validboard)
# card = collectCards(brds=validboard)
# comment = collectComments(brds=validboard)
# checklist = collectCheckLists(brds=validboard)
# field = collectCardFields(brds=tempBoard())
# fieldoption = collectFieldOptions(flds=validfield)

# print(field)


def execute_values(df):
    """
    Using psycopg2.extras.execute_values() to insert the dataframe
    """
    # Create a list of tupples from the dataframe values
    tuples = [tuple(x) for x in df.to_numpy()]
    # Comma-separated dataframe columns
    cols = ",".join(list(df.columns))
    # SQL quert to execute
    query = "INSERT INTO %s(%s) VALUES %%s" % ("comment", cols)
    return tuples


# print(execute_values(field))
