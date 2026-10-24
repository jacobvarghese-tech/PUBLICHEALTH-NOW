# Review packet: Medicare Fraud Flagger

Written 2026-10-24. The lower-scoring model files were removed the same day. No model was refit to write this file.

A high score means the billing row resembles providers who were later excluded for a fraud-type reason. It is not a finding that the firm committed fraud.

## What to open

| What | Path |
|---|---|
| App | `app/index.html`, served by `app/server.py` |
| About page | `app/about.html` |
| Contest brief | `AGENTS.md` |
| Build brief | `handoff-firm-flagging.md` |
| This packet | `REVIEW.md` |
| Score ledger | `models/model_island_db.json` |

The page loads `models/candidates/blend_357_247.joblib`. The lower-scoring model files were removed on 2026-10-24.

## The smallest highest-scoring saved ranker

`models/candidates/blend_357_247.joblib`

- Recorded 2024 top 1 percent: **26 of 48**
- Recorded 2024 top 5 percent: **26 of 48**
- Size: **414.05 MB**
- How it scores: the higher of the ranked scores from candidates 357 and 247. Both forests are stored inside this one file. `scripts/save_blend.py` wrote it. It did not fit a new forest.
- Ledger: `models/model_island_db.json` has `best_confirm_top1` 26 and `best_spec` `blend_357_247.joblib`. `models/overseer_state.json` names the same file.

No saved candidate in that ledger has `confirm_top1` above 26. The next saved forests, 357 at 25 of 48 and 247, were copied inside the blend and then removed from disk.

2024 has 48 fraud rows. That is below the published external-validation floor of at least 100 events, ideally 200 or more, so 26 of 48 is not a precise estimate of next-year capture.

## What was removed

On 2026-10-24 the lower-scoring `.joblib` files, their notes, and the spec folders were removed. About 1,813 MB left the disk. `models/` now holds the blend, `models/model_island_db.json`, and `models/overseer_state.json`.

`app/server.py` loads the blend. A typed row and a stored year both take the higher of the two ranks inside that file. The scoring code that the blend calls is still in `scripts/optimized_rank.py`, `scripts/paper_forest.py`, and `scripts/save_blend.py`.

Kept on disk:

| File | MB | Role |
|---|---:|---|
| `models/candidates/blend_357_247.joblib` | 414.05 | The model the page loads. |
| `models/model_island_db.json` | 0.09 | Ledger for the 26 of 48 count. |
| `models/overseer_state.json` | 0.00 | Names the same best file. |

## What a reviewer should know before judging the score

- The about page names the blend and keeps the earlier 11 of 48 figure so a reviewer can see what the first model did.
- The blend's recorded top 5 percent is 26 of 48. The page forest's recorded top 5 percent is 48 of 48. A reviewer who cares about both cutoffs should see both numbers.
- Training for the second forest stayed inside 2013–2022. 2023 was the selection year. 2024 was the confirm year.
- Libraries and tools used to build the pipeline are listed on the about page. Grok, in the Grok Build CLI, was used to build the pipeline, the model step, and the page. The student describes their own part in the portal, in their own words.

## Submission clock

Treat noon Eastern on Monday, October 26, 2026 as the submission deadline. Submit earlier. After the submission period ends, the submission cannot be changed.
