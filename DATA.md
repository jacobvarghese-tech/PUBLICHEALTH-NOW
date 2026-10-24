# How to get the data

A fresh clone has the page, the scoring code, and this note. It does not have the Medicare files or the saved ranker. Those files are public or too large for git. A full CMS year is about 3 GB. The saved ranker is 414 MB.

`py -3.14 app/server.py` stops and names the missing paths until those files are in place. The unit tests under `tests/` that build their own small tables do not need the downloads.

Do not commit the CSVs or the `.joblib` file.

A high score means a billing row resembles providers who were later excluded for a fraud-type reason. It is not a finding that the firm committed fraud.

## What the app needs

The page reads one row per provider per year from `data/paper_rolled/`. Years on the page are 2018 through 2024. The first launch builds `app/data/search.sqlite` from those files. That index is about 4 GB and can be deleted. The server rebuilds it.

| Path | What it is |
|---|---|
| `data/paper_rolled/2018.csv` through `2024.csv` | One row per rendering NPI for that year. The page searches these. |
| `data/paper_rolled/2013.csv` through `2017.csv` | Earlier years used to fit the second forest. The page does not search them. |
| `data/training/UPDATED.csv` | HHS OIG List of Excluded Individuals/Entities. Labels come from this file. |
| `data/nppes/npi_sex.csv` | NPI to M/F, used when a CMS year has no gender column. |
| `models/candidates/blend_357_247.joblib` | The saved ranker. Both forests are inside this file. |

`scripts/paper_roll_year.py --year YEAR` downloads one CMS year and writes `data/paper_rolled/YEAR.csv`. Use that command. `scripts/download_year.py` writes an older layout in `data/rolled/`, and the page does not read that folder.

## Commands

From the repo root, with Python 3.14:

```
py -3.14 -m pip install -r requirements.txt
py -3.14 -m unittest discover -s tests
```

The second command runs on a fresh clone. Tests that need the model or a year file skip themselves and say which file they need.

To build the page files, one year at a time:

```
py -3.14 scripts/paper_roll_year.py --year 2024
```

Replace `2024` with each year from 2013 through 2024. That script downloads the CMS year, writes `data/paper_rolled/YEAR.csv`, and deletes the raw CSV after the roll exists. `--keep-raw` leaves the raw file in `data/raw/`. A year is about 3 GB before the roll and about 400 MB after it. 2013, 2014, and 2015 have direct CSV URLs in that script. 2016 through 2024 open the CMS resources page for that year and take the CSV URL from the open page.

The current LEIE file is already in this repo at `data/training/UPDATED.csv`. A newer monthly file is the direct download https://oig.hhs.gov/exclusions/downloadables/UPDATED.csv. The page that lists it is https://oig.hhs.gov/exclusions/exclusions_list.asp. Save a replacement as `data/training/UPDATED.csv`.

NPPES:

```
py -3.14 scripts/nppes_gender.py
```

That reads `data/nppes/NPPES_Data_Dissemination_October_2026_V2.zip` and writes `data/nppes/npi_sex.csv`. The zip URL is https://download.cms.gov/nppes/NPPES_Data_Dissemination_October_2026_V2.zip. The listing page is https://download.cms.gov/nppes/NPI_Files.html.

The saved ranker is not a public download. Copy `models/candidates/blend_357_247.joblib` from the person who trained it. The page cannot score a row without that file.

## Where the public files come from

1. Medicare Physician & Other Practitioners by Provider and Service, one file per year, from https://data.cms.gov/. A row is one rendering NPI, one HCPCS code, and one place of service. `scripts/paper_roll_year.py` downloads the year into `data/raw/` and writes the rolled file.
2. LEIE, the monthly `UPDATED.csv`, from https://oig.hhs.gov/exclusions/downloadables/UPDATED.csv. Save it as `data/training/UPDATED.csv`. A provider-year is a fraud label only when `EXCLTYPE` is `1128a1`, `1128a3`, `1128b6`, or `1128b7` and the exclusion year is after the billing year.
3. NPPES dissemination file, from https://download.cms.gov/nppes/NPPES_Data_Dissemination_October_2026_V2.zip. The zip is about 1 GB. `scripts/nppes_gender.py` keeps only NPI and sex in `data/nppes/npi_sex.csv`.

## Shape of a rolled row

`scripts/paper_roll_year.py` groups a raw year by specialty, NPI, gender, and year. It keeps name, city, state, and ZIP for the search and the map. Those five fields are not model features. The numeric features are the mean, sum, median, standard deviation, min, and max of five line fields:

- line service count
- unique beneficiary count
- beneficiary day service count
- average submitted charge
- average Medicare payment

The column names in the rolled file match `app/page_logic.py`.

## What not to put back

These were copies of the files above. They are not a second dataset.

- `data/rolled/` was an earlier rollup. The page uses `data/paper_rolled/`.
- `data/training/physician_2013_2023.csv` was the rolled years stacked into one file.
- `data/feature_columns/`, `data/paper_scores/`, `data/paper_scores_rus/`, and `data/paper_rus_parts/` were experiment outputs.
- `data/nppes/NPPES_Data_Dissemination_October_2026_V2.zip` was the zip after `npi_sex.csv` had been extracted.
- `app/data/search.sqlite` is rebuilt on launch.

## Run the page

```
py -3.14 -m pip install -r requirements.txt
py -3.14 app/server.py 8765
```

Open http://127.0.0.1:8765/. A static file server cannot score a row.
