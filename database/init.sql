CREATE USER analyst_reader WITH PASSWORD 'analyst_reader_password';
GRANT CONNECT ON DATABASE analytics TO analyst_reader;
GRANT USAGE ON SCHEMA public TO analyst_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO analyst_reader;
