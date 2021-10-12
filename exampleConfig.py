"""
This file contains basic configuration in order to run the proceeding scripts.
NOTE: This is a an example Config file with dummy data intended to exemplify
how to set up the file to run scripts.
"""


"""
This is a list of idBoards to not include in the data pull. This list gets
used to add a key/value to the board list to flag whether to include
"""
excluded_boards = [
    "123123123123",
    "456456456456",
    "678678678678",
]

"""
This is a specific list of board Ids that comments are being included.
Comments result in a long run time for the program and not every user is
utilizing comments for dashboard purposes. Should a user require comments
be included in their dashboard, the id of their board needs to be added
to this list.
"""
comments_included = [
    "6786786786786",
    "0898098908908",
    "2234098083456",
]


"""
This is a list of dictionaries that identifies which organizations
to include in the data pull and which to exclude. The purpose of this is
to make this user agnostic such that the id of the organization is used to
pull the boards for which the majority of the resulting functions depend.
"""
included_org = [
    {"orgId": "456456456456", "orgName": "FAKE_ORG_NAME", "include": True},
    {"orgId": "456697897899", "orgName": "ANOTHER_FAKE_ORG_NAME", "include": True},
    {
        "orgId": "1236678999",
        "orgName": "82934902348",
        "include": False,
    },
]

"""
This provides the commonly used API queries and params.
"""
boardBase = "https://api.trello.com/1/boards/"
organizationBase = "https://api.trello.com/1/organizations/"
organizationParams = "/boards?fields=id,name,closed"
cardsBase = "https://api.trello.com/1/cards/"
membersParams = "/members"
listParams = "/lists?fields=id,name,idBoard,closed&filter=all"
labelParams = "/labels?fields=id,name,idBoard,color"
customFieldParams = "/customFields?fields=id,name,idModel,type"
cardsParams = "/cards?fields=id,name,idBoard,closed,dateLastActivity,idLabels,idList,idMembers,idShort,shortLink,shortUrl&filter=all"
checklistParams = "/?fields=name&checklists=all&checklist_fields=id,name,idCard,idBoard&checkItem_fields=name"
customFieldBase = "https://api.trello.com/1/customFields/"
