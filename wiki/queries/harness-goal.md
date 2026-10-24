---
type: query
title: Harness goal
updated: 2026-10-20
tags: [query, app, model, llm]
sources:
  - https://docs.x.ai/developers/quickstart
  - https://docs.x.ai/developers/models
  - https://docs.x.ai/developers/pricing
  - https://docs.x.ai/developers/rate-limits
  - https://dspy.ai/current/getting-started/program-dont-prompt/
  - https://dspy.ai/current/api/optimizers/GEPA/overview/
  - https://dspy.ai/current/getting-started/gepa-optimization/
  - https://dspy.ai/current/diving-deeper/saving-and-loading/
  - https://github.com/stanfordnlp/dspy/blob/main/docs/docs/learn/programming/language_models.md
  - https://pypi.org/project/gepa/
  - models/holdout_note.txt
  - models/paper_forest_note.txt
---

# Harness goal

## Question

What one `/goal` line finishes the labeled LLM scoring harness from [[harness action-plan prompt]] overnight, using only `XAI_API_KEY`?

## Answer

Paste this as the whole prompt in a new Grok CLI session. The session executes the plan. It does not start `/deep-research`.

```
/goal Finish one labeled LLM scoring harness for Medicare Fraud Flagger overnight. This session executes the deep-research action plan. It does not research a second algorithm.

Finish means all of these are true, and an independent check can open the files: scripts/harness_score.py exists; import gepa succeeds on this Python 3.14 interpreter; a non-streaming smoke call to grok-4.7 returns a score and a reason for one non-demo rolled row; models/harness_gepa.json exists; that JSON contains no API key; one function in the script scores one row from the eight billing fields.

Provider is xAI only. Read os.getenv("XAI_API_KEY") at request time. Send Authorization: Bearer from that value. Base URL https://api.x.ai/v1. If the env var is missing or empty, stop and say to set XAI_API_KEY. Do not invent a key. Do not write the key into a file, a wiki page, a log, stdout, stderr, a comment, or a browser bundle. A presence check may print only true or false.

Re-open these pages before you copy an install line or a model id. If an open disagrees on the install line or the model id, the open wins. Locks below stay.

- https://docs.x.ai/developers/quickstart
- https://docs.x.ai/developers/models
- https://docs.x.ai/developers/pricing
- https://docs.x.ai/developers/rate-limits
- https://dspy.ai/current/getting-started/program-dont-prompt/
- https://dspy.ai/current/api/optimizers/GEPA/overview/
- https://dspy.ai/current/getting-started/gepa-optimization/
- https://dspy.ai/current/diving-deeper/saving-and-loading/
- https://github.com/stanfordnlp/dspy/blob/main/docs/docs/learn/programming/language_models.md
- https://pypi.org/project/dspy/
- https://pypi.org/project/gepa/
- https://pypi.org/project/openai/

Then, on this Windows CPython 3.14 interpreter at C:\Users\Jacob\AppData\Local\Programs\Python\Python314\python.exe, install what those pages show for the OpenAI-compatible DSPy path. The prior open on 2026-10-20 was pip install openai, pip install dspy, pip install gepa. pip install xai-sdk only if the opened quickstart still shows it; DSPy talks through the OpenAI-compatible endpoint, not the gRPC SDK. Done when import gepa and import dspy both succeed. If import gepa fails on 3.14, record the real traceback and stop. Do not invent a fallback package.

Create only C:\Users\Jacob\Downloads\congressional app\scripts\harness_score.py. You may also write models/harness_gepa.json and models/harness_gepa_note.txt. You may import from scripts/train.py and scripts/join_labels.py. Do not edit scripts/train.py, scripts/join_labels.py, models/xgb_shallow.json, models/xgb_expanded.json, models/paper_forest.joblib, models/holdout_note.txt, app/, or data/rolled/.

Wire, after the opens. DSPy does not name XAI_API_KEY, so pass the env value as api_key. Docs examples use api_base, not base_url.

- Student LM: dspy.LM("openai/grok-4.7", api_key=os.getenv("XAI_API_KEY"), api_base="https://api.x.ai/v1")
- GEPA reflection LM: dspy.LM("openai/grok-4.3", api_key=os.getenv("XAI_API_KEY"), api_base="https://api.x.ai/v1")
- Omit stream=True.

Program. Signature inputs, in this order: Service count, Beneficiary count, Average charge, Average payment, Charge-to-payment ratio, Top-code share, Specialty, Growth. Specialty is a string such as Clinical Laboratory. Growth is this year's service count divided by the prior year's service count, minus 1, and is missing when there is no prior row or the prior service count is 0. Missing numbers stay missing. NPI, Name, City, State, ZIP, and Year identify the row. They are not signature inputs. Outputs: a resemblance score in 0 to 1, plus a short reason. Wrap that signature with dspy.Predict, or an equivalent Module that uses Predict. The metric callable is def metric(gold, pred, trace=None, pred_name=None, pred_trace=None) and returns a float or a dspy.Prediction / ScoreWithFeedback with score plus feedback text. Save with compiled_program.save("models/harness_gepa.json") as state-only JSON. Include one function that scores one row.

Splits. Draw train and val from the 2019-2023 pool. Load labeled rows with the existing join: a row is fraud only when its NPI matches a 10-digit NPI on data/training/UPDATED.csv, EXCLTYPE is 1128a1, 1128a3, 1128b6, or 1128b7, and the year of EXCLDATE is after the billing year. Same-year and earlier exclusions are not positive. Counted pool: 1,270 fraud rows and 11,430 clean rows already undersampled at 9 clean per fraud, seed 1. From that pool, with seed 1:

- trainset: 150 fraud, 1350 clean
- valset: 50 fraud, 450 clean

Pass a valset distinct from trainset. 2024 never enters either set. Demo NPIs 1124725817 and 1639879034 are in neither set. Write those four counts to stdout and to models/harness_gepa_note.txt before compile. Do not put all 1,270 fraud rows in the validation set.

Compile. dspy.GEPA with the configured reflection_lm, exactly one budget flag max_metric_calls=150 (not auto="heavy"), and compile(student, trainset=..., valset=...). Keep going until models/harness_gepa.json exists unless the GEPA import failed, the key is missing, or a page you opened shows the model id is gone. Retry on rate limits. Do not print the key on a retry.

Smoke-call before compile. One rolled provider-year row that is not a demo NPI. Print the score and the reason. Confirm the call used grok-4.7 and did not stream.

2024 after compile. 2024 is holdout, not fit. Implement the single-row scorer so a later pass can score 2024. Do not send about 1.21 million 2024 rows through the LM in this overnight run. That full pass is the review-budget item the research left open. Print the 100-event-floor caveat: 2024 has 48 fraud rows, below the published external-validation floor of 100 events, so shares are not a precise estimate. Record in models/harness_gepa_note.txt that the saved XGBoost figures to sit beside later are 11/48 top 1% and 18/48 top 5%, and the paper-style forest figures are 19/48 and 48/48. Do not write those numbers into models/xgb_shallow.json. Do not invent a 2024 numerator from a subsample and present it as the XGBoost comparison.

A high score means the billing profile resembles providers later excluded for a fraud-type reason. The script must not say the firm committed fraud.

Leave out. Do not add a second algorithm, a comparison optimizer, or another tree. Do not build Harness2 (https://arxiv.org/abs/2610.14224), HarnessPro (https://arxiv.org/abs/2610.26770), PRISM (https://arxiv.org/abs/2609.05736), or OPRO. Do not switch the running page off the forest. Do not host the score function. Do not raise max_metric_calls above 150. Do not download a CMS file. Do not download an LEIE file. Do not add city, state, ZIP, NPI, or name as signature inputs. Do not reopen the medically-unnecessary-test label hunt. Do not add Part D. Do not invent a district, a school, a home address, a parent email, or a 9-digit ZIP. Do not estimate a dollar bill.

Machine: Windows, Python 3.14.4, workspace C:\Users\Jacob\Downloads\congressional app. xgboost 3.4.1, pandas, numpy, and scikit-learn 1.8.0 are already installed.

Done when the JSON is present, the key is absent from the repo and from that JSON, the smoke call printed a score and a reason, and the note file records the split counts. Do not stop before the saved program exists unless the GEPA import failed or XAI_API_KEY is missing.
```

The runner is `scripts/harness_score.py`. The saved program is `models/harness_gepa.json`. The page model stays where it is.

Already on disk:

- Rolled provider-years at `data/rolled/`. Labels at `data/training/UPDATED.csv`.
- Load and label helpers in `scripts/train.py` and `scripts/join_labels.py`. Import them. Leave those files unchanged.
- Saved XGBoost holdout in `models/holdout_note.txt`: 11/48 and 18/48 on 2024.
- Paper-style forest note in `models/paper_forest_note.txt`: 19/48 and 48/48 on 2024. That saturation is why this goal does not add another tree.
- Demo NPIs `1124725817` and `1639879034` are not LEIE labels.

The overnight finish line is the saved program and the single-row scorer. A full 2024 LLM pass over about 1.21 million rows is the later budget item the research left open.

## Citations

- [[harness action-plan prompt]]
- [[harness RSI research prompt]]
- [[core idea]]
- [[scope]]
- Student request on 2026-10-20 for one `/goal` line that finishes the harness overnight on the xAI key only, matching the deep-research action-plan prompt.
- https://docs.x.ai/developers/quickstart
- https://dspy.ai/current/api/optimizers/GEPA/overview/
- https://arxiv.org/abs/2507.19457

## What this changes in the wiki

Filed the overnight goal line. Did not install a package, write `scripts/harness_score.py`, or edit `app/`. The page and the saved tree files stay until that goal runs.
