-- Members who keep their Maaldar role after they stop boosting even though they
-- have less than the 365 days the bot normally requires (util.is_old_maaldar).
-- Rows are hand-picked exceptions, added with:
--   INSERT INTO MaaldarGrandfathered VALUES ('<user id>') ON CONFLICT DO NOTHING;
CREATE TABLE IF NOT EXISTS MaaldarGrandfathered (user_id text PRIMARY KEY);
