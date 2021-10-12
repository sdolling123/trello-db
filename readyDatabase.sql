UPDATE card 
SET label_id = REPLACE(REPLACE(REPLACE(REPLACE(label_id, '[', '{'),']','}'),' ',''),'''','');

UPDATE card 
SET member_id = REPLACE(REPLACE(REPLACE(REPLACE(member_id, '[', '{'),']','}'),' ',''),'''','');

UPDATE card
SET label_id = f_get_label(label_id);

UPDATE card
SET member_id = f_get_member(member_id);

ALTER TABLE public.card RENAME COLUMN label_id TO label;

ALTER TABLE public.card RENAME COLUMN member_id TO member;

ALTER TABLE public.card ADD COLUMN card_age INTERVAL NULL;

UPDATE card
SET card_age = AGE(card_creation);

CALL p_create_views('timetrade');

CALL p_create_views('teambazing');

CALL p_create_views('dsdgisintern');