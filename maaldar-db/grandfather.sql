-- One-shot: freeze the set of users who keep their Maaldar role after they stop
-- boosting. 15552000 s = 180 days. Run on deploy day (2026-09-29) only: a later
-- run would also grandfather anyone who passed 180 days after the cutoff.
CREATE TABLE IF NOT EXISTS MaaldarGrandfathered (user_id text PRIMARY KEY);
INSERT INTO MaaldarGrandfathered
  SELECT user_id FROM MaaldarDuration WHERE boosting_since >= 15552000
  ON CONFLICT DO NOTHING;
SELECT count(*) AS grandfathered FROM MaaldarGrandfathered;
