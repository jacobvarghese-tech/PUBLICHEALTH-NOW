---
type: query
title: Can it be a good flag and database
updated: 2026-10-17
tags: [query, app]
sources:
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC6120851/
---

# Can it be a good flag and database

## Question

Can Medicare Fraud Flagger actually be a good flag and a good database?

## Answer

The database half can be good. The flag half can be a useful score for a name you already have. It cannot be a reliable national hunt list, and that limit is known before training.

The browser is a search over the official public billing file for 2018–2024, plus exclusion status from the LEIE. That is a real record. A person with a name, city, or NPI can pull the eight numbers and see whether that NPI was later excluded. That part does not depend on the model being sharp.

The flag is a rank. The closest published test, Bauder and Khoshgoftaar 2018, got an AUC of about 0.873 with a random forest at a 90:10 mix on 2012–2015. AUC 0.87 means excluded providers tended to rank above clean ones. It does not mean 87% of fraud is caught. This build uses a different model, eight rolled features, and later years, so that number is a ceiling to compare against, not a promise.

The base rate makes a browsable "top flags" list a poor product. Fraud-type exclusions are a few hundred provider-years against on the order of a million providers. A top 1% list is still mostly clean providers. The honest use is: someone brings a name, the page returns a percentile, and a person checks the provider. Printing the 2024 top 1% and top 5% capture on the about page is the quality statement.

The two Coffeezilla labs are a hard case for this grain of data. A source row is one NPI, one HCPCS code, and one place of service. The model sees the year rolled up. A lab whose odd billing is one code can look ordinary after the rest of the year is averaged in. Top-code share keeps a piece of that signal. If their 2024 percentile is outside the top 5%, the page says so. That miss would not mean the database failed.

## Citations

- Bauder and Khoshgoftaar, Health Information Science and Systems, 2018, https://pmc.ncbi.nlm.nih.gov/articles/PMC6120851/
- [[action plan]]
- [[app viable]]
- [[scope]]

## What this changes in the wiki

Filed this page. Did not change [[scope]]. The page still ships the percentile either way.
