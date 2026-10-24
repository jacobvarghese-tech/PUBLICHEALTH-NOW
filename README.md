# Medicare Fraud Flagger

Medicare Fraud Flagger is the app for this 2026 Congressional App Challenge entry. The page looks up a public billing row and scores it. A high score is a resemblance to providers later excluded for a fraud-type reason. It is not a finding that the firm committed fraud.

The Medicare year files and the saved ranker are not in git. `DATA.md` has the download command for each year and the folder for each file. A clone runs `py -3.14 -m unittest discover -s tests`. Tests that need a missing year or the model skip themselves. The page stops and names the missing files until those downloads are in place.

Contest notes for the agent are in `AGENTS.md`. The wiki catalog is `wiki/index.md`.

Karpathy's LLM Wiki idea file is imported at `raw/sources/karpathy-llm-wiki.md`. Do not edit files in `raw/`.
