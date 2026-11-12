# SUPERVISOR DIRECTIVE 4 (Opus): HOLD the J2 holdout run until one more S2 attempt finishes

Order matters. Once J2's holdout is opened, S2 can never share it. Dropping S2 because of a PID-guard bug would permanently waste the last lever. My "final" rule covered a genuine measurement crash; a guard that fires before any data request is neither.

Fix: DELETE the single-process guard entirely (one worker, one process; the coordinator ensures no duplicate launch). Log the diff and code hash. Same frozen event list, same counted trial, ~30 min. Report dev CAR for 500, 400 and pooled, and apply the MDE rule with holdout N=255.

Whatever comes out (pass, fail on MDE, or a true crash) is final. Then freeze J2 (+S2 if it clears) and run the holdout once with user approval.
