# Experiment design: Mens vs Womens e-mail campaign

This plan was written before this repository computed any outcome. Changes made after the outcome data are opened go in the Amendments section, with a date and a reason.

The data are public (Hillstrom, 2008) and have been analyzed many times. I have seen published summaries, so the plan is not blind. What it does is fix the metrics, tests and decision rule before the analysis here is run.

## Decision

Which e-mail, if any, should go to customers who bought in the last 12 months, and should the choice depend on the customer?

## Design

- Population: 64,000 customers whose last purchase was within the past 12 months.
- Unit of randomization and analysis: the customer.
- Arms: Mens e-mail, Womens e-mail, and no e-mail (control), each assigned to about one third at random.
- Outcome window: two weeks after the send.
- One readout at the end. There are no interim looks. Sequential monitoring is studied separately on data with checkpoints.

## Metrics

| Metric | Definition | Role |
| --- | --- | --- |
| Visit rate | share of customers with `visit = 1` | Primary |
| Conversion rate | share of customers with `conversion = 1` | Secondary |
| Spend per customer | mean of `spend`, zeros included | Secondary |
| Spend per visitor | total spend / number of visitors | Secondary, ratio metric |
| Spend per converter | total spend / number of converters | Descriptive only, because it conditions on a post-treatment outcome |

There is no guardrail metric in the data. Unsubscribes and complaints were not recorded, and the readout will say so.

Pre-treatment covariates: `recency`, `history`, `history_segment`, `mens`, `womens`, `zip_code`, `newbie`, `channel`. They are used for balance checks, variance reduction and subgroups, never to define outcomes.

## Checks before any outcome is analyzed

1. Data: 64,000 rows, no missing values, exactly three arm labels, `spend >= 0`, `spend > 0` only when `conversion = 1`, and `conversion = 1` only when `visit = 1`. Violations are counted and reported, not dropped.
2. Sample ratio mismatch: a chi-square test of the arm counts against one third each. If p < 0.001, the analysis stops until the cause is found.
3. Balance: the standardized mean difference of each covariate (categories as indicators) for each e-mail arm against control. Any absolute value above 0.1 is flagged.

## Comparisons and estimates

- Each metric has three comparisons: Mens vs control, Womens vs control, and Mens vs Womens.
- Primary family: visit rate, three comparisons, two-sided, Holm correction at a familywise level of 0.05.
- Secondary metrics get 95% intervals with Holm correction within each metric.
- Effects are reported as absolute differences (normal intervals with unpooled variances) and as relative lifts (delta-method intervals).
- The ratio metric uses the delta method, checked with a customer-level bootstrap of 2,000 resamples.
- Variance reduction is reported as a second estimate next to the unadjusted one:
  - CUPED (Deng et al., 2013) with past-year spend (`history`) as the covariate.
  - Regression adjustment on all pre-treatment covariates, interacted with arm (Lin, 2013).
  - For each, the reduction in variance relative to the unadjusted estimate.

## Power

About 21,333 customers per arm. Power 80%, two-sided tests. The baselines are a grid, not estimates from the data. Values come from `results/design_mde.csv` (`scripts/mde_table.py`).

| Metric | Baseline | MDE at alpha 0.05 | MDE at alpha 0.05/3 |
| --- | --- | --- | --- |
| Visit rate | 5% | 0.59 points (11.8%) | 0.68 points (13.7%) |
| Visit rate | 10% | 0.81 points (8.1%) | 0.94 points (9.4%) |
| Visit rate | 15% | 0.97 points (6.5%) | 1.12 points (7.5%) |
| Visit rate | 20% | 1.09 points (5.4%) | 1.25 points (6.3%) |
| Conversion rate | 0.5% | 0.19 points (38.3%) | 0.22 points (44.2%) |
| Conversion rate | 1% | 0.27 points (27.0%) | 0.31 points (31.2%) |
| Conversion rate | 2% | 0.38 points (19.0%) | 0.44 points (21.9%) |
| Continuous metric | | 0.027 SD | 0.031 SD |

Relative MDEs are in parentheses. Alpha 0.05/3 is the first Holm step, the strictest one. The test is well powered for visits. Conversion effects smaller than about a quarter of the baseline rate can be missed. Spend has many zeros and a long right tail, so its SD is large relative to its mean, and its relative MDE will be large.

## Heterogeneity and targeting

- Pre-specified subgroups, each tested as an interaction with arm, with Holm correction within the set: past-year buyer type (mens only, womens only, both), `newbie`, and `channel`.
- Exploratory: an uplift model (T-learner with gradient boosting) fit on a random half of the customers and evaluated on the other half with a Qini curve.
- Exploratory: the value of the policy "send the e-mail with the larger predicted uplift, or none if both are negative", estimated on the held-out half by inverse probability weighting with the known assignment probability of one third.
- Exploratory results are labelled as such and do not change the primary decision.

## Decision rule

1. An e-mail qualifies if its Holm-adjusted visit effect against control is positive and its spend-per-customer effect is not negative.
2. If both qualify and the Holm-adjusted Mens vs Womens visit difference is significant, send the better one. Otherwise send the one with the higher spend per customer, and state that the visit test does not separate them.
3. A targeting policy replaces the single e-mail only if the 95% interval for its gain in held-out visit rate lies above zero.

## Amendments

**2026-10-21, clarifications before any between-arm estimate.** These were written after the arm-level means in `results/metrics/arm_metrics.csv` had been computed, but before any difference, interval or test. They fill in details the plan left open and do not change a metric, a test or the decision rule.

1. Holm correction applies to p-values. The reported 95% intervals are unadjusted.
2. Relative lift is measured against the second arm of each comparison: control for the two e-mail arms, and Womens for Mens vs Womens.
3. CUPED and regression adjustment are applied to the three customer-level metrics (visit, conversion, spend per customer). Spend per visitor is reported unadjusted.
4. CUPED estimates its coefficient on the two arms of each comparison, with `history` centered at their mean.
5. Regression adjustment uses all listed covariates. Categories enter as indicators with one reference level each, and `history_segment` enters next to `history`. Standard errors are HC2.
6. The bootstrap for spend per visitor resamples customers within each arm, with a fixed seed.

**2026-10-21, clarifications before any subgroup or uplift analysis.** Written after the between-arm estimates in `results/effects/` had been computed, and before any subgroup, uplift or policy result.

7. Subgroup analyses use visit, the primary metric, only.
8. Buyer type has three levels in the data: mens only, womens only, and both. No customer has neither.
9. For each subgroup variable, a linear probability model regresses visit on arm, subgroup level and their interactions, on all three arms, with HC2 errors. The test is a joint Wald test that all arm-by-subgroup terms are zero (4, 2 and 4 degrees of freedom for buyer type, `newbie` and `channel`). Holm correction runs over these three tests. The effect of each e-mail against control within each level is reported with a 95% interval, as description.
10. The uplift split is 50/50 at random within each arm, with a fixed seed. On the training half, one gradient boosting classifier for visit is fit per arm (scikit-learn `HistGradientBoostingClassifier`, default settings, fixed seed) on the 15 covariates in `analysis_frame.sql`. The predicted uplift of an e-mail is its predicted visit probability minus that under control.
11. The Qini curve for each e-mail ranks the held-out customers of that arm and of control by predicted uplift. At each targeted fraction it gives the incremental visits Y_t - Y_c N_t / N_c, scaled by the held-out size of the pair. The Qini coefficient is the area between this curve and the straight line to its end point.
12. Policy values are estimated on the held-out half by inverse probability weighting with assignment probability 1/3, for four policies: the targeting rule, Mens to all, Womens to all, and no e-mail. The comparison in decision rule 3 is the targeting rule against Mens to all, the single e-mail the rule selected. Its interval comes from the per-customer differences of the weighted terms.

## References

- Deng, A., Xu, Y., Kohavi, R. and Walker, T. (2013). Improving the sensitivity of online controlled experiments by utilizing pre-experiment data. WSDM.
- Hillstrom, K. (2008). The MineThatData e-mail analytics and data mining challenge. https://blog.minethatdata.com/2008/03/minethatdata-e-mail-analytics-and-data.html
- Lin, W. (2013). Agnostic notes on regression adjustments to experimental data: reexamining Freedman's critique. Annals of Applied Statistics 7, 295-318.
