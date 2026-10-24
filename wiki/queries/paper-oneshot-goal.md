---
type: query
title: Paper one-shot goal
updated: 2026-10-19
tags: [query, app, model]
sources:
  - wiki/concepts/paper-comparison.md
  - scripts/paper_oneshot.py
  - data/nppes/npi_sex.csv
  - data/nppes/column_map.txt
---

# Paper one-shot goal

## Question

What one `/goal` line runs the Bauder comparison fit tonight without touching the app model?

## Answer

Paste this as the whole prompt:

```
/goal Do the steps on wiki/concepts/paper-comparison.md by running python scripts/paper_oneshot.py. That script rolls 2013, then 2014, then 2015, then fits. A year whose data/paper_rolled file and count already exist is skipped. A partial download is resumed. If a download size disagrees with the expected byte count, stop and record both sizes. Write models/paper_replicate.json beside the paper cell 0.87302. Do not edit scripts/train.py, data/rolled/, app/, models/xgb_shallow.json, or models/xgb_expanded.json. A missing 2012 file is a recorded gap. Do not stop before the fit unless a byte count disagrees.
```

The runner is `scripts/paper_oneshot.py`. It calls `scripts/paper_roll_year.py` once per year, then `scripts/paper_fit.py`.

Already on disk:

- 2013 NBER header was opened. It contains `pgender` and `hcpcs_cd`. URL `http://data.nber.org/cms/providercharge/2013/phys2013.csv`. Expected bytes 2,590,718,145. A partial file may already sit at `data/raw/phys2013.csv.partial`. Resume it. Do not start a second download of that URL.
- 2014 CMS URL and expected bytes 2,905,565,005 are in the script.
- 2015 CMS URL and expected bytes 2,975,342,985 are in the script.
- Gender lookup for the CMS years is `data/nppes/npi_sex.csv`. Column on the physician file is filled from `Provider Sex Code`. Codes are M, F, and blank.
- Column map is `data/nppes/column_map.txt`.
- Labels come from the June 27, 2017 LEIE capture. The fit script downloads that capture if it is missing. Do not use `data/training/UPDATED.csv`.

The output is a comparison file. It does not replace the app model.

## Citations

- [[paper comparison]]
- Student request on 2026-10-19 to set up a one-shot goal for tonight.

## What this changes in the wiki

Filed the goal line and the runner. The 2013 download that had been started in this session was stopped so tonight's goal owns one run. The partial file was left in place.
