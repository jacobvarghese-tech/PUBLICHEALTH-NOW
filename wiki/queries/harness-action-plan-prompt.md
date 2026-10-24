---
type: query
title: Harness action-plan prompt
updated: 2026-10-20
tags: [query, app, model, llm]
sources:
  - https://docs.x.ai/developers/quickstart
  - https://docs.x.ai/developers/models
  - https://docs.x.ai/developers/pricing
  - https://docs.x.ai/developers/rate-limits
  - https://dspy.ai/current/api/optimizers/GEPA/overview/
  - https://github.com/stanfordnlp/dspy/blob/main/docs/docs/learn/programming/language_models.md
  - https://github.com/gepa-ai/gepa
  - https://arxiv.org/abs/2507.19457
  - https://arxiv.org/abs/2610.14224
  - https://arxiv.org/abs/2610.26770
  - https://arxiv.org/abs/2609.05736
  - https://developers.openai.com/api/docs/guides/deep-research
  - models/holdout_note.txt
  - models/paper_forest_shares.json
---

# Harness action-plan prompt

## Question

What prompt should the deep-research run use so the report is an action plan that fully builds one labeled LLM scoring harness for Medicare Fraud Flagger, optimized by recursive self-improvement against about 1,270 fraud rows, calling xAI with the student's existing key?

## Answer

Twenty agents opened primary pages on prompt design, labeled optimizers, RSI harness papers, and the xAI docs. The laptop path that takes labels and an xAI key is a compiled DSPy program optimized by GEPA. Harness², HarnessPro, and PRISM are real RSI systems, and they do not take a labeled classification metric on this machine. The prompt below locks that finding and asks the next run to re-open the pages and write steps a later session can execute.

The stock `/deep-research` runner splits a query into at most four questions when breadth is left unset. Each question returns at most six claims. A second pass keeps a claim only when it can open the cited source and support the exact statement. A numbered checklist that is not itself a surviving claim gets dropped. Put the executable fact in the claim: the URL, the install line, the constructor argument, the output path, and the done-when line.

The prompt to pass as `args.query`:

```
I need an action plan a later session can execute to finish one LLM scoring harness for Medicare Fraud Flagger. Finish means a frozen language model, a typed scoring program, a metric that returns a score and text feedback, a train set and a validation set drawn from labeled provider-year rows, a GEPA compile, a saved program file that does not contain an API key, and one function that scores one row. The page and the saved tree files stay in place until that later session says otherwise.

The provider is xAI. The student already has an API key. Read it from the environment variable XAI_API_KEY. Never write the key into a file, a wiki page, a log, or a browser bundle. Base URL https://api.x.ai/v1. Auth header Authorization: Bearer $XAI_API_KEY. The quickstart model id is grok-4.7. Re-open https://docs.x.ai/developers/quickstart and https://docs.x.ai/developers/models before you put a model id, a price, or an install line into a step. If those pages have moved, your open wins.

How to split the work. This run plans at most four questions and verifies claims independently. Keep these four questions separate. Do not merge them. Each question may return at most six claims. A step that is not inside a surviving claim will be dropped, so each claim must carry the URL you opened, the file path to create or edit, and the done-when line.

1. Wire the key. Open https://docs.x.ai/developers/quickstart, https://docs.x.ai/developers/models, https://docs.x.ai/developers/pricing, and https://docs.x.ai/developers/rate-limits. Confirm the env var, the base URL, the auth header, the quickstart model id, and whether a short score call must stream. Confirm the Python install the quickstart shows for the OpenAI SDK and for the xAI SDK. Then open the DSPy language-model page that still documents an OpenAI-compatible endpoint, including https://github.com/stanfordnlp/dspy/blob/main/docs/docs/learn/programming/language_models.md. Confirm the constructor: dspy.LM with an openai/ prefix, api_key, and api_base. Confirm that DSPy docs do not name XAI_API_KEY, so the plan reads XAI_API_KEY and passes that value as api_key. Name one model id for the student program and one model id for the GEPA reflection LM. Use ids you read on the models page. Do not invent an id. A cheaper text model may be named only if that page lists it. Do not pick a voice, image, or video model.

2. Build the program. Open https://dspy.ai/current/getting-started/program-dont-prompt/, the DSPy metrics page, and the DSPy saving-and-loading page. Name the signature fields, the module class, the metric callable, and the save call. The signature inputs are the eight billing fields below. The output is a resemblance score in 0 to 1, plus a short reason. The metric takes gold, pred, trace, pred_name, and pred_trace, and returns a score plus feedback text. Open https://dspy.ai/current/api/optimizers/GEPA/overview/ and confirm that shape. The saved artifact path is models/harness_gepa.json. The page that says API keys are never serialized is the source for the done-when line that the key is absent from that file. Create scripts/harness_score.py. Do not edit scripts/train.py, models/xgb_shallow.json, models/xgb_expanded.json, models/paper_forest.joblib, app/, or data/rolled/.

3. Compile with GEPA. Open https://arxiv.org/abs/2507.19457, https://github.com/gepa-ai/gepa, and the DSPy GEPA getting-started page. Confirm pip install gepa, Python >=3.10 and <3.15, and that dspy.GEPA raises ImportError on Python 3.15 and later because gepa declares requires-python <3.15. This machine is Python 3.14.4, so name that bound in the install step. Confirm compile(student, trainset, valset), reflection_lm, and that exactly one of auto, max_full_evals, or max_metric_calls is set. The first compile uses max_metric_calls=150, the README example, not auto=heavy. Trainset and valset are separate. 2024 never enters either. Confirm the paper's smallest labeled train split and the warning that omitting valset reuses trainset and overfits. Subsample the 1,270 fraud rows. Do not put all 12,700 undersampled rows in the validation set. The claim must name the counts to write before compile: fraud rows in train, fraud rows in val, clean rows in each, and the seed.

4. Keep rule and what not to build. Open the 2024 holdout rule in the local notes named below, and open https://pmc.ncbi.nlm.nih.gov/articles/PMC4738418/ for the 100-event floor. The plan scores 2024 once, after compile, and writes the top 1 percent and top 5 percent shares beside the saved XGBoost shares. 48 events are below that floor, so the plan prints the caveat and does not treat the shares as a precise estimate. Also open https://arxiv.org/abs/2610.14224, https://arxiv.org/abs/2610.26770, and https://arxiv.org/abs/2609.05736. State in one claim each why Harness2, HarnessPro, and PRISM are not this build: label-free or tool-agent rollouts, and an install that is not a labeled scorer on this Windows laptop. A page switch stays a later decision.

Measured facts. Counted in this workspace. Use them. Do not re-estimate them.

- One row is one rendering NPI for one calendar year, rolled from Medicare Physician and Other Practitioners by Provider and Service.
- Signature inputs, in this order: Service count, Beneficiary count, Average charge, Average payment, Charge-to-payment ratio, Top-code share, Specialty, Growth. Specialty is a string such as Clinical Laboratory. Growth is this year's service count divided by the prior year's service count, minus 1, and is missing when there is no prior row or the prior service count is 0. Missing numbers stay missing. Name, NPI, city, state, ZIP, and Year identify the row. They are not signature inputs.
- A row is fraud only when its NPI matches a 10-digit NPI on the HHS OIG LEIE, EXCLTYPE is 1128a1, 1128a3, 1128b6, or 1128b7, and the year of EXCLDATE is after the billing year. Same-year and earlier exclusions are not positive.
- Counted 2019-2023 fraud rows: 1,270. Clean rows already undersampled at 9 per fraud, seed 1: 11,430. The paper-style forest counted 5,900 fraud rows on a different rollup. That larger count is not the GEPA trainset.
- Saved XGBoost, models/xgb_shallow.json, trained 2019-2023, 2024 held out. 2024: 11/48 in the top 1 percent, 18/48 in the top 5 percent.
- Paper-style forest, models/paper_forest.joblib, 2013-2023 train. Every training-year fraud row sat in that year's top 1 percent. 2024: 19/48 in the top 1 percent, 48/48 in the top 5 percent. That is the tree failure mode. Do not add another tree.
- 2023 has 93 current-rule fraud rows. 2024 has 48 fraud rows in about 1.21 million provider-years. Both counts are below the 100-event external-validation floor.
- Demo rows are not labels. Prince Laboratories, NPI 1124725817. Reliable Results Labs, NPI 1639879034. Neither is on the LEIE. Do not put them in trainset or valset.
- Machine: Windows, Python 3.14.4, about 16 GB RAM, workspace C:\Users\Jacob\Downloads\congressional app. xgboost 3.4.1, pandas, numpy, and scikit-learn 1.8.0 are already installed. Weka is not installed.
- PyPI pages opened on 2026-10-20: dspy 3.4.1 requires >=3.10,<3.16. gepa 0.1.4 requires >=3.10,<3.15. openai 3.35.1 requires >=3.10 and lists Python 3.14. xai-sdk 1.20.0 requires >=3.10. Re-open those pages before the install step. If the version moved, your open wins.

Prior opens, 2026-10-20. Re-open before you copy a line into a step. If your open disagrees, your open wins and the old line moves to Unverified.

- Quickstart: pip install openai, then OpenAI(api_key=..., base_url="https://api.x.ai/v1"), client.responses.create(model="grok-4.7", input=...), response.output_text. Streaming is opt-in. Chat Completions at POST /v1/chat/completions is legacy. Native SDK is pip install xai-sdk, Client(api_key=os.getenv("XAI_API_KEY")), chat.sample().content. GEPA and DSPy speak chat through LiteLLM, so the plan uses the OpenAI-compatible path, not the gRPC SDK, unless you open a DSPy page that accepts the xAI SDK.
- DSPy custom endpoint, from the GitHub language-models page: dspy.LM("openai/your-model-name", api_key="PROVIDER_API_KEY", api_base="YOUR_PROVIDER_URL"). Docs examples use api_base, not base_url. Nobody in the DSPy docs documents api.x.ai. Do not invent a second argument name.
- GEPA outside DSPy: pip install gepa, MIT, gepa.optimize(seed_candidate, trainset, task_lm, reflection_lm, max_metric_calls). A string task_lm does not take api_base. A custom base URL for the task model is a callable, or dspy.GEPA with a configured dspy.LM. Prefer dspy.GEPA so one LM object holds api_key and api_base.
- GEPA paper train sizes start at 45 labeled examples (AIME). HotpotQA used 150 train and 300 val. Docs say a huge valset spends the metric budget on scoring. First compile: at most 150 fraud rows in trainset and at most 50 fraud rows in valset, with clean rows sampled at 9 per fraud inside that subsample, seed 1. Write the counts. Do not use the full 1,270 as the validation set.
- Models page text prices per 1M tokens, short context: grok-4.7 is $2.00 input and $6.00 output. grok-4.3 is $1.25 input and $2.50 output. grok-4.20-0309-non-reasoning matches grok-4.3 and has reasoning off. grok-4.7 rate limit on the model page: 150 requests per second and 50,000,000 tokens per minute, which matches tier 0 on the rate-limits page. Batch API is 20 percent off for grok-4.7 and grok-4.3, and is not the first compile. Do not estimate a dollar bill.
- Harness2, https://github.com/google-research/harness2, Apache-2.0, label-free Propose-Probe-Compose, install documented for Linux and Python 3.12. Not this build.
- HarnessPro, https://github.com/pzs19/HarnessPro, MIT, label-free, public release is selected harness artifacts, not the RSI loop. Not this build.
- PRISM, paper https://arxiv.org/abs/2609.05736, code https://github.com/airbnb/agent-harness-optimizer, tool-agent rollouts on BFCL and tau2. The paper does not say a ranking metric can replace that benchmark. Not this build.
- TextGrad, https://github.com/zou-group/textgrad, can take an OpenAI-compatible client through ChatExternalClient. It optimizes text variables, not a compiled program with a saved DSPy artifact. Leave it out of the critical path unless a GEPA install fails on Python 3.14.
- MIPROv2 optimizes instructions and few-shots and wants a scalar metric. It is the comparison optimizer in the GEPA paper, not the first compile.
- OPRO official code is https://github.com/google-deepmind/opro. It has no api_base flag. Not this build.
- No opened paper replaces Bauder and Khoshgoftaar 2018 with an LLM on rolled Medicare rows and LEIE labels. GAO-26-107799 says CMS does not deny a claim from analytics alone, and that Medicare was not using generative AI to identify fraud. The score stays a resemblance flag.

Locks. If a source conflicts with one, put the conflict under Unverified and keep the lock.

- One harness. Do not add a second algorithm, a tree, or a comparison model to the page.
- Do not fit on 2024. Do not put 2024 rows in trainset or valset.
- Do not mark a row positive because of an exclusion in or before that billing year.
- The page must not say the firm committed fraud. A high score means the billing profile resembles providers later excluded for a fraud-type reason.
- Do not add city, state, ZIP, NPI, or name as signature inputs. Do not download beneficiary-level claims.
- Do not reopen the medically-unnecessary-test label hunt. Do not add Part D. DMEPOS stays a 2.0 item.
- Do not invent a district, a school, a home address, a parent email, or a 9-digit ZIP.
- Do not print the API key. Do not commit it.
- Do not tell the later session to stop before the saved program exists, unless the GEPA import fails on Python 3.14. If that import fails, the claim records the error and names the fallback you opened. It does not invent a package.

Output of this research run. Write the report as an action plan. Use these sections, in this order. Each step must also appear as a claim, or it will be dropped.

- Decision. One paragraph. The harness is a DSPy program compiled by GEPA against a frozen xAI model. Name the output file. Say the page and the tree files stay.
- Wire. The env var, the base URL, the model ids, the dspy.LM line, and the file that owns it. The key is read from the environment. The line in the report uses a placeholder, not a real key.
- Program. Signature fields, module, metric return shape, save path, score function.
- Splits. Train and val counts, seed, and the rule that 2024 is scored once after compile.
- Steps. Numbered. Each step names the script, the input files, the output file, the count to write, and the done-when line. One install step. One smoke-call step that prints a score for one rolled row and does not print the key. One compile step. One 2024 score step.
- Keep rule. The 2024 top 1 percent and top 5 percent shares, written beside 11/48 and 18/48, with the 100-event caveat.
- Leave out. Harness2, HarnessPro, PRISM, OPRO, and a new tree. One sentence each, with the URL.
- Unverified. A page you could not open, a model id you could not read, or a Python 3.14 import you did not run.
- Sources. The URL you opened, next to the question number it supports.

Leave open. Do not invent a preference on these unless a source makes them part of a step: whether the running page switches off the forest, whether to host the score function, which review budget a person can work, and whether a later compile may raise max_metric_calls above 150 after the first saved file exists.

Return verified facts only. A guessed model id or a guessed repository is a failed step.
```

Pass it with `args.breadth` set to 4.

## Citations

- Student request on 2026-10-20 to replace the ranking prompt with an action-plan prompt, after a 20-agent search of prompt-writing guides, harness optimizers, RSI papers, and xAI key wiring.
- [[harness RSI research prompt]]
- [[core idea]]
- [[model reliability]]
- https://docs.x.ai/developers/quickstart
- https://docs.x.ai/developers/models
- https://docs.x.ai/developers/pricing
- https://docs.x.ai/developers/rate-limits
- https://dspy.ai/current/api/optimizers/GEPA/overview/
- https://github.com/gepa-ai/gepa
- https://arxiv.org/abs/2507.19457
- https://arxiv.org/abs/2610.14224
- https://arxiv.org/abs/2610.26770
- https://arxiv.org/abs/2609.05736
- https://developers.openai.com/api/docs/guides/deep-research
- https://www.anthropic.com/research/multi-agent-research-system

## What this changes in the wiki

Filed the action-plan prompt. Marked [[harness RSI research prompt]] as superseded for the next run. Did not start `/deep-research`. Did not edit `scripts/`, `models/`, or `app/`. The one-model lock on [[scope]] stays until a later session executes the plan.
