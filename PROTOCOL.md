# Analysis protocol
Specified after inspecting schemas, counts and coverage, before fitting outcome models (29 September 2026). This is an exploratory, single-dataset analysis, not a preregistration.

## Questions and directional hypotheses
- O1 (distributed engagement): more active days in OULAD days 0-55 predicts lower subsequent Fail/Withdrawn odds, controlling total clicks, module/season, prior attempts, workload and early submission completion.
- O2 (recent disengagement): lower log((clicks days 42-55 + 1)/(clicks days 28-41 + 1)) predicts higher subsequent Fail/Withdrawn odds, additionally controlling active days and the O1 controls.
- M1 (habit formation): more active days in Moodle's first eight observed calendar weeks predicts more active days in weeks 9-12, controlling early event volume, initial arrival week and resource diversity.
- M2 (breadth): greater early Shannon diversity of non-System component types predicts more active days in weeks 9-12, controlling volume, active days and initial arrival week.

## Scope
OULAD: landmark at day 56; include registrations by day 0, no withdrawal before day 56. Train/validate on 2013 enrolments with person-disjoint 80/20 split; evaluate once on 2014 users not present in 2013, restricted to module-season combinations observed in training. All early features end at day 55. No scores or future submission facts as predictors.
Moodle: use the assignment's MOODLE Data.csv. Day 0 is midnight of the first observed date; this is an observation anchor, not a verified course start. Include user IDs first observed before day 28, making four or more weeks available before cutoff. Later inactivity means no recorded events, not dropout. No claims about grades. Supplementary folders have incompatible identifiers/schema and are not pooled.

## Evaluation
OULAD: dummy prevalence, logistic volume/context baseline, enhanced logistic model and random forest. Hyperparameters fixed; select enhanced model threshold by validation F1, assess test AUROC, average precision, Brier, balanced accuracy, precision/recall/F1 and confusion matrix. Use person-clustered bootstrap intervals for AUROC and paired differences; never optimize on test. Exploratory adjusted O1/O2 inference on 2014 held-out data with person-clustered standard errors.
Moodle: standardized log event volume, active days, component diversity and quiz share; K-Means k=2..5 chosen by silhouette. Evaluate resample stability (ARI), report profiles and future participation as external descriptive validation. M1/M2: OLS with HC3 errors and bootstrap intervals; report association, not causation. Holm correction jointly for the four directional hypotheses using conservative two-sided p-values.

## Cleaning and sensitivity
Check unique keys, joins, duplicate rows, dates, missingness and excluded counts. OULAD is daily aggregation: no minute-level sessions/time-on-task. Moodle excludes auto-save and SCORM score/status telemetry from primary event counts; sessions split at gaps >30 minutes, summed within-session gaps are observed duration proxies, not attention. Sensitivity at 15/60 minutes and with telemetry retained. No inferred due dates, grades, or unobserved zero-event enrolled students.

## Post-fit diagnostic checks (explicitly secondary)
The raw OULAD table contained 787,170 exact repeated rows, whose provenance is not documented. Primary counts retain supplied rows; refit adjusted associations after removing exact repeats to test dependence on this choice. Also distinguish Fail from withdrawal by excluding withdrawn cases, isolate the temporal feature increments with fixed logistic models, and check Moodle OLS directions using a bounded fractional-logit mean model. These checks do not replace primary results or select the reported classifier.
