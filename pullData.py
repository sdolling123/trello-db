import os
import requests
import config
import pandas as pd
import re
import numpy as np


"""
This script does the initial data pull from Trello.
"""

query = {
    "key": os.environ.get("TRELLO_KEY"),
    "token": os.environ.get("TRELLO_TOKEN"),
}

boardBase = config.boardBase
organizationBase = config.organizationBase
organizationParams = config.organizationParams
checklistParams = config.checklistParams
excluded_boards = config.excluded_boards
comments_included = config.comments_included
included_org = config.included_org
customFieldBase = config.customFieldBase


class TrelloCall:
    def __init__(self):
        """provide the key and token, base, and counter"""
        self.key = os.environ.get("TRELLO_KEY")
        self.token = os.environ.get("TRELLO_TOKEN")
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


def cardCreated(id):
    """
    This gets used inline with the card function to calculate the date a
    given card was created.
    """
    return pd.to_datetime(int(id[:8], 16), unit="s").date()


def collectBoards(orgs):
    """
    This function accepts a list of dictionaries containing organization IDs as well as whether to run
    that particular org. In return, a list of dictionaries is provided containing board name, board id,
    and whether that board is closed.
    """
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
    return board_frame


def fromBoardPull(board_list):
    """
    This takes the outcome for the collectBoards function and returns a data
    payload for card, label, list, member, validfield, customfield, comments
    will use this output for their own functions.
    """
    board_data = []
    for item in board_list["board_id"]:
        url = (
            "https://api.trello.com/1/boards/"
            + item
            + "/?fields=name&checklists=all&members=all&member_fields=id,fullName,username,idBoard&labels=all&label_fields=id,name,idBoard,color&lists=all&list_fields=name,closed,idBoard&cards=all&card_fields=name,idBoard,idList,idLabels,idMembers,closed,dateLastActivity,idShort,shortLink,shortUrl,idChecklists,checkItemStates,desc&customFields=true&card_customFieldItems=true&key="
            + query["key"]
            + "&token="
            + query["token"]
        )
        headers = {"Accept": "application/json"}
        response = requests.request("GET", url, headers=headers)
        response = response.json()
        board_data.append(response)
    return board_data


def cardDataPull(board_pull):
    """
    This returns a dataframe for all included board card data.
    """
    card_list = []
    for item in board_pull:
        for element in item["cards"]:
            card_list.append(
                {
                    "card_id": element["id"],
                    "card_creation": cardCreated(element["id"]),
                    "card_name": element["name"],
                    "card_description": element["desc"],
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
    return card_frame


def checklistDataPull(board_pull):
    check_list = []
    item_list = []
    for item in board_pull:
        for element in item["checklists"]:
            check_list.append(
                {
                    "checklist_id": element["id"],
                    "checklist_name": element["name"],
                    "card_id": element["idCard"],
                    "board_id": element["idBoard"],
                }
            )
        for index in range(len(item["checklists"])):
            for value in item["checklists"][index]["checkItems"]:
                item_list.append(
                    {
                        "checklist_id": value["idChecklist"],
                        "item_state": value["state"],
                        "item_id": value["id"],
                        "item_name": value["name"],
                        "item_member": value["idMember"],
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
    return full_checklist


def validFieldOptionDataPull(validfield):
    """
    This takes in a list of custom fields, filters them for type = list and
    makes API calls to grab the valid options and their ids. The ids can then
    be joined to the table that stores the value ids at the card level.
    """
    option_list = []
    filtered = validfield[validfield["field_type"] == "list"]
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


def validListDataPull(board_pull):
    """
    Returns a dataframe for all list data for included boards.
    """
    list_dict = []
    for item in board_pull:
        for element in item["lists"]:
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


def validLabelDataPull(board_pull):
    """
    Returns a dataframe for label data for all included boards.
    """
    label_dict = []
    for item in board_pull:
        for element in item["labels"]:
            label_dict.append(
                {
                    "label_id": element["id"],
                    "label_name": element["name"],
                    "board_id": element["idBoard"],
                    "label_color": element["color"],
                }
            )
    label_frame = pd.DataFrame(label_dict)
    return label_frame


def validMemberDataPull(board_pull):
    """
    Returns a dataframe for all included board member data.
    """
    full_list = []
    for item in board_pull:
        for element in item["members"]:
            full_list.append(
                {
                    "member_id": element["id"],
                    "member_name": element["fullName"],
                    "member_username": element["username"],
                }
            )
    member_frame = pd.DataFrame(full_list)
    member_frame = pd.DataFrame(full_list).drop_duplicates(inplace=False)
    return member_frame


def validFieldDataPull(board_pull):
    """
    Returns a dataframe for all validCustomField data for included boards.
    """
    field_dict = []
    for item in board_pull:
        for element in item["customFields"]:
            field_dict.append(
                {
                    "field_id": element["id"],
                    "field_name": element["name"],
                    "board_id": element["idModel"],
                    "field_type": element["type"],
                }
            )
        field_frame = pd.DataFrame(field_dict)
    return field_frame


def commentDataPull(board_pull):
    """
    Returns dataframe for comments for comment included boards.
    """
    comment_dict = []
    for item in board_pull:
        for element in item["cards"]:
            url = (
                "https://api.trello.com/1/cards/"
                + element["id"]
                + "/actions?filter=commentCard"
                + "&key="
                + query["key"]
                + "&token="
                + query["token"]
            )
            headers = {"Accept": "application/json"}
            response = requests.request("GET", url, headers=headers)
            r = response.json()
            for item in r:
                comment_dict.append(
                    {
                        "card_id": element["id"],
                        "member_id": item["idMemberCreator"],
                        "card_comment": item["data"]["text"],
                        "comment_date": item["date"],
                    }
                )
    comment_frame = pd.DataFrame(comment_dict)
    comment_frame["comment_date"] = pd.to_datetime(
        comment_frame["comment_date"]
    ).dt.date
    return comment_frame


def fieldDataPull(board_pull):
    """
    Returns factual information for fields at the card level for included boards.
    """
    field_dict = []
    for value in board_pull:
        for item in value["cards"]:
            for element in item["customFieldItems"]:
                if "idValue" in element:
                    field_dict.append(
                        {
                            "field_id": element["idCustomField"],
                            "card_id": element["idModel"],
                            "field_value_id": element["idValue"],
                        }
                    )
                elif "date" in element["value"]:
                    field_dict.append(
                        {
                            "field_id": element["idCustomField"],
                            "card_id": element["idModel"],
                            "field_date": element["value"]["date"],
                        }
                    )
                elif "text" in element["value"]:
                    field_dict.append(
                        {
                            "field_id": element["idCustomField"],
                            "card_id": element["idModel"],
                            "field_text": element["value"]["text"],
                        }
                    )
                elif "checked" in element["value"]:
                    field_dict.append(
                        {
                            "field_id": element["idCustomField"],
                            "card_id": element["idModel"],
                            "field_checked": element["value"]["checked"],
                        }
                    )
    cardField_frame = pd.DataFrame(field_dict)
    return cardField_frame
