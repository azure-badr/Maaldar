CREATE OR REPLACE FUNCTION delete_expired_sessions()
RETURNS VOID AS $$
BEGIN
  DELETE FROM MaaldarSession WHERE now() - created_at > INTERVAL '1 hour';
END;
$$ LANGUAGE plpgsql;