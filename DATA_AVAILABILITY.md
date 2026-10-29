# Code and data availability: what CEUS expects, and what to hand over

CEUS follows Elsevier's Research Data policy **Option B**: sharing is
*encouraged, not mandatory*. There is no box that must be ticked, and a
submission will not be rejected solely because the code is missing. What the
policy does require is a **Data statement** that says what is available and,
where something cannot be shared, why.

That is the rule. The practice is harsher, because the journal's whole identity
is computational: reviewers routinely ask for the script behind a table, and a
paper whose central claim is a *measurement protocol* is judged on whether
someone else can run that protocol.

## Three options, ranked by what they buy you

| What you hand over | Reviewer reads it as | Recommended? |
|---|---|---|
| Pseudocode only | "They do not intend anyone to reproduce this." Adds nothing over the equations already in the Methods | No |
| Results tables only (the CSVs behind Tables 2-16) | "The numbers exist, but the path to them does not." Acceptable as a minimum, weak for a methods paper | As a floor, not as a plan |
| Analysis code + derived 1 km table + README + parameters | "This is a protocol someone can apply elsewhere." This is what "reproducible" means in a CEUS review | Yes |

The middle row is the honest answer to "may we ship the result tables only?":
yes, it satisfies the letter of Option B, but it undercuts the paper's main
selling point. A
reviewer who cannot rerun the G2SFCA identity check has to take the 99.57 % on
faith — and that number is the paper's proof of correctness.

## What can and cannot leave your disk

| Asset | Redistributable? | What to do instead |
|---|---|---|
| Analysis-ready 1 km table (derived, de-identified) | Yes, if no licensed micro-data is embedded | Deposit on Zenodo with a DOI; a few hundred MB is fine |
| G2SFCA / morphology / street-view indicator code | Yes | MIT licence in this repository |
| School POI (Amap) | No — vendor licence forbids redistribution | Publish query keywords, retrieval date, counts per city, and the deduplication rule |
| Road network | Depends on source: OSM is ODbL (share with attribution); commercial extracts are not | If OSM, ship the `.osm.pbf` extract filter; if commercial, ship a script that rebuilds from the same source |
| Street-view imagery | No — imagery licence | Ship the 1 km indicator table (already aggregated) plus the segmentation model name and prompt/label set |
| Population grid | Usually yes with attribution (WorldPop / census) | Cite the version and year; include the dasymetric step |
| Community education index (30 m) | Depends on the underlying survey | Ship the 1 km aggregate, not the 30 m source |

The principle: **aggregate, do not withhold.** Almost everything restricted at
the point level can be published at 1 km without breaching a licence, and 1 km
is the unit the paper actually analyses.

## Paste-ready data statement (full sharing)

> The analysis code, the derived 1 km analysis table, and all parameters needed
> to reproduce Tables 2-14 and Figures 1-7 are archived at Zenodo
> (DOI: 10.5281/zenodo.XXXXXXX) under an MIT licence for code and CC BY 4.0 for
> data. School locations were retrieved from the Amap POI service in March 2025;
> the vendor licence does not permit redistribution of the raw points, so we
> provide the query terms, retrieval dates, per-city counts and the
> deduplication rule, from which the point set can be rebuilt. Street-view
> imagery is likewise not redistributable; we publish the resulting 1 km
> indicator table and the segmentation label set used to produce it.

## Paste-ready data statement (restricted)

> The 1 km analysis table and the code that generates every table and figure in
> this article are available from the corresponding author on reasonable
> request. Raw school locations and street-view imagery cannot be shared because
> they are licensed from commercial providers; the aggregation parameters and
> retrieval protocol are reported in Section 3 so that the measurement can be
> repeated with equivalent inputs.

The first statement is worth the one day of packaging. The second is the fallback
if a licence review blocks release before submission.

## Checklist before submission

- [ ] Repository public, tagged `v1.0.0`, Zenodo DOI minted
- [ ] `make demo` runs from a clean environment in under two minutes
- [ ] Every table and figure in the paper is listed in `docs/paper_mapping.md`
      with the script and command that produce it
- [ ] `configs/params.yaml` contains every threshold quoted in the text
- [ ] Data statement names the DOI, the licence, and the reason for each
      restriction
- [ ] No absolute paths, no credentials, no personal data in the repository
