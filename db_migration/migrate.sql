BEGIN;

SET search_path TO public;

-- auth_group

INSERT INTO auth_group (id, name)
    SELECT id, name FROM old_public.auth_group;
SELECT setval('auth_group_id_seq', COALESCE((SELECT MAX(id)+1 FROM auth_group), 1), false);

-- auth_user

INSERT INTO auth_user (id, username, first_name, last_name, email, password, is_staff, is_active, is_superuser, last_login, date_joined)
    SELECT id, username, first_name, last_name, email, password, is_staff, is_active, is_superuser, last_login, date_joined FROM old_public.auth_user;
SELECT setval('auth_user_id_seq', COALESCE((SELECT MAX(id)+1 FROM auth_user), 1), false);

-- django_admin_log

INSERT INTO django_admin_log (id, change_message, action_flag, object_repr, object_id, content_type_id, user_id, action_time)
    SELECT id, change_message, action_flag, object_repr, object_id, content_type_id, user_id, action_time FROM old_public.django_admin_log;
SELECT setval('django_admin_log_id_seq', COALESCE((SELECT MAX(id)+1 FROM django_admin_log), 1), false);

-- django_comment_flags

INSERT INTO django_comment_flags (id, flag_date, flag, comment_id, user_id)
    SELECT id, flag_date, flag, comment_id, user_id FROM old_public.django_comment_flags;
SELECT setval('django_comment_flags_id_seq', COALESCE((SELECT MAX(id)+1 FROM django_comment_flags), 1), false);

-- django_comments

INSERT INTO django_comments (id, is_removed, is_public, ip_address, submit_date, comment, user_url, user_email, user_name, user_id, site_id, object_pk, content_type_id)
    SELECT id, is_removed, is_public, ip_address, submit_date, comment, user_url, user_email, user_name, user_id, site_id, object_pk, content_type_id FROM old_public.django_comments;
SELECT setval('django_comments_id_seq', COALESCE((SELECT MAX(id)+1 FROM django_comments), 1), false);

-- django_site

-- Delete existing default site
DELETE FROM django_site;
INSERT INTO django_site (id, domain, name)
    SELECT id, domain, name FROM old_public.django_site;
SELECT setval('django_site_id_seq', COALESCE((SELECT MAX(id)+1 FROM django_site), 1), false);

-- events_event

INSERT INTO events_event (id, exact, timezone, version, coordinates, description, address, city, country, tags, endtime, starttime, title, acronym, modification_time, creation_time, user_id)
    SELECT id, exact, timezone, version, coordinates, description, address, city, country, tags, endtime, starttime, title, acronym, modification_time, creation_time, user_id FROM old_public.events_event;
SELECT setval('events_event_id_seq', COALESCE((SELECT MAX(id)+1 FROM events_event), 1), false);


-- replaceit

INSERT INTO replaceit (id, )
    SELECT id,  FROM old_public.replaceit;
SELECT setval('replaceit_id_seq', COALESCE((SELECT MAX(id)+1 FROM replaceit), 1), false);


ROLLBACK;
