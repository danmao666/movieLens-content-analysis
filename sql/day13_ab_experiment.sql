-- Day 13 is an experiment design task. No randomized experiment result exists
-- in MovieLens, so do not manufacture a treatment/control result.

-- The future primary metric definition:
-- COUNT(DISTINCT users with at least one event in the seven-day window)
-- divided by COUNT(DISTINCT eligible assigned users).

-- Suggested guardrail data checks after a real experiment table exists:
-- 1. Assignment balance by variant.
-- 2. One assignment per user.
-- 3. Event completeness by variant.
-- 4. Rating-active rate and content diversity by variant.
