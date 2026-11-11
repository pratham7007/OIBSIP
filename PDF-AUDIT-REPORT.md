# OASIS PDF Checklist Audit

This report compares the deliverables in this workspace with the 52 assignments in
`OASIS INFOBYTE — Task List.pdf`. It records work that is implemented separately from
work that still needs a suitable dataset, a local device/lab, or an external action.
No missing measurements, lab results, screenshots, or credentials have been invented.

## Summary

| Track | Assignments | Audit status |
|---|---:|---|
| Web Development & Designing | 8 | Deliverables are present and were previously marked complete. |
| Android App Development | 5 | All five screens are implemented; no Android SDK/emulator/device validation is documented. |
| Java Development | 5 | All five applications are implemented; interactive GUI checks are not documented. |
| Graphics Design | 5 | All exports regenerated and checked; two PDF source/publication checklist items remain (below). |
| Data Science | 5 | All five workflows execute; unemployment and car-price workflows use synthetic data. |
| Python Programming | 5 | Applications are implemented; live integrations and desktop/audio behavior need external runtime checks. |
| Data Analytics | 9 | All nine workflows execute; data and notebook-structure gaps remain (below). |
| Security Analyst | 10 | Tasks 4–6 have research reports; practical evidence for the other seven tasks is absent. |

The Data Science three-task minimum is met by the Iris, SMS spam, and advertising-sales
workflows; the synthetic unemployment and car-price workflows remain partial. The
Security Analyst track has only three report-ready tasks against its four-task minimum.
Source implementation is not equivalent to a tested Android, Java GUI, live API, or
security-lab submission.

## Remaining or partial checklist items

### Android App Development

- **Tasks 1–5 — runtime verification pending.** Unit converter, login/to-do, calculator,
  quiz, and stopwatch source is present. The Android SDK/emulator/device checks were not
  run in this audit, so builds, navigation, persistence, and device behavior are not
  claimed as verified. See [the Android setup notes](./ANDROID%20APP%20DEVELOPMENT/README.md).

### Java Development

- **Tasks 1–5 — interactive GUI verification pending.** The projects were previously
  reported as build/smoke-tested, but the Swing interfaces have not been manually
  exercised in this audit.

### Graphics Design

- **Task 2 — LinkedIn publication pending.** A design rationale and post copy are saved
  locally; the required LinkedIn post has not been published.
- **Task 5 — image-source checklist deviation.** The brochure uses original vector
  illustrations rather than royalty-free stock images from the PDF's named sources. This
  avoids unlicensed imagery, but does not literally satisfy that sourcing checklist.

The generated infographic was verified at 800×2000 pixels and at least 150 DPI. The
brochure PDF has six A4 pages; the business-card PDF has two pages with a 91×61 mm page
size, corresponding to 85×55 mm trim with 3 mm bleed.

### Data Science

- **Task 2 — unemployment analysis is synthetic.** The current workflow illustrates
  regional/time-series analysis but does not use measured Indian unemployment data; its
  pandemic comparisons must not be interpreted as empirical findings.
- **Task 3 — car-price prediction is synthetic.** Model results do not represent a used-car
  market or real selling prices.
- **Notebook narrative requirement — partially met.** The notebooks call shared analysis
  functions from one code cell and contain generic introductory markdown. The PDF asks for
  written, task-specific observations in notebook markdown (including observations between
  charts for unemployment). Printed runtime notes do not fully replace those markdown
  cells.

### Data Analytics

- **Task 1 — retail demographics and product categories unavailable.** UCI Online Retail
  has no customer age/gender or product-category fields. Those requested distributions
  cannot be derived honestly from this source. The notebook documents the limitation
  instead of fabricating them.
- **Task 2 — true customer lifetime value is unavailable.** The workflow reports
  same-period historical spend as a clearly labelled proxy; it does not estimate
  predictive lifetime value.
- **Task 3 — notebook documentation partially met.** Cleaning decisions and before/after
  metrics are produced by the shared analysis code, but the notebook is a thin wrapper and
  does not contain the PDF's requested per-decision markdown explanations.
- **Task 4 — notebook narrative partially met.** The workflow computes model metrics,
  class-specific word clouds, and misclassification notes, but the notebook does not have
  task-specific markdown cells discussing each result as requested.
- **Task 7 — fraud records are synthetic.** The pipeline demonstrates an imbalanced-data
  workflow but cannot substantiate fraud-detection performance on real transactions.
- **Task 8 — historical-data caveat.** The licensed Play Store snapshot is from 2018.
  Install counts are bucketed and the revenue measure is only a price-times-install-floor
  proxy, not observed revenue or a current-market estimate.

### Python Programming

- **Tasks 1 and 4 — live integrations not verified.** Voice input needs a working
  microphone/audio setup; speech recognition uses the library's remote recognition
  service. Live weather requires a valid API key. These integrations have not been
  exercised with user credentials or hardware.
- **Tasks 1–5 — GUI/service runtime checks pending.** Python syntax checks passed for all
  six application scripts, and password-generation boundary/type guarantees passed. This
  does not substitute for manually exercising the desktop UIs, audio, HTTP, or local chat
  client/server.

### Security Analyst

- **Tasks 1–3 and 7–10 — practical evidence incomplete.** No authorized local VM/firewall/
  DVWA lab was available and the required Nmap, UFW, Nikto, Wireshark, and DVWA evidence
  was not collected. This includes scan outputs and screenshots, firewall verification,
  DVWA exercise evidence, authorized capture/analysis, advanced lab evidence, and the
  end-to-end assessment report. Templates and defensive explanations are not evidence of
  completed practicals.
- **Tasks 4–6 — research reports prepared.**
- **Track minimum:** only 3 of 10 tasks are report-ready, below the PDF's 4-task minimum.
  Practical work must be performed by the student only in a system/lab they own or are
  explicitly authorized to test. No third-party system was scanned or tested.

## Validation performed for this audit

- Executed all 14 Data Science/Data Analytics workflow functions with a non-interactive
  plotting backend; all completed successfully.
- Compiled all six Python Programming scripts for syntax.
- Tested password generation at lengths 8, 12, 20, and 256, including selected character
  type guarantees, ambiguous-character exclusion, and invalid input rejection. Generated
  passwords were not printed.
- Regenerated the graphics exports and checked the infographic dimensions/DPI, PDF page
  counts and physical dimensions, and logo variants/vector/post-copy files.
- Verified without printing any credential that the exam demo-credential output uses a
  format specifier for the generated password.

These checks do not replace the external runtime, device, publication, dataset, or
authorized lab steps identified above.
