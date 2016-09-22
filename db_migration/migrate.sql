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

-- events_calendar

INSERT INTO events_calendar (id, date_added, group_id, event_id)
    SELECT id, date_added, group_id, event_id FROM old_public.events_calendar;
SELECT setval('events_calendar_id_seq', COALESCE((SELECT MAX(id)+1 FROM events_calendar), 1), false);

-- events_eventsession

INSERT INTO events_eventsession (id, session_endtime, session_starttime, session_date, session_name, event_id)
    SELECT id, session_endtime, session_starttime, session_date, session_name, event_id FROM old_public.events_eventsession;
SELECT setval('events_eventsession_id_seq', COALESCE((SELECT MAX(id)+1 FROM events_eventsession), 1), false);

-- events_eventurl

INSERT INTO events_eventurl (id, url, url_name, event_id)
    SELECT id, url, url_name, event_id FROM old_public.events_eventurl;
SELECT setval('events_eventurl_id_seq', COALESCE((SELECT MAX(id)+1 FROM events_eventurl), 1), false);

-- events_filter

INSERT INTO events_filter (id, email, name, query, modification_time, user_id)
    SELECT id, email, name, query, modification_time, user_id FROM old_public.events_filter;
SELECT setval('events_filter_id_seq', COALESCE((SELECT MAX(id)+1 FROM events_filter), 1), false);

-- events_group

INSERT INTO events_group (id, modification_time, creation_time, description, name)
    SELECT id, modification_time, creation_time, description, name FROM old_public.events_group;
SELECT setval('events_group_id_seq', COALESCE((SELECT MAX(id)+1 FROM events_group), 1), false);

-- events_groupinvitation

INSERT INTO events_groupinvitation (id, issue_date, activation_key, as_administrator, group_id, guest_id, host_id)
    SELECT id, issue_date, activation_key, as_administrator, group_id, guest_id, host_id FROM old_public.events_groupinvitation;
SELECT setval('events_groupinvitation_id_seq', COALESCE((SELECT MAX(id)+1 FROM events_groupinvitation), 1), false);

-- events_membership

INSERT INTO events_membership (id, date_joined, new_member_email, new_event_email, is_administrator, group_id, user_id)
    SELECT id, date_joined, new_member_email, new_event_email, is_administrator, group_id, user_id FROM old_public.events_membership;
SELECT setval('events_membership_id_seq', COALESCE((SELECT MAX(id)+1 FROM events_membership), 1), false);

-- events_recurrence
-- NOTE: in old data, id was missing

INSERT INTO events_recurrence (master_id, event_id)
    SELECT master_id, event_id FROM old_public.events_recurrence;

-- events_revisioninfo

INSERT INTO events_revisioninfo (id, reason, redirect, as_text, revision_id)
    SELECT id, reason, redirect, as_text, revision_id FROM old_public.events_revisioninfo;
SELECT setval('events_revisioninfo_id_seq', COALESCE((SELECT MAX(id)+1 FROM events_revisioninfo), 1), false);

-- oembed_providerrule
-- NOTE: We don't migrate oembed_providerrule, it is already pre-populated by
-- ./manage.py migrate. Just confirm data / ids are same.
-- INSERT INTO oembed_providerrule (id, format, endpoint, regex, name)
--    SELECT id, format, endpoint, regex, name FROM old_public.oembed_providerrule;
-- SELECT setval('oembed_providerrule_id_seq', COALESCE((SELECT MAX(id)+1 FROM oembed_providerrule), 1), false);

-- oembed_storedoembed

INSERT INTO oembed_storedoembed (id, date_added, html, max_height, max_width, match)
    SELECT id, date_added, html, max_height, max_width, match FROM old_public.oembed_storedoembed;
SELECT setval('oembed_storedoembed_id_seq', COALESCE((SELECT MAX(id)+1 FROM oembed_storedoembed), 1), false);

-- registration_registrationprofile

-- NOTE: there is a new bool, not null, field called "activated". We assume
-- and insert a "true" value.

INSERT INTO registration_registrationprofile (id, activation_key, user_id, activated)
    SELECT id, activation_key, user_id, true FROM old_public.registration_registrationprofile;
SELECT setval('registration_registrationprofile_id_seq', COALESCE((SELECT MAX(id)+1 FROM registration_registrationprofile), 1), false);

-- tagging_tag

INSERT INTO tagging_tag (id, name)
    SELECT id, name FROM old_public.tagging_tag;
SELECT setval('tagging_tag_id_seq', COALESCE((SELECT MAX(id)+1 FROM tagging_tag), 1), false);

-- tagging_taggeditem

INSERT INTO tagging_taggeditem (id, object_id, content_type_id, tag_id)
    SELECT id, object_id, content_type_id, tag_id FROM old_public.tagging_taggeditem;
SELECT setval('tagging_taggeditem_id_seq', COALESCE((SELECT MAX(id)+1 FROM tagging_taggeditem), 1), false);

-- reversion_revision
-- NOTE: the former field "manager_slug" is removed. Value was 'default' in all rows
-- it is assumed to be used as "db" value for reversion_version

INSERT INTO reversion_revision (id, comment, user_id, date_created)
    SELECT id, comment, user_id, date_created FROM old_public.reversion_revision;
SELECT setval('reversion_revision_id_seq', COALESCE((SELECT MAX(id)+1 FROM reversion_revision), 1), false);

-- reversion_version
-- NOTE: former fields "object_id_int" and "type" are removed, new field
-- "db" added assuming the value 'default'

INSERT INTO reversion_version (id, object_repr, serialized_data, format, content_type_id, object_id, revision_id, db)
    SELECT id, object_repr, serialized_data, format, content_type_id, object_id, revision_id, 'default' FROM old_public.reversion_version;
SELECT setval('reversion_version_id_seq', COALESCE((SELECT MAX(id)+1 FROM reversion_version), 1), false);

--
-- TODO: FIXME: Map the content_type_id according to new (public) schema
--

ROLLBACK;
