BEGIN;

-- Drop some tables we don't need such as cache table, country /
-- continent borders that will be recreated with the migration script
-- and potential celery tables that we don't use anymore

DO
$$
DECLARE
    row record;
BEGIN
    FOR row IN (SELECT tablename FROM pg_tables WHERE tablename LIKE 'djcelery_%') UNION
    (SELECT tablename FROM pg_tables WHERE tablename LIKE 'celery_%') UNION
    (SELECT tablename FROM pg_tables WHERE tablename LIKE 'data_%')
    LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(row.tablename) || ' CASCADE ;';
    END LOOP;
END;
$$;

DROP TABLE IF EXISTS cache CASCADE;


CREATE SCHEMA old_public;

DO
$$
DECLARE
    row record;
BEGIN
    FOR row IN SELECT tablename FROM pg_tables WHERE schemaname = 'public'
    LOOP
        EXECUTE 'ALTER TABLE public.' || quote_ident(row.tablename) || ' SET SCHEMA old_public;';
    END LOOP;
END;
$$;

COMMIT;
