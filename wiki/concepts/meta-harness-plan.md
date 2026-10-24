---
type: concept
title: Meta harness plan
updated: 2026-10-22
tags: [app, model, planning]
sources:
  - https://docs.x.ai/developers/models/grok-4.5
  - https://docs.x.ai/developers/models/grok-4.7.md
  - https://docs.x.ai/developers/quickstart
  - https://raw.githubusercontent.com/shap/shap/master/README.md
  - https://raw.githubusercontent.com/marcotcr/lime/master/README.md
  - https://pypi.org/pypi/ripgrep-rs/json
  - https://pypi.org/project/rank-bm25/
  - https://scikit-learn.org/stable/install.html
  - https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html
  - scripts/meta_harness.py
  - harness/score_rows.py
  - models/optimized_note.txt
  - models/harness_rank_note.txt
  - models/rank_evolve_note.txt
---

# Meta harness plan

Filed 2026-10-22. This page is the plan. Writer model `grok-4.5`. Reviewer model `grok-4.7`. Parent script `scripts/meta_harness.py`. Harness folder `harness/`. The file that records the 2024 count out of 48 is `models/meta_harness_note.txt`.

`grok-4.7` reviewed each numbered step against the opened pages and the parent files, and passed it. Step 6 came back once with a miss on the RankEvolve confirmation wording. `grok-4.5` rewrote that line. `grok-4.7` passed the rewrite. This page merges only those passed slices.

Do not start `scripts/meta_harness.py` from this page. Do not use /deep-research. Do not fit a model. Do not edit `app/`. Do not replace `models/xgb_shallow.json`, `models/paper_forest.joblib`, or `models/optimized_model.joblib`.

A high score means resemblance to later fraud-type exclusions. It is not a finding that the firm committed fraud.

Numbered steps follow. A later session can say "do step 4."

## 1. How to use the plan

This page is a plan for a later session. Do not start `scripts/meta_harness.py` from this page. Do not use /deep-research. Do not fit a model. Do not edit `app/`. Do not replace `models/xgb_shallow.json`, `models/paper_forest.joblib`, or `models/optimized_model.joblib`.

The writer model is grok-4.5. The reviewer model is grok-4.7. The parent scorekeeper is `scripts/meta_harness.py`. The harness code lives under `harness/`. The 2024 count is written to `models/meta_harness_note.txt`. When a later session names a numbered step, it says "do step 4" (or whichever step number applies).

The score is fraud rows caught in the top 1 percent of the 2024 year, out of 48. Higher is better. Also record the top 5 percent count out of 48. Accuracy is not a score. A high score means resemblance to later fraud-type exclusions. It is not a finding that the firm committed fraud.

Prior losses are facts, not a reason to stop: prompt harness 1/48 on the 288-row subsample; RankEvolve kept none of 20 and confirmed 3/48. Current best to beat is optimized rank 20/48 on the full year.

On-disk defaults `PROPOSAL_COUNT = 12` and `PROPOSER_MODEL = grok-4.6` are not the live run. The live search does not call `run_loop`, because `run_loop` keeps a fitness-only gain inside `should_keep` before the session can apply the count-rise rule; the session runs its own 20-proposal loop and calls `score_source`, and it does not edit the parent. It does not hand the scorekeeper source to the harness writer.

Do not print `XAI_API_KEY`. Do not write it into a file. Use the key name only. Base URL is `https://api.x.ai/v1`.

Workspace: `C:\Users\Jacob\Downloads\congressional app`. Windows. Python 3.14.4.

Opened 2026-10-22 with `Accept: text/markdown`:

- https://docs.x.ai/developers/models/grok-4.5 printed Model name `grok-4.5`. Aliases printed: `grok-4.5-latest`, `grok-build-latest`. Do not use an alias. Writer calls use `grok-4.5`.
- https://docs.x.ai/developers/models/grok-4.7.md printed Model name `grok-4.7`. No alias printed. Do not invent one. Reviewer calls use `grok-4.7`.
- Both pages printed reasoning efforts `low`, `medium`, `high`, `xhigh`, default `high`.

## 2. Tool install steps

Opened 2026-10-22. Install lines below are copied from the pages named in each item. A grok-4.7 reviewer of this slice accepts or rejects each line. The writer does not mark a line accepted.

A high score means resemblance to later fraud-type exclusions. It is not a finding that the firm committed fraud. Accuracy is not a score. Prior harnesses lost (prompt harness 1/48 on the 288-row subsample; RankEvolve kept none of 20). That loss is why these tools are in the plan. Do not conclude the run would not work.

Parent constraint: `scripts/meta_harness.py` `reject_reason` rejects any import, any open, and any read of NPI, name, city, state, ZIP, or year inside `harness/score_rows.py`. The later agent may widen `harness/` with helpers. The scored `score_rows` file must not import a module that reads those identifiers. Explainers and rankers are parent-side or helper-side notes that feed the proposer. The scored function still returns one float per row from the eight billing fields plus `tree_score` and `paper_score`. The parent computes those two frozen scores. The harness does not fit a model on labels. 2024 labels stay out of the prompt that writes the harness.

### 2.1 OpenAI-compatible client

- Page opened: https://docs.x.ai/developers/quickstart
- Same pip line also on https://pypi.org/pypi/openai/json (`pip install openai`, `from openai import OpenAI`).
- Install command: `pip install openai`
- Client from the quickstart page: `from openai import OpenAI` then `OpenAI(api_key=os.getenv("XAI_API_KEY"), base_url="https://api.x.ai/v1")`.
- Pin: `requirements.txt` already lists `openai==2.54.0`. Reinstall only if the import check fails. Do not upgrade past the pin unless the import fails. Do not print the key. Do not write the key into a file.
- Import check: `py -3.14 -c "from openai import OpenAI; print('openai-ok')"`
- Why it can raise the count out of 48: the later parent calls `grok-4.5` to propose the next harness file and `grok-4.7` to review that file before the parent scores it. That propose/review cycle is the path to catching more of the 48 fraud rows in the top 1 percent.

### 2.2 SHAP

- Page opened: https://raw.githubusercontent.com/shap/shap/master/README.md
- Docs home https://shap.readthedocs.io/en/latest/ loaded with title "Welcome to the SHAP documentation — SHAP latest documentation" and did not print a pip line. The install line is from the README.
- Install command printed on the README: `pip install shap`
- The README also printed `conda install -c conda-forge shap`. Prefer pip.
- Import check: `py -3.14 -c "import shap; print('shap-ok')"`
- Why it can raise the count out of 48: a parent-side helper can explain which of the eight billing fields and which of `tree_score` and `paper_score` move a missed 2023 selection fraud row. The proposer sees that note and can combine fields so more of the 48 land in the top 1 percent. The scored `harness/score_rows.py` must not import `shap` while the parent rejects imports in that file.

### 2.3 LIME

- Page opened: https://raw.githubusercontent.com/marcotcr/lime/master/README.md and https://github.com/marcotcr/lime
- Install command printed on the README: `pip install lime`
- PyPI JSON https://pypi.org/pypi/lime/json printed name `lime`, version `0.2.0.1`, summary "Local Interpretable Model-Agnostic Explanations for machine learning classifiers", `requires_python >=3.5`. The JSON description field was empty, so the install line comes from the README.
- Import check: `py -3.14 -c "import lime; print('lime-ok')"`
- Why it can raise the count out of 48: a local explanation of a missed 2023 selection fraud row tells the proposer which billing field to nudge. That can lift more of the 48 into the top 1 percent. The scored `score_rows` file must not import `lime` while the parent rejects imports.

### 2.4 ripgrep-rs

- Page opened: https://pypi.org/pypi/ripgrep-rs/json
- The HTML page https://pypi.org/project/ripgrep-rs/ returned a bot challenge and did not print an install line. Use the JSON page.
- Install command printed in the JSON description: `pip install ripgrep-rs`
- Usage printed: `from ripgrep_rs import search` (also `search_structured` and `files`).
- A Windows cp314 wheel name was visible: `ripgrep_rs-0.3.12-cp314-cp314-win_amd64.whl`. Do not pin that version. The page's install line is unpinned.
- Import check: `py -3.14 -c "from ripgrep_rs import search; print('ripgrep-ok')"`
- Why it can raise the count out of 48: the later writer can search `harness/` for the score contract without receiving the evaluator. That search can raise the chance a proposal catches more of the 48 fraud rows in the top 1 percent. The scored `score_rows` file must not import `ripgrep_rs` while the parent rejects imports.

### 2.5 rank-bm25

- Page opened: https://pypi.org/project/rank-bm25/ printed in the HTML: `pip install rank-bm25`
- JSON description at https://pypi.org/pypi/rank-bm25/json also printed `pip install rank_bm25` and `from rank_bm25 import BM25Okapi`. It also printed a `git+ssh` line. Skip the git line. It is not the immediate pip line.
- Install command: `pip install rank-bm25`
- Import check: `py -3.14 -c "from rank_bm25 import BM25Okapi; print('bm25-ok')"`
- Why it can raise the count out of 48: the parent, not the scored `score_rows` file, can rank missed-row notes and pass one extra frozen rank into the proposer note. The scored file must not import `rank_bm25` while the parent rejects imports, and must not read NPI, name, city, state, ZIP, or year. This can raise the fraud-row count in the top 1 percent out of 48.

### 2.6 scikit-learn IsolationForest

- Pages opened: https://scikit-learn.org/stable/install.html title "Installing scikit-learn — scikit-learn 1.9.1 documentation". The Windows example printed `pip install -U scikit-learn`.
- https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html title "IsolationForest — scikit-learn 1.9.1 documentation". Printed: `decision_function = score_samples - offset_`.
- `requirements.txt` already pins `scikit-learn==1.9.1`. Do not upgrade. Import check is enough. Do not run `pip install -U scikit-learn`.
- Import check: `py -3.14 -c "from sklearn.ensemble import IsolationForest; print('iforest-ok')"`
- Fit split: the parent may compute an extra frozen anomaly score from the eight billing fields and pass it in. The scored file must not fit a model and must not read NPI, name, city, state, ZIP, or year.
- Why it can raise the count out of 48: combining an anomaly score with `tree_score` and `paper_score` can lift a row that resembles a later fraud-type exclusion into the top 1 percent, raising the count out of 48.

### 2.7 ELI5 skipped

Pages opened 2026-10-22: https://pypi.org/project/eli5/ returned a bot challenge shell and did not print an install line. https://pypi.org/pypi/eli5/json description explained ELI5 as a package that debugs classifiers and explains predictions. The loaded description did not contain `pip install`. https://raw.githubusercontent.com/eli5-org/eli5/master/README.rst loaded and also did not print a pip install line. Do not invent `pip install eli5`. Skip the tool. A later session may reopen the package page and add it only if that reopen prints an install line.

### 2.8 Install order

1. OpenAI client only if `from openai import OpenAI` fails.
2. `pip install shap`
3. `pip install lime`
4. `pip install ripgrep-rs`
5. `pip install rank-bm25`
6. scikit-learn: import check only. No upgrade.
7. ELI5: skip.

```text
py -3.14 -c "from openai import OpenAI; print('openai-ok')"
py -3.14 -c "import shap; print('shap-ok')"
py -3.14 -c "import lime; print('lime-ok')"
py -3.14 -c "from ripgrep_rs import search; print('ripgrep-ok')"
py -3.14 -c "from rank_bm25 import BM25Okapi; print('bm25-ok')"
py -3.14 -c "from sklearn.ensemble import IsolationForest; print('iforest-ok')"
```

A high score means resemblance to later fraud-type exclusions. It is not a finding that the firm committed fraud.

## 3. The harness contract

3.1. Keep `harness/score_rows.py` as the scored entry point. The seed is `score_rows(rows)` returning `[float(row["paper_score"]) for row in rows]`. The docstring states that frozen scores are already computed. `tree_score` is the shallow XGBoost probability. `paper_score` is the page-forest score. The eight billing fields are the features. Return one float per row, same order, same length. Higher means more resemblance to later fraud-type exclusions. Do not say the firm committed fraud. Accuracy is not a score.

3.2. Treat each row from `harness_rows` in `scripts/meta_harness.py` as the eight billing fields plus parent-computed `tree_score` and `paper_score`. Exact names: `Service count`, `Beneficiary count`, `Average charge`, `Average payment`, `Charge-to-payment ratio`, `Top-code share`, `Specialty`, `Growth`. No identifier is placed on the row. The parent alone computes those two scores.

3.3. The parent gets `tree_score` via `tree_scores_for` and `paper_score` via `paper_scores_for` (which reads `data/paper_scores/{year}.csv`). The harness must not recompute, refit, or reload those scores.

3.4. Never use identifiers as features. Forbidden reads: NPI, name, city, state, ZIP, year. `BANNED_READS` in the parent are `NPI`, `Name`, `City`, `State`, `ZIP`, `Year`. The harness must not import a module that reads those fields.

3.5. The current parent `reject_reason` rejects `Import`, `ImportFrom`, calls to `import`, `__import__`, `importlib`, `reload`, `open`, or `file`, and any name, attribute, string, or subscript equal to a banned read. `score_rows` must be exactly one function taking `rows`. A candidate that fails these checks is rejected before it is scored. The plan may widen `harness/` so helpers may exist. The scored `score_rows` source still must not import, must not open a file, and must not read those identifiers.

3.6. `run_harness` requires a list of finite floats, same length as `rows`, same order. The parent keeps a candidate only when the 2023 top 1 percent fraud count rises and the top 1 percent slice stays at most 2 percent of the selection rows. 2024 is scored once, after the search stops, as the top 1 percent count out of 48 and the top 5 percent count out of 48. Do not put 2024 labels in the prompt that writes the harness.

3.7. Do not hand the agent the evaluator. Do not give the harness writer `scripts/meta_harness.py`, `scripts/rank_evolve.py`, `scripts/harness_score.py`, the label file, `app/`, or the saved model binaries. The agent does not edit those files. The parent remains the only scorer of the 2023 keep decision and the one 2024 score.

3.8. If a later helper needs an extra frozen score, the parent computes it and passes it in on the row. The harness does not fit a model and does not train on labels.

3.9. `grok-4.5` proposes the next file under `harness/`. `grok-4.7` reviews that file before the parent scores it. Prior harnesses lost. That loss is why this contract allows combining frozen scores and billing fields inside `score_rows` and its helpers to chase a higher count out of 48.

A high score means resemblance to later fraud-type exclusions. It is not a finding that the firm committed fraud.

## 4. The loop

### 4.1 Who runs the loop

The executing parent session owns the loop. It does not call `run_loop`. It does not call `main()`. It does not run `python scripts/meta_harness.py`. `run_loop` scores every proposal and calls `should_keep` from `scripts/rank_evolve.py` internally at the point that sets parent and best; that keep is fitness-only (`list_fitness` is `top1_captured - 0.25 * extra_slice_rows`, and `should_keep` returns `child_fitness > parent_fitness and top1_slice <= rows * 0.02`). A fitness-only gain is already the next parent before the session can apply this plan's count-rise rule. Applying a stricter keep to stats returned by `run_loop`, without editing `scripts/meta_harness.py`, is unreachable. Nobody edits `scripts/meta_harness.py`.

The live search runs its own loop. The proposal count is 20 (`proposal_count=20` is the count, not a `run_loop` argument). A later `grok-4.7` reviewer may raise that count. It must not go below 20. The session imports scoring helpers from the existing scorekeeper and calls `score_source` itself. It does not replace the scorekeeper, does not rewrite its module-level defaults, and does not hand the scorekeeper source to the harness writer.

| Role | Model id | Job |
|---|---|---|
| Harness writer | `grok-4.5` | Proposes the next `harness/score_rows.py` and any helper under `harness/` |
| Harness reviewer | `grok-4.7` | Reviews that proposed file before the session scores it |
| Score API (no loop) | `score_source` / `slice_stats` in `scripts/meta_harness.py` | Returns `(fn, stats, fitness, error, scores)` for a source; session owns keep and parent |
| Scorekeeper file | `scripts/meta_harness.py` | Imported for `score_source` and helpers only; one 2024 score after the search stops; not started as a process |

API for both models: base URL `https://api.x.ai/v1`, key name `XAI_API_KEY`. Use those model ids. Do not use an alias. Do not print the key. Do not write the key into a file.

Free rein on the harness side: rewrite `harness/score_rows.py`, add helpers under `harness/`, combine frozen `tree_score` and `paper_score` with the eight billing fields, and use free tools the plan already accepted. Free rein stops at the scorekeeper. The harness writer does not receive the scorekeeper source, does not edit `scripts/meta_harness.py`, does not edit labels, does not edit `app/`, and does not replace saved model binaries. Do not hand `scripts/meta_harness.py` source to the harness writer. The executing session calls `score_source`. The harness writer does not.

On-disk defaults inside `scripts/meta_harness.py` are `SEARCH_YEARS = (2019, 2020, 2021, 2022)`, `SELECTION_YEAR = 2023`, `CONFIRM_YEAR = 2024`, `CLEAN_PER_FRAUD = 9`, `CONFIRM_CLEAN_PER = 5`, `PROPOSAL_COUNT = 12`, and `PROPOSER_MODEL = "grok-4.6"`. Those proposal defaults are not the live run. The live run is the session's own 20-proposal loop that calls `score_source`. Running `python scripts/meta_harness.py` under module defaults would still do 12 proposals on `grok-4.6` with fitness-only keeps inside `run_loop`. The executing session does not do that.

### 4.2 Selection file

Build the 2023 selection sample once before the seed score.

- Year: 2023 only.
- Undersample: 9 clean rows per fraud row, seed 1 (`scripts.train.SEED` is 1).
- Drop demo NPIs `1124725817` and `1639879034`.
- Label positive only when the exclusion year is after the billing year and `EXCLTYPE` is one of `1128a1`, `1128a3`, `1128b6`, or `1128b7`.

The parent attaches frozen `tree_score` (shallow XGBoost) and `paper_score` (page forest) to each row. Each harness row is the eight billing fields plus those two scores. Identifier fields stay out of the harness row and out of every proposer note. Search years 2019-2022 are not the keep file. Confirmation year 2024 is not used until the search stops.

### 4.3 Seed gate before proposal 1

Before proposal 1, the executing session calls `score_source` on the seed and the 2023 selection rows. It does not go through `run_loop`.

1. Read the current seed from `harness/score_rows.py`. The seed returns `paper_score` for each row.
2. Call `score_source(seed_source, select_rows, select_labels)`. That call returns `(fn, stats, fitness, error, scores)`. `stats` come from `slice_stats`. `slice_stats` keys include `top1_captured`, `top1_fraud`, `top5_captured`, `top5_fraud`, `top1_slice`, `rows`.
3. Record selection `top1_captured`, `top5_captured`, `top1_slice`, `rows`, and fitness. Existing `list_fitness` is `top1_captured - 0.25 * extra_slice_rows`. Fitness is recorded only as context. It is not this plan's keep rule.
4. If that `score_source` call errors, stop. Do not start proposal 1.
5. Only after a real seed score exists, open proposal 1. The seed source is the initial parent. Only a later kept source replaces it.

### 4.4 Call shape: twenty proposals without editing the parent

`scripts/meta_harness.py` stays on disk as written. Nobody edits it to flip `PROPOSAL_COUNT` or `PROPOSER_MODEL`. Nobody edits it to change keep behavior.

The executing session does not call `run_loop`. It does not call `main()`. It does not run `python scripts/meta_harness.py`. It runs its own loop of 20 proposals and calls `score_source` for every scored source. A later `grok-4.7` reviewer may raise the proposal count. It must not lower it below 20.

The on-disk default path inside the scorekeeper still uses `run_loop`, `should_keep`, and model `grok-4.6` when started as a script. The live plan does not use that path.

The loop runs exactly that many proposals. A rejected proposal counts toward 20. Do not stop after two quiet rounds. Do not stop early because nothing was kept. A rejected proposal, a review miss, a proposer exception, and a `score_source` error all append a record and continue. Errors become the next note. Continue until the proposal count is finished.

### 4.5 Proposer callable: grok-4.5 writes, grok-4.7 reviews, then score_source

The executing session's proposer callable owns the keep. It is not passed into `run_loop`. For each proposal step the callable:

1. Calls `grok-4.5` with the current kept parent source and the latest note. Asks for a full `score_rows(rows)` file and any `harness/` helper text the writer needs. Do not hand `scripts/meta_harness.py` source to this writer. Do not put 2024 labels in the writer prompt.
2. Calls `grok-4.7` on that file before any `score_source` call. The reviewer checks one `score_rows(rows)`, finite floats, no imports or file opens the scorekeeper rejects, no read of NPI, name, city, state, ZIP, or year, no 2024 labels, and no claim that the firm committed fraud.
3. When the review misses, the proposal still counts and the miss is the next note. The parent source does not change. Do not call `score_source` on a review miss. Same for a writer crash or a rate limit: surface the error, count the proposal, continue.
4. Only after `grok-4.7` passes does the callable call `score_source(proposed_source, select_rows, select_labels)`. That call is the parent score. Name `score_source` and `slice_stats`. The return is `(fn, stats, fitness, error, scores)`. Read keep inputs from `stats` (`top1_captured`, `top1_slice`, `rows`, and the other `slice_stats` keys as needed).
5. If `score_source` errors, the proposal counts and the error becomes the next note. The parent source does not change. Do not stop after two quiet rounds.

Do not put 2024 labels in the prompt that writes the harness. 2024 is scored once, after the search stops, by the session alone using parent helpers. Do not call `should_keep` for this plan's keep decision.

Client from the opened quickstart page, key name only:

```python
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv("XAI_API_KEY"),
    base_url="https://api.x.ai/v1",
)
```

### 4.6 Keep rule

After a reviewed source passes `grok-4.7`, the session calls `score_source(proposed_source, select_rows, select_labels)` on the 2023 selection file. `stats` come from `slice_stats`.

On disk, `should_keep(child_fitness, parent_fitness, child_stats)` returns `child_fitness > parent_fitness and top1_slice <= rows * 0.02`. `list_fitness` is `top1_captured - 0.25 * extra_slice_rows`. That is a fitness-only keep. It is not this plan's keep rule. `run_loop` calls `should_keep` internally when it sets parent and best. Because the live search does not call `run_loop`, that path never runs. Do not call `should_keep` for this decision.

This plan's keep rule:

- Keep only when the 2023 top 1 percent fraud count rises and the top 1 percent slice stays at most 2 percent of the selection rows.
- In `slice_stats` numbers, that is `int(child top1_captured) > int(parent top1_captured)` and `int(top1_slice) <= int(rows) * 0.02`.
- A fitness-only gain is not a keep.
- Do not call `should_keep` for this decision.

Only a kept source becomes the parent the next `grok-4.5` call sees. Only a kept source is eligible for the one 2024 score. If none are kept, the 2024 score uses the seed.

On keep, the new source becomes the parent for the next proposal, and the note lists the new selection stats plus missed selection fraud rows. On loss, reject, crash, `score_source` error, or review miss, the parent source stays as it was, the proposal still counts, and the note carries the loss, error, or review miss into the next step. A `score_source` error counts and becomes the next note. Do not stop after two quiet rounds.

2024 is not used in the keep decision. Nobody edits `scripts/meta_harness.py` or `scripts/rank_evolve.py`. The harness writer does not edit the parent to sneak a keep.

A high score means resemblance to later fraud-type exclusions. It is not a finding that the firm committed fraud.

### 4.7 Notes the writer sees

Every proposer note may include missed selection fraud rows. Each missed row shows only the eight billing fields plus `tree_score` and `paper_score`. No NPI, name, city, state, ZIP, or year. No 2024 labels.

Eight billing fields: Service count, Beneficiary count, Average charge, Average payment, Charge-to-payment ratio, Top-code share, Specialty, Growth.

### 4.8 Prior losses are facts to beat

- Prompt harness: 1/48 on the 288-row subsample.
- RankEvolve: kept none of 20, confirmed 3/48.

Those facts are why the loop exists. Do not stop because of them. When the proposal count finishes, the session writes the best kept harness (the seed if none kept), then runs the single 2024 confirmation score. The best kept harness is the last source this plan's count-rise rule kept. It is not `run_loop`'s `best`. A high score means resemblance to later fraud-type exclusions. It is not a finding that the firm committed fraud.

## 5. The one 2024 score

5.1. After the search loop stops, freeze the single harness that will be scored once. Use the best kept proposal from the loop. If none was kept, use the seed harness. Do not score 2024 during the loop. Score 2024 once, after the search stops.

5.2. Before that one score, have `grok-4.7` decide the 2024 evaluation set. Default is the full 2024 year. If `grok-4.7` writes that the machine cannot hold the full year, use the 288-row subsample already used by `models/harness_rank_note.txt`: every fraud row and 5 clean rows per fraud row, seed 1, 288 rows, 48 fraud rows. This planning session does not decide the machine cannot hold the full year. Say which set was scored.

5.3. The parent is `scripts/meta_harness.py`. The agent does not edit that file, the labels, `app/`, or the saved model binaries. Do not hand that evaluator to the harness writer.

On disk today, `main()` always loads a 2024 subsample via `load_sample((2024,), CONFIRM_CLEAN_PER=5)`, and `render_note` hard-codes the sentence "Confirmation is a 2024 subsample". It writes `confirm_top1=`, `same_rows_paper_top1=`, `same_rows_xgboost_top1=`, and `beats_paper_on_same_rows=`. It does not write `beats_current_best` and does not write a top 5 percent confirm line.

The executing session must still produce the fields this plan requires. It must not edit `scripts/meta_harness.py` to do that. After the session's own loop stops, it calls the existing scoring functions from the parent module — `score_source`, `slice_stats`, `paper_scores_for`, `tree_scores_for`, `harness_rows`, `compile_score_rows`, `run_harness` — on the best kept source (the seed if none was kept) and writes `models/meta_harness_note.txt` with the required fields. It does not call `run_loop` and does not use `loop["best"]`.

5.4. In `models/meta_harness_note.txt`, state which set was scored: full 2024 year, or the 288-row subsample. Record:

- `confirm_top1=` as a count out of 48
- the top 5 percent count out of 48
- the same-row count for the page forest
- the same-row count for the shallow tree
- `beats_current_best` as true or false

5.5. Same-row baselines. Do not refit. Do not re-estimate.

Full 2024 year, already scored: shallow XGBoost 11/48 and 18/48. Those 11/48 and 18/48 are not from `data/paper_scores/2024.csv`. Page forest 19/48 and 48/48, recounted from `data/paper_scores/2024.csv`. Optimized rank 20/48 and 48/48 in `models/optimized_note.txt`. That 20/48 is the current best. The page still loads `models/paper_forest.joblib`. On the full year, `beats_current_best` is true only when the new top 1 percent count is higher than 20/48.

Subsample: 288 rows, 48 fraud rows, 5 clean per fraud, seed 1. Prior marks for context only: prompt harness 1/48, shallow tree 3/48, RankEvolve seed 3/48. RankEvolve kept none of 20 proposals. `models/harness_rank_note.txt` says the paper forest was not scored on those rows. The same-row paper count on the subsample is computed at confirmation time. It is not the full-year 19/48. Do not invent a subsample paper count. When the note uses the subsample, `beats_current_best` is true only when the new count is higher than that same-row paper count.

5.6. Print this caveat in the note before any share, the sentence already in `scripts/harness_score.py`:

> 2024 has 48 fraud rows, below the published external-validation floor of 100 events, so shares are not a precise estimate.

Then write the share. The share is still the score the student asked for. Accuracy is not a score. The score is fraud rows caught in the top 1 percent out of 48. Also record the top 5 percent count out of 48.

5.7. State the meaning of the score in the note. A high score means resemblance to later fraud-type exclusions. It is not a finding that the firm committed fraud.

5.8. Treat the one 2024 score as the chase target for a count higher than 20/48 on the full year, or higher than the same-row paper count on the subsample. Prior harnesses lost. That loss is why this step exists. Do not conclude a higher count is impossible. Do not put 2024 labels in the prompt that writes the harness.

## 6. Files the later session may create, and files it must not replace

The later agent has free rein inside the harness codebase. It may rewrite `harness/score_rows.py` and any helper it creates under `harness/`. It may combine frozen scores, billing fields, and free tools it installs. It may call `grok-4.5` to propose the next file. It may call `grok-4.7` to review that file before the parent scores it. Free rein does not include the scorekeeper. `scripts/meta_harness.py` computes the 2023 keep decision and the one 2024 score. The agent does not edit that file, the labels, `app/`, or the saved model binaries.

### May create or rewrite

- `harness/score_rows.py`
- any helper created under `harness/`
- `models/meta_harness_note.txt`. The parent writes this. It records `confirm_top1=` as a count out of 48, the top 5 percent count out of 48, the same-row page-forest count, the same-row shallow-tree count, and `beats_current_best`
- a requirements line only if a free tool import fails and the opened page printed that pip line
- tests that cover the harness contract, not a second scorekeeper

### Must not replace or edit

- `scripts/meta_harness.py`
- `app/`
- `models/xgb_shallow.json`
- `models/paper_forest.joblib`
- `models/optimized_model.joblib`
- `data/training/UPDATED.csv` and other label files
- `data/paper_scores/2024.csv`
- evaluator scripts: `scripts/rank_evolve.py`, `scripts/harness_score.py`, `scripts/harness_rank.py`, `scripts/optimized_rank.py`
- Do not hand those evaluator files to the agent that writes `score_rows`.

## Measured facts

Copy these. Do not re-estimate.

- Workspace: `C:\Users\Jacob\Downloads\congressional app`. Windows. Python 3.14.4. The key name is `XAI_API_KEY`. Base URL `https://api.x.ai/v1`. Do not print the key. Do not write it into a file.
- Writer `grok-4.5` from https://docs.x.ai/developers/models/grok-4.5 opened 2026-10-22. Page printed Model name `grok-4.5`. Aliases printed: `grok-4.5-latest` and `grok-build-latest`. Do not use an alias.
- Reviewer `grok-4.7` from https://docs.x.ai/developers/models/grok-4.7.md opened 2026-10-22. Page printed Model name `grok-4.7`. No alias printed. Do not invent one.
- Eight billing fields: Service count, Beneficiary count, Average charge, Average payment, Charge-to-payment ratio, Top-code share, Specialty, Growth. NPI, name, city, state, ZIP, and year identify the row. They are not features.
- A row is positive only when the exclusion year is after the billing year and EXCLTYPE is `1128a1`, `1128a3`, `1128b6`, or `1128b7`. Demo NPIs `1124725817` and `1639879034` are dropped.
- Full 2024 year, already scored, do not refit: shallow XGBoost 11/48 and 18/48. Do not attribute 11/48 and 18/48 to `data/paper_scores/2024.csv`. Page forest 19/48 and 48/48, recounted from `data/paper_scores/2024.csv`. Optimized rank 20/48 and 48/48 in `models/optimized_note.txt`. That 20/48 is the current best. The page still loads `models/paper_forest.joblib`.
- Subsample, 288 rows, 48 fraud rows, 5 clean per fraud, seed 1: prompt harness 1/48, shallow tree 3/48. RankEvolve seed 3/48, kept none of 20 proposals, confirmed 3/48.
- 2024 has 48 fraud rows, below the 100-event floor. Print that caveat before the share: "2024 has 48 fraud rows, below the published external-validation floor of 100 events, so shares are not a precise estimate." The share is still the score the student asked for.
- Setup already on disk, not a finished run: `harness/score_rows.py` returns the page-forest score. `scripts/meta_harness.py` is the parent. `tests/test_meta_harness.py` passes. The live loop has not started. On disk the parent has `PROPOSAL_COUNT = 12` and `PROPOSER_MODEL = grok-4.6`. The plan's run uses 20 proposals in the session's own loop with writer `grok-4.5` and reviewer `grok-4.7`, calling `score_source` directly rather than `run_loop` call arguments, and not by editing the parent.

A high score means resemblance to later fraud-type exclusions. It is not a finding that the firm committed fraud.

The later parent writes `models/meta_harness_note.txt`. That note prints the 48-event caveat before the share. That note contains `confirm_top1=` as a count out of 48. That note contains the top 5 percent count out of 48. That note contains the same-row page-forest count and the same-row shallow-tree count. That note contains `beats_current_best`. `beats_current_best` is true only when the new count is higher than 20/48 on the full year, or higher than the same-row paper count when the subsample is used. Writer is `grok-4.5`. Reviewer is `grok-4.7`. A missing `confirm_top1=` line means the later run is not done. Do not stop because prior scores were 1/48 and 3/48.

Success line: confirm_top1= as a count out of 48
