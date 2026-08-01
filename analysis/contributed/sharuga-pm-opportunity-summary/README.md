# Tower Hamlets: permitted:rejected ratio by Prime Minister and Opportunity Area

Contributed by **Sharuga**, from her own working analysis of the Tower
Hamlets planning-applications data.

## Her write-up (verbatim)

> 2021 - London Plan - divided certain areas into opportunity areas - which
> were places considered to need more development.
>
> In order to show a story i compiled the data at tower hamlets over the
> years with the various prime ministers and governments in charge to see
> if a pattern was observed.
>
> Graph shows the ratio of permitted and rejected proposals to do
> additional buildings (e.g. increase height) and renovations.
>
> As you can see there is no distinct pattern but the overall ratio
> permitted:rejected is 3.56:1 showing overall showing across the whole
> borough most were accepted.
>
> There was a 3.63:1 ratio for approval to rejection in opportunity areas
> whereas 3.41:1 in non-opportunity area within tower hamlet data set.
> Represent approximately 6% approval to rejection ratio within
> opportunity areas.

## Files

- [`data.csv`](data.csv) — her working data: one row per (year, Prime
  Minister, Opportunity Area yes/no), with Permitted/Rejected/Undecided
  counts and a permitted:rejected ratio column.
- [`chart.jpg`](chart.jpg) — her chart (a photo of an Excel line plot,
  compressed from the original for repo size; content unchanged).

## How this compares to the rest of this repo

I (the repo's other maintainer, via Claude) checked her numbers against the
same `housing_planning.sqlite` source this repo's pipeline uses, before
adding [`../../tower_hamlets_pm_opportunity_summary.csv`](../../tower_hamlets_pm_opportunity_summary.csv)
and its accompanying chart as a full-dataset counterpart. Two things are
worth knowing if you're comparing the two:

1. **Minor rounding**: her write-up states 3.56:1 / 3.63:1 / 3.41:1
   (overall / OA / non-OA), but summing her own `data.csv` gives 3.64:1 /
   3.68:1 / 3.58:1. Small difference, doesn't change the conclusion.
2. **Scope**: her totals (1,654 permitted + 454 rejected = 2,108 decided
   applications, 2016–2026) are less than half this repo's full Tower
   Hamlets total for the same period (4,426 decided applications, all
   application types). Her write-up describes the scope as "proposals to
   do additional buildings (e.g. increase height) and renovations," which
   implies she filtered to a specific subset of application types. I tried
   the most obvious candidate in the source data (`app_type = "Full
   Planning Permission"` only) and it doesn't reproduce her numbers either
   (2.11:1 / 2.38:1 — different ratios, not just a different total), so
   her exact filter isn't reconstructable from what's in the sqlite export
   alone. If you're reading this, Sharuga — it'd be great to know the exact
   filter/query so the two analyses can be reconciled properly.

Neither version is "more correct" than the other — they're answering
slightly different questions (a specific proposal-type subset vs. every
application type). See the root README's Prime Minister section for what
the full-dataset version shows.
