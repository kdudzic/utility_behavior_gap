# Public-Package Verification

Verified 2026-09-22 in a separate checkout populated from the Git index, with a
fresh CPython 3.13 virtual environment installed from `requirements.txt`.

The analysis process was forbidden from opening the private research checkout,
the private backup checkout, or the separate utility-fitting checkout. Network
connections were also blocked. No model APIs were called.

Command tested:

```bash
python paper_reproduction/reproduce.py run
```

Results:

- All four steps completed in 70.45 seconds on the verification machine.
- 29 numerical/table comparisons passed against the preserved references.
- All 196 model/task cells across seven outcome contrasts matched the accepted
  confidence intervals and tie counts; the five primary aggregate summaries
  matched their unified bootstrap reference.
- Both utility-trend regression sets matched their references.
- All 236 generic/rubric feature rows matched the saved length-controlled
  estimates; all four formatted feature tables matched exactly.
- Feature-directionality counts, intervals, and LaTeX matched.
- The original reasoning summaries, local-label Qwen follow-up, and updated
  suspicion-exclusion analysis matched. The follow-up adds 1,620 comparisons
  to the original 300 Qwen comparisons.
- 14 targeted unit tests passed in the isolated checkout.
- The regenerated high-low lollipop was visually inspected: model and panel
  labels are not cropped, the horizontal scale is 0-1, and interval annotations
  use the family-wise convention.

These checks validate deterministic analysis reproduction from the packaged
measurements, saved judgments, and labels. They do not regenerate paid model
responses, independently re-label traces, or prove the original annotations
correct. See `ARTIFACTS.md` for retained historical material outside this runner.

Raw API caches were not copied into the public repo. Newly packaged processed
inputs, including the Qwen follow-up traces, occupy approximately 45 MiB
compressed. The original trace package is an additional 8.7 MiB. Previously
tracked historical files are retained rather than deleted.
