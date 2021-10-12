DROP TABLE IF EXISTS validboard CASCADE;

DROP TABLE IF EXISTS card CASCADE;

DROP TABLE IF EXISTS comment CASCADE;

DROP TABLE IF EXISTS checklist CASCADE;

DROP TABLE IF EXISTS field CASCADE;

DROP TABLE IF EXISTS validfieldoption CASCADE;

DROP TABLE IF EXISTS validfield CASCADE;

DROP TABLE IF EXISTS validlabel CASCADE;

DROP TABLE IF EXISTS validlist CASCADE;

DROP TABLE IF EXISTS validmember CASCADE;

CREATE TABLE validboard (
    board_name TEXT,
    board_id TEXT,
    board_closed BOOLEAN,
    board_included BOOLEAN,
    board_comment BOOLEAN,
    schema_name TEXT
);

CREATE TABLE card (
    card_id TEXT,
    card_creation DATE,
    card_name TEXT,
    card_description TEXT,
    board_id TEXT,
    list_id TEXT,
    card_last_active DATE,
    label_id TEXT,
    member_id TEXT,
    card_number TEXT,
    card_link TEXT,
    card_url TEXT,
    card_closed BOOLEAN
);

CREATE TABLE comment (
    card_id TEXT,
    member_id TEXT,
    card_comment TEXT,
    comment_date DATE
);

CREATE TABLE checklist (
    checklist_id TEXT,
    item_state TEXT,
    item_id TEXT,
    item_name TEXT,
    item_member TEXT,
    checklist_name TEXT,
    card_id TEXT,
    board_id TEXT
);

CREATE TABLE field (
    field_id TEXT,
    card_id TEXT,
    field_text TEXT,
    field_value_id TEXT,
    field_date DATE
);

CREATE TABLE validfieldoption (
    field_option_id TEXT,
    field_option_value TEXT,
    field_option_color TEXT
);

CREATE TABLE validfield (
    field_id TEXT,
    field_name TEXT,
    board_id TEXT,
    field_type TEXT
);

CREATE TABLE validlabel (
    label_id TEXT,
    label_name TEXT,
    board_id TEXT,
    label_color TEXT
);

CREATE TABLE validlist (
    list_id TEXT,
    list_name TEXT,
    board_id TEXT,
    list_closed BOOLEAN
);

CREATE TABLE validmember (
    member_id TEXT,
    member_name TEXT,
    member_username TEXT
);