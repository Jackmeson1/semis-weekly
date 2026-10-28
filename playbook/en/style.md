# Writing style

Reader: an individual investor who is learning macro, skims on a phone first, then reads closely. Every log (levels 1, 2 and 3) follows this guide.

Basis: an October 2026 preprint found that text written by large language models uses more hard-to-process syntax and rare phrasing than human writing, packing in information at the cost of being understood (Clark, Martin and Mahowald, arXiv 2610.29162). Comparable publications (broker macro weeklies, morning notes, market newsletters) share three habits: the conclusion comes first, one claim per sentence, and terms are explained where they first appear.

The number rule is unchanged: every number in the text must come from the input data. You may convert units or round. You may not compute new metrics or add numbers. If data is missing, write "no data this week."

## Structure and length

1. Lede first. The one-line summary is at most 25 words, makes one claim, has at most one number, and says both how things stand this week and what that means for the reader.
2. Visible text, excluding the json block: channel log 350–550 words; horizon log 300–450 words; synthesis 350–500 words.
3. One or two sentences per horizon; the explainer 90–150 words in two or three paragraphs; at most four items under deviations and uncertainty, each under 25 words, most important first.
4. No paragraph over four sentences or about 75 words.

## Sentences

5. One claim per sentence. Aim for 16 words on average and never exceed 25.
6. At most three numbers per sentence. More than that goes into a table.
7. At most one parenthetical per sentence, under 10 words, never nested. If it needs more, write a new sentence.
8. No telegraphic fragments. Keep the subject and the verb: not "jump not determined" but "the 10-year close for that day is not out yet, so we cannot tell whether yields jumped."
9. No noun stacks such as "cloud capex-to-operating-cash-flow quarterly change." Split them.
10. Put the actor first and the number second. Use a person or an institution as the subject, not "the data shows" or "the signal indicates."

## IDs and internal language

11. No internal IDs (the ones starting S-L, HZ, VETO, NOVETO, INF, CAL, ACT, INV, SW, CH) in the one-liner, the text or tables. Use the name or say what the rule means; names are in `playbook/glossary.yaml`. Instead of "VETO-01 not triggered," write "Funding is not blocked: that would take credit tightening and cloud capex reaching 1.0 of operating cash flow."
12. IDs go only into `signal_refs` and `rule_refs` in the closing json block, for tracing. The verdict, horizons, chains and invariants strings in the json are shown on the page, so they carry no IDs either. `semis check` rejects a log that has them.
13. No pipeline language: "input package," version numbers, "first version," "I did not recompute," "truncated at 15,000 characters." Say it the way the reader would understand it: "Only META has reported this week."
14. No boilerplate such as "added threshold, to be calibrated." Mention where a threshold comes from only when it changed this week's conclusion, once: "This tripwire is our own, not the author's."

## Terms (the reader is learning)

15. The first time a term appears in a log: name, one plain sentence, this week's number.
16. Explain at most two new terms per log. Use only words the reader has already met for the rest.
17. Explain a term where it first appears, not later in the explainer.
18. The explainer teaches one concept with this week's numbers. Its last sentence says how it reaches semiconductors.

## Terms of art

19. Keep as is: capex, VIX, FOMC, CPI, GEX, CTA, bp, MBS, TGA. Spell out HY and IG once ("high-yield (HY)"); gloss 2s10s once as "the gap between 2-year and 10-year yields."
20. Say in plain words: gamma flip is "the gamma flip level", vol control is "volatility-control funds", when-issued is "pre-issue trading", LOs are "long-only funds".
21. Use only the four state labels the page shows: Not binding, Near, Binding, No data.
22. Not "plus points / minus points" but "supportive / unsupportive," and say for which question, for example "for the question of cloud capex returns."

## Numbers

23. Every number carries four things: value, unit, direction and a comparison point. For example: "The 10-year yield fell from a% to b%, down c bp in five trading days; last week it fell d bp."
24. Write the direction in words (fell, rose, widened, narrowed), not only with a sign.
25. One money unit per log (billions throughout, for example). Companies that report in another currency (TSMC in NT$, ASML in euros) keep their own currency; do not convert.
26. Name the comparison: last week, last quarter, a year ago, or the tripwire. No ambiguous "prior period" column.
27. Give the full form of a number once, then refer to it briefly.

## Tables and prose

28. Tables for numbers to compare, prose for relationships. At most 5 columns and 6 rows; each cell under 12 words and at most two numbers.
29. Date ranges and definitions go in a note under the table, not in the cells.
30. Evidence table columns: indicator (by name), this week, comparison (say whether it is last week, last quarter or a year ago), tripwire, state.

## Confidence and uncertainty

31. One vocabulary only: "well supported" (several independent data points agree), "roughly so" (supported, but one key datum is missing or approximate), "a guess" (mostly rule-based inference). These map to json confidence high, medium and low.
32. The first item under deviations and uncertainty is the one most likely to flip the conclusion, written as "If ..., the conclusion becomes ..."
33. At most one hedge word per sentence.
34. Missing data is always "no data this week," plus what is missing and which conclusion it affects.
