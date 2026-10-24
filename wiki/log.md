# Log

Append-only. Newest entries at the bottom. Prefix format: `## [YYYY-MM-DD] ingest|query|lint | Title`

## [2026-10-15] ingest | Karpathy LLM Wiki gist

Imported the idea file unchanged to `raw/sources/karpathy-llm-wiki.md` from https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f. Instantiated the pattern for this contest in `WIKI.md` and the Obsidian vault config. Did not edit the gist.

Pages: [[LLM Wiki pattern]], [[Karpathy LLM Wiki gist]].

## [2026-10-15] ingest | 2026 contest brief and rules PDF

Saved the official rules PDF to `raw/sources/2026-CAC-Rules.pdf`. Copied the 2026-10-15 agent brief to `raw/sources/contest-brief-2026-10-15.md` and left `AGENTS.md` as the operating schema, not a wiki page.

Seeded the wiki from those two sources. Open conflict: rules PDF says submit by 12:00 p.m. EDT on October 26, 2026. Registration page, as recorded in the brief, says 9:00 p.m. ET the same day. Planning deadline is noon.

Pages touched: [[overview]], [[index]], [[Congressional App Challenge]], [[Internet Education Foundation]], [[House of Representatives]], [[deadline]], [[eligibility]], [[submission]], [[judging]], [[prizes]], [[app idea]], [[2026 contest brief]], [[2026 CAC Rules PDF]], [[LLM Wiki pattern]].

District, member, team, and app concept are still unknown.

## [2026-10-15] query | Label gate and the ranking app

Finished the label hunt in `handoff-label-shortage.md` and shipped the unsupervised ranking because the gate failed.

DMEPOS referring-provider catheter codes A4351–A4353, 2021–2024, joined 22,550 NPIs to 3 fraud-type exclusions. The supplier file joined 2,225 NPIs to 0. Fifty-five skin-substitute Q codes joined 1,564 NPIs to 2. Those searches added 5 unique fraud-type NPIs, all billed before the exclusion year. Wayback snapshots recovered 282 fraud-type NPIs missing from the current file. They were not joined to billing rows. Named labs resolved in NPPES stayed off the positive list. Physician-file watched codes joined to 29 after the full 2022–2024 download. The gate needed 50.

## [2026-10-16] query | Firm-flagging handoff

The next build is the published LEIE join, not another unnecessary-test label hunt. Wrote `handoff-firm-flagging.md`. Paper baseline is 1,409 fraud provider-years for 2012–2015. The 2012–2024 estimate is about 4,600 fraud rows. The trained model does not exist yet. Pattern Check in `app/` remains the ranking page.

The app is Pattern Check in `app/`. For 81419 in 2024, Prince Laboratories ranks 1 of 48 and Reliable Results ranks 3 of 48. The page says a high score is an unusual pattern, not a fraud finding.

Pages touched: [[app idea]], [[overview]], [[index]].

## [2026-10-17] query | Core idea at the start of the build

Filed [[core idea]]. The idea to build is Medicare Fraud Flagger in `handoff-firm-flagging.md`. Pattern Check remains the description on [[app idea]] until the model exists. `app/` was not in the workspace on this date.

Pages touched: [[core idea]], [[app idea]], [[index]].

## [2026-10-17] query | How deep the build goes

Locked the contest depth on [[scope]]. The handoff's 2013–2024 window is cut to 2018–2024, train 2019–2023, hold out 2024. One untuned XGBoost model. Local search page. Stop under 200 train-window fraud rows. October 23 is the page deadline. Filed [[project scope]].

Pages touched: [[scope]], [[project scope]], [[overview]], [[app idea]], [[index]].

## [2026-10-17] query | Decisions before the action plan

Filed [[build decisions]]. Agents write the app. The student records the demo. Hosting is wanted and assumed to be AWS, so the local-only line on [[scope]] is open. Measured this machine: Python 3.14.4, 345.2 GB free, 15.8 GB RAM, no AWS CLI. Research workflow not started. Open: AWS account, public scores, the student's own code, district, and team.

Pages touched: [[build decisions]], [[scope]], [[overview]], [[index]].

## [2026-10-17] query | Second pass on the build decisions

The student said to finish the app and not plan around the AI-authorship rule. Submission may not happen. The deadline stays as motivation. They do not have AWS credits yet. The page they want is a dashboard that asks for the XGBoost features and browses past years. Updated [[build decisions]] and [[scope]]. Research still not started.

Pages touched: [[build decisions]], [[scope]], [[log]].

## [2026-10-17] query | Page layout and years closed

The student chose both parts equally on one screen, and years 2018–2024. Updated [[build decisions]] and [[scope]]. Starting the deep-research workflow for the action plan.

Pages touched: [[build decisions]], [[scope]].

## [2026-10-17] query | Action-plan research prompt

Stopped the first deep-research run. It was still on a draft query. Filed [[action-plan prompt]] and started a new run with that prompt. The standing checklist will be `wiki/concepts/action-plan.md` after the report returns.

Pages touched: [[action-plan prompt]], [[index]].

## [2026-10-17] ingest | Action-plan research report

`deep-research-2` finished Partial after about 3 hours. 24 claims went to verification. The report body failed citation validation, so the standing checklist uses the deterministic finding list. Filed [[action plan]] with nine steps, the year CSV URLs, the LEIE columns, the column contract, and the unverified checks. Critical path ends at the local page. Hosting stays off it.

Pages touched: [[action plan]], [[index]].

## [2026-10-17] query | Is the app viable

Filed [[app viable]]. The build is viable on this laptop if each year is rolled in chunks. The score is a review flag. Held-out capture is unknown until training.

Pages touched: [[app viable]], [[index]].

## [2026-10-17] query | Can it be a good flag and database

Filed [[good flag]]. The browser over the official files can be a good database. The score can rank a name you already have. A national top-flags list stays mostly clean because exclusions are rare. The 2018 paper's best AUC was about 0.873, which is a comparison point, not a promise for this model.

Pages touched: [[good flag]], [[index]].

## [2026-10-17] query | Is XGBoost still viable

Filed [[xgboost viable]]. One shallow XGBoost model remains the locked model. The wheel exists for Python 3.14. The 2018 paper's best learner was a random forest at about 0.873, which stays a comparison point.

Pages touched: [[xgboost viable]], [[index]].

## [2026-10-17] query | Will the plan hit the goal

Filed [[plan audit]]. HEAD-checked the 2018, 2023, and 2024 CSVs. The 2024 file is 3,250,282,192 bytes and the header starts with Rndrng_NPI. Counted the live LEIE: 32,790 fraud-type rows, 4,296 with a usable NPI. Both demo labs are in the current CMS release and absent from the LEIE. The 200-row stop is unlikely. The exact overlap waits on the join.

Pages touched: [[plan audit]], [[index]].

## [2026-10-17] note | Development starts at step 1

The student asked how development starts and how the phases work. No code was written. The next action is step 1 of [[action plan]]: a venv and `xgboost` plus `pandas`. Years run one at a time through steps 3 and 4. Step 5 is the stop gate. Step 8 stays off the path.

## [2026-10-17] note | How to start a phase

The start line for step 1 is now on [[action plan]]. A phase name alone is not a goal. The line has to include the done-when check.

## [2026-10-17] note | Phase 2 start line

Added the `/goal` line for step 2 on [[action plan]]. It waits until step 1 imports. It does not download a billing year.

## [2026-10-17] note | Phase 3 start line

Added the `/goal` line for steps 3 and 4 on [[action plan]]. It covers 2018 only. The check includes the rollup and the raw-file delete, because step 3's own done-when line requires the raw CSV to be gone.

## [2026-10-17] note | Year count

The download loop is seven years, 2018 through 2024. 2018 is the growth baseline. Train on 2019–2023. Hold out 2024.

## [2026-10-17] note | One goal for the seven years

Replaced the 2018-only start line with one `/goal` that walks 2018 through 2024 in order. A `/loop` is the wrong tool, because the next tick would start a second download.

## [2026-10-17] note | One goal versus seven prompts

One goal walks the years and reuses the first script. Seven sequential goals stop a bad rollup at one year. Seven goals at once would download every year together. Prefer 2018 alone, then one goal for the rest.

## [2026-10-17] note | 2018 start line

Added the 2018-only `/goal` line on [[action plan]]. The seven-year line stays for after that file looks right.

## [2026-10-17] note | 2018 check

`data/rolled/2018.csv` has 1,061,278 data rows, the 14 contract columns, and 166,982,995 bytes. The note matches. `data/raw/` is empty. The source-row count was not re-read from CMS.

## [2026-10-17] note | 2019 start line

Added the 2019 `/goal` line on [[action plan]]. `scripts/download_year.py` is hard-coded to 2018, so the line tells the next session to take the year as an argument and to fill Growth from the 2018 rolled file.

## [2026-10-17] note | 2019 check

`data/rolled/2019.csv` has 1,093,367 rows, no duplicate NPIs, and the 14 contract columns. Growth matches the formula on all 981,474 rows that also appear in 2018 with a non-zero service count. 111,893 rows have no 2018 match and Growth is blank. The 2018 file was unchanged. `data/raw/` is empty.

## [2026-10-17] note | 2020 start line

Added the 2020 `/goal` line on [[action plan]]. The script already takes `--year`, `--url`, and `--bytes`. Growth comes from the 2019 rolled file.

## [2026-10-17] note | 2020 check

`data/rolled/2020.csv` has 1,085,313 rows, no duplicate NPIs, and the 14 contract columns. Growth matches the formula on all 986,846 rows that also appear in 2019 with a non-zero service count. 98,467 rows have no 2019 match and Growth is blank. The 2018 and 2019 files were unchanged. `data/raw/` is empty.

## [2026-10-17] note | 2021 start line

Added the 2021 `/goal` line on [[action plan]]. Growth comes from the 2020 rolled file.

## [2026-10-17] note | 2021 check

`data/rolled/2021.csv` has 1,123,589 rows, no duplicate NPIs, and the 14 contract columns. Growth matches the formula on all 996,091 rows that also appear in 2020 with a non-zero service count. 127,498 rows have no 2020 match and Growth is blank. The 2018, 2019, and 2020 files were unchanged. `data/raw/` is empty.

## [2026-10-17] note | Remaining years start line

Added one `/goal` line for 2022, then 2023, then 2024 on [[action plan]]. Each year fills Growth from the year before it. The four finished files stay untouched.

## [2026-10-17] note | Years done, join is next

All seven rolled files are in `data/rolled/`. `data/training/` still has only the LEIE file and the raw fraud-row count. No join script exists. The next start line is step 5 on [[action plan]].

## [2026-10-17] note | Join cleared, train is next

`data/training/fraud_provider_year_count.txt` says 1270. That is above the 200 stop. The next start line is step 6 on [[action plan]]. No model file exists yet.

## [2026-10-17] note | Step 6 check

`models/xgb_shallow.json` loads with the eight locked features, depth 4, and 100 trees. Training sample is 1270 fraud and 11430 clean. 2024 holdout capture is 11/48 in the top 1% and 18/48 in the top 5%. The exclusion file runs through 2026, so those 48 labels are possible. Rolled files were unchanged.

## [2026-10-17] note | Page is next

Step 6 is checked. `app/` still holds the Pattern Check page. The next start line is step 7 on [[action plan]]. It replaces that page and scores the two demo NPIs.

## [2026-10-17] note | Step 7 check

`python app/server.py` served Medicare Fraud Flagger on `http://127.0.0.1:8765/` and again on `http://127.0.0.1:8766/`. Both boots printed a listening URL. The page is one screen: the eight-feature form and the 2018-2024 browser. Search by name, city, and NPI filled the same row. The Deerfield Beach pin reopened NPI `1124725817`. A blank Growth field stayed blank and the score said the row was incomplete. NPI `1124725817` is 2024 percentile 99.988902 (1207339/1207473), inside the top 5%. NPI `1639879034` is 2024 percentile 99.945258 (1206812/1207473), inside the top 5%. The about page names Grok, the CMS files, the LEIE, XGBoost, and Leaflet, and states training years 2019-2023, 1270 fraud rows, and the 11/48 and 18/48 holdout shares. No done-when line failed. `data/rolled/`, `scripts/`, and `models/` were unchanged.

## [2026-10-18] query | Model reliability research prompt

The student asked for a deep-research prompt to make the trained XGBoost model more reliable. Filed [[model reliability prompt]]. The prompt takes the current fit as given: depth 4, 1270 fraud rows, real-mix 475/1270 and 918/1270, 2024 holdout 11/48 and 18/48. It asks for a diagnosis, ranked single-owner changes, and a leave-alone list. It does not reopen a second model, a grid search, or the unnecessary-test hunt. The standing note will be `wiki/concepts/model-reliability.md` after a report returns. No model file was changed.

Pages touched: [[model reliability prompt]], [[index]].

## [2026-10-18] query | Reliability apply prompt

The student asked for a coding prompt based on the reliability research. The run finished Partial: 19 of 22 claims kept, one ranked change, no booster or feature change. Filed [[reliability apply prompt]]. The prompt runs the four on-disk diagnosis checks, tabulates EXCLTYPE, then prints the 100-event caveat beside the stored 11/48 and 18/48 on the about page. It forbids a refit, a second model, a grid, an interval for 11/48, and a new exclusion list. The standing note is still unwritten. No model file was changed.

Pages touched: [[reliability apply prompt]], [[index]].

## [2026-10-18] query | Retrain research prompt

The student is willing to retrain and asked for a deep-research prompt. Filed [[retrain research prompt]]. The prompt asks for one keep-or-replace decision. It gives the measured 48-row ranks, the two-year label window, and the 1-in-1,100 review list as facts. It splits the evidence into label timing, rare-event validation, feature grain, and decision threshold so the four researchers do not open the same papers. It leaves a second algorithm, a grid, and a new dataset open. No model file was changed.

Pages touched: [[retrain research prompt]], [[index]].

## [2026-10-18] query | Reliability checklist applied

Ran the four diagnosis checks and the EXCLTYPE table on the files already on disk. The saved fit matched: depth 4, 100 trees, eight features, training sample 1270 and 11430, real mix 475/1270 and 918/1270, holdout 11/48 and 18/48. Memorization was not established. The 2024 fraud-row count is 48, below the Collins, Ogundimu, and Altman floor of at least 100 events. The label rule is the same four codes and the same after-the-billing-year rule in both windows. Mandatory versus permissive mix is 1169/101 in 2019–2023 and 46/2 in 2024, so the mixed-class cause was killed.

Applied the one page change. `app/about.html` still prints 11/48 and 18/48 and now says those 48 rows are below the 100-event floor, so the two shares are not a precise estimate. `python app/server.py` on port 8767 served that sentence. `python -m unittest tests.test_page tests.test_train` passed, 16 tests. SHA-256 of `models/xgb_shallow.json` was `5A215FB6D4995C59AF0528C9427D3B29A430E6AE5B3D1893262572357D8D5531` before and after. `data/rolled/` was not edited. Filed [[model reliability]].

Pages touched: [[model reliability]], [[index]], [[log]].

## [2026-10-18] query | Full retrain action-plan prompt

The student asked for a deep-research prompt that sets up an action plan for a full retrain. Disk size and the contest clock are not constraints. A new model is allowed. Filed [[full retrain action-plan prompt]]. The prompt asks for ordered steps, exact CSV URLs, a stop-and-count rule, and a keep rule. Evidence targets are 2013-2017 physician files, both DMEPOS files, the LEIE archive, and the holdout readout. Wayback extras and the year-by-year fraud counts are facts in the prompt. DOJ, FCA, and CIA names stay off the positive class. No model file was changed.

Pages touched: [[full retrain action-plan prompt]], [[index]], [[log]].

## [2026-10-18] query | Expanded retrain action-plan prompt

The student asked for a research prompt that plans one new model on the piles left out of the 2019–2023 fit, and that uses at least 12 agents. Filed [[expanded retrain action-plan prompt]]. The 12 questions are one physician year each for 2013–2017, referring DMEPOS, supplier DMEPOS, recovered exclusions, monthly supplements, no-NPI matching, fit settings, and the holdout lock. The stock `/deep-research` runner caps the split at 6 and ignores a breadth outside 2–6, so this prompt is not a `/deep-research` call. No model file was changed.

Pages touched: [[expanded retrain action-plan prompt]], [[index]], [[log]].

## [2026-10-19] query | Paper replication action-plan prompt

The student asked for a deep-research prompt whose report is an action plan to replicate the Bauder and Khoshgoftaar 2018 model. Filed [[paper replicate prompt]]. The four questions are the paper method, the source files, the rebuild steps, and the score comparison. The replica would be `models/paper_replicate.json`. Both saved model files stay in place. No model file was changed. The research run was not started.

## [2026-10-19] query | Closest paper-model action-plan prompt

The student asked for a high-quality deep-research prompt whose report is an action plan to develop a model as close as possible to the paper. Filed [[closest paper-model prompt]]. The four questions are the paper method, the closest public file for each year, the rebuild steps, and the score comparison. A missing original file is a recorded gap, and the plan still fits. The replica would be `models/paper_replicate.json`. Both saved model files stay in place. No model file was changed. The research run was not started.

Pages touched: [[closest paper-model prompt]], [[index]], [[log]].

## [2026-10-19] query | Closest paper-model research result

The `deep-research` run on [[closest paper-model prompt]] finished Partial. Filed [[paper comparison]]. The learner to score is RF100 at the 90:10 mix, beside the paper cell 0.87302. The output path is `models/paper_replicate.json`. Both saved XGBoost files stay. `scripts/train.py`, `data/rolled/`, and `app/` stay unedited.

The run did not open the live PMC PDF. The method and the score table rest on `raw/sources/pmc_extract.txt`. No 2012 data URL was opened, so that year is a recorded skip. 2014 and 2015 have CMS URLs. Gender on those files comes from a later NPPES snapshot. Labels come from the June 27, 2017 LEIE capture, not today's `UPDATED.csv`. Indefinite 1128(c)(3)(g)(ii) has no numeric length in the extract, so those rows stay out of the fraud class. No model file was changed.

Pages touched: [[paper comparison]], [[index]], [[log]].

## [2026-10-19] query | Paper-holes research prompt

The student asked for a deep-research prompt that plugs the holes in the comparison plan, using at least 12 agents at once. Filed [[paper-holes research prompt]]. The stock `/deep-research` runner still caps the split at 6, so the 12 holes live in `.grok/workflows/paper-holes.rhai`. A smoke check passed. No research run was started. No script or model file was edited.

Pages touched: [[paper-holes research prompt]], [[index]], [[log]].

## [2026-10-19] data | Gender lookup and column map

The student asked to run the gender and column fix. Downloaded the October 12, 2026 NPPES ZIP, 1,159,720,219 bytes, to `data/nppes/`. The inner header names the sex field `Provider Sex Code`. `scripts/nppes_gender.py` wrote `data/nppes/npi_sex.csv`: 9,852,180 NPIs, 2,298,983 M, 5,159,668 F, 2,340,086 blank. Codes other than M and F were blanked. The five paper numeric names map to `Tot_Srvcs`, `Tot_Benes`, `Tot_Bene_Day_Srvcs`, `Avg_Sbmtd_Chrg`, and `Avg_Mdcr_Pymt_Amt` on the 2013–2015 headers already on disk. The map is `data/nppes/column_map.txt`. No physician CSV was downloaded. `models/`, `scripts/train.py`, `data/rolled/`, and `app/` were not edited.

Pages touched: [[paper comparison]], [[log]].

## [2026-10-19] data | Overnight paper comparison fit started

The student asked to one-shot the comparison model overnight. This fit writes `models/paper_replicate.json`. It does not replace `models/xgb_shallow.json`. The 2013 NBER header was opened and contains `pgender` and `hcpcs_cd`. Expected bytes 2,590,718,145. A download of that year was started, then stopped so tonight's goal owns one run. The partial file remains at `data/raw/phys2013.csv.partial`.

## [2026-10-19] query | Paper one-shot goal

The student asked to set up a one-shot goal prompt for tonight. Filed [[paper one-shot goal]]. The runner is `scripts/paper_oneshot.py`. It resumes a partial download, skips a year already rolled, and stops on a byte-count mismatch. The prompt is also the start line on [[paper comparison]].

Pages touched: [[paper one-shot goal]], [[paper comparison]], [[index]], [[log]].

## [2026-10-20] query | Paper forest app goal

The student asked for a `/goal` line that makes the paper forest usable in place of the XGBoost model. Filed [[paper forest app goal]]. The line rolls 2016 through 2024 into `data/paper_rolled/`, keeps name, city, state, and ZIP, fits on 2013–2023 with the app label rule, holds out 2024, and points `app/server.py` at `models/paper_forest.joblib`. Search for 2018–2024 must return a percentile. The two demo NPIs stay on the page. `models/xgb_shallow.json`, `models/xgb_expanded.json`, `models/paper_replicate.json`, `scripts/train.py`, and `data/rolled/` stay unchanged. No year was downloaded. No model file was edited.

Pages touched: [[paper forest app goal]], [[index]], [[log]].

## [2026-10-20] query | Undersampling action-plan prompt

The student asked for a deep-research prompt that turns the paper's random undersampling into an action plan. Filed [[undersampling action-plan prompt]]. The plan is for a second forest at the paper's best class mix, scored on the real 2024 list. The page forest stays in place until that comparison says otherwise. No fit was run.

Pages touched: [[undersampling action-plan prompt]], [[index]], [[log]].

## [2026-10-20] ingest | Undersample research report

`deep-research` finished Partial after 22 minutes. The paper sampling, the Table 5 scores, and the keep rule survived. The numbered fit checklist did not, because no surviving claim named a script, an input path, an output path, and a count together. Filed [[undersample plan]] with three steps rebuilt from the surviving findings and files already on disk. The mix is 90:10. The second forest goes to `models/paper_forest_rus.joblib`. `models/paper_forest.joblib` stays. The page 11 sentence that names "99:10 and 99:5" as the best RF100 mixes disagrees with Table 5 and stays unverified. No fit was run.

Pages touched: [[undersample plan]], [[index]], [[log]].

## [2026-10-20] query | Undersample goal

The student asked for one `/goal` line that spins up about 20 agents and finishes the second forest. Filed [[undersample goal]]. Eleven agents label one training year each, seven check 2018–2024 features, one writes the script, and one fits after the counts exist. The user config caps concurrent subagents at 4, so the prompt tells the session to raise that cap to 20 before the first spawn. No agent was spawned. No model was fit.

Pages touched: [[undersample goal]], [[undersample plan]], [[index]], [[log]].

## [2026-10-20] query | Leaf-size action-plan prompt

The student asked for a research prompt that turns one score-tie fix into an action plan. The fix is stopping a leaf once it holds 50 rows, and once it holds 100 rows, so a mixed leaf can vote a fraction. Filed [[leaf-size action-plan prompt]]. The plan is two comparison forests, scored on the real 2024 list. More labels, undersampling, and a page switch are outside the plan. The page forest stays in place until that comparison says otherwise. No fit was run.

Pages touched: [[leaf-size action-plan prompt]], [[index]], [[log]].

## [2026-10-20] query | Tie-break action-plan prompt

The student asked for a deep-research prompt that turns the third score-tie option into an action plan. The forest stays. When two scores match, the list a person reads sorts by how unusual the charge is for that specialty. Filed [[tie-break action-plan prompt]]. The page does not show a national ranked list today, so the plan writes one. A page change stays a later decision. No model was fit.

Pages touched: [[tie-break action-plan prompt]], [[index]], [[log]].

## [2026-10-20] ingest | Leaf-size plan

Opened sklearn 1.8.0 RandomForestClassifier and DecisionTreeClassifier. The leaf stop is `min_samples_leaf`, default 1. A mixed leaf votes the class fraction. `min_samples_split` is a different stop and stays at 2. Filed [[leaf-size plan]] with five steps: label, fit 50, fit 100, score 2018–2024, write the 2024 comparison. Output files are `models/paper_forest_leaf50.joblib` and `models/paper_forest_leaf100.joblib`. `models/paper_forest.joblib` stays. The 5,900 vs 5,901 fraud-count gap stays a gap. No fit was run.

Pages touched: [[leaf-size plan]], [[index]], [[log]].

## [2026-10-20] ingest | Leaf-size research report

`deep-research` finished Partial after 15 minutes. The leaf-stop name (`min_samples_leaf`, default 1), the `predict_proba` fraction vote, and the keep rule survived. Fit-step claims named output paths and the 5,900 mix from the page-forest note. The compile pass already had [[leaf-size plan]]; it was updated with the Partial findings: `.predict()` majority class is a different call from the page score, and the prompt's 2013–2015 grouped counts disagree with the on-disk `.count.txt` files. No fit was run.

Pages touched: [[leaf-size plan]], [[log]].

## [2026-10-20] query | Harness RSI research prompt

The student asked for a deep-research prompt that uses an LLM to find the four best public harnesses that allow harness optimization, given about 1,200 labeled fraud rows, for RSI optimization of Medicare Fraud Flagger. Tree models on disk are the reason: XGBoost 11/48 and 18/48 on 2024, expanded 8/48, paper forest 19/48 top 1 percent after 100 percent capture on every training year. Filed [[harness RSI research prompt]]. Four questions: labeled optimizers, RSI full-harness search, rare-event ranking fit, runnable four. Breadth 4. The page and the saved tree files stay. No research run was started. No model file was changed.

Pages touched: [[harness RSI research prompt]], [[index]], [[log]].

## [2026-10-20] query | Harness action-plan prompt

The student asked to shift the ranking prompt into a deep-research action plan that finishes the harness, and to search first with about 20 agents. Twenty agents opened prompt-writing guides, DSPy, GEPA, MIPROv2, OPRO, TextGrad, Harness2, HarnessPro, PRISM, other optimizers, and the xAI docs. The laptop path that takes the 1,270 labels and an XAI_API_KEY is a DSPy program compiled by GEPA against https://api.x.ai/v1. Harness2, HarnessPro, and PRISM stay out of the critical path because they are label-free or tool-agent loops. Filed [[harness action-plan prompt]]. Marked [[harness RSI research prompt]] as superseded for the next run. No research run was started. No model file was changed. The key was not written down.

Pages touched: [[harness action-plan prompt]], [[harness RSI research prompt]], [[index]], [[log]].

## [2026-10-20] query | Harness goal

The student asked for one overnight `/goal` prompt that finishes the labeled LLM scoring harness, using only `XAI_API_KEY`, and matching [[harness action-plan prompt]]. Filed [[harness goal]]. The session that runs it creates `scripts/harness_score.py` and `models/harness_gepa.json`, reads the key from the environment, and leaves the page and the tree files in place. A full 2024 LLM pass stays the later budget item. No install was run. The key was not written down.

Pages touched: [[harness goal]], [[index]], [[log]].

## [2026-10-21] query | Three harness plans prompt

The student asked for a deep-research prompt that writes three separate overnight action plans, one per harness type, each a train-grade-improve loop, with at least 16 agents. The stock `/deep-research` runner caps the split at 6, so the runner is `.grok/workflows/three-harness-plans.rhai`. A smoke check passed. It used canned host results and did not open a page. The 16 questions cover year-holdout, feature-code search, and the label-lag score, plus shared locks. The later coding night is a different session and also uses at least 16 subagents. No research run was started. No model file was changed. The page model stays.

Pages touched: [[three harness plans prompt]], [[index]], [[log]].

## [2026-10-22] query | Three harness plans

The stock `deep-research` run finished Partial and did not write the three plans. Filed [[three harness plans]] from the findings that survived and from the files on disk. Plan A is `scripts/harness_year.py`. Plan B is `scripts/harness_features.py`. Plan C is `scripts/harness_lag.py`. Each grades years before 2024, stops after two years with no gain, and scores 2024 once after the stop. No model was fit. `app/` was not edited. The page model stays.

Pages touched: [[three harness plans]], [[index]], [[log]].

## [2026-10-22] query | Harness pick

The student asked which self-optimizing harness fits the app, the xAI key, and the control trials. Filed [[harness pick]]. The pick is `optimize_anything` with the GEPA engine. Student model `grok-4.20-0309-non-reasoning`. Reflection model `grok-4.3`. Search years 2019–2022. Selection year 2023. Confirmation year 2024, scored once. The search metric is the selection-trial top 1 percent fraud count, not the one-row metric in `scripts/harness_score.py`. No compile was started. `app/` was not edited.

Pages touched: [[harness pick]], [[harness pick query]], [[index]], [[log]].

## [2026-10-22] query | Harness one-shot

The student asked for a one-shot that leaves a score by morning. Started `scripts/harness_rank.py`. Search is 12 fraud rows from 2019–2022. Selection inside GEPA is 8 fraud rows from 2023. After the stop, the script ranks 2023 and then scores a 2024 subsample. The morning file is `models/harness_rank_note.txt`. The page model stays.

Pages touched: [[harness one-shot]], [[index]], [[log]].

## [2026-10-22] query | RankEvolve plan

The student asked for an action plan for a RankEvolve-style scorer before school. Filed [[rankevolve plan]]. The candidate is a capped Python function on top of the frozen shallow score. Search is 2019–2022. Selection is 2023. Confirmation is the same 2024 subsample the prompt harness lost, scored once. No script was started. `app/` was not edited.

Pages touched: [[rankevolve plan]], [[rankevolve plan query]], [[index]], [[log]].

## [2026-10-22] query | Meta harness action-plan prompt

The student asked for a prompt that gets an action plan for the meta-harness run, with grok-4.5 as the writer and grok-4.7 as the reviewer, about 20 agents, free tools installed, and free rein inside the harness codebase. Deep research is the wrong runner. Filed [[meta harness action-plan prompt]]. The line is a `/goal`. It does not start the live loop and it does not conclude that the run would fail. No model was fit. `app/` was not edited.

Pages touched: [[meta harness action-plan prompt]], [[index]], [[log]].

## [2026-10-22] query | Label islands goal

The student asked for a prompt for the label loop, the second option outside the harness loop and the forest loop. Filed [[label islands goal]]. The line is a `/goal`. Training labels may change. The 2024 numerator stays on the four app codes. Spec 22 stays frozen. No fit was started. `app/` was not edited.

Pages touched: [[label islands goal]], [[index]], [[log]].

