# Readout: Mens vs Womens e-mail test

**Recommendation: send the Mens e-mail to every customer in this population, without model-based targeting.** The Mens e-mail increased the two-week visit rate by 7.7 percentage points against no e-mail and was effective in every buyer group. An uplift model that chose between the two e-mails did not improve on this rule for held-out customers.

## What was tested

In this test, 64,000 customers who had bought in the past year were randomized in equal proportions to a Mens e-mail, a Womens e-mail or no e-mail, and their visits, purchases and spend were tracked for two weeks. The metrics, tests and decision rule were fixed in [design.md](design.md) before any outcome was computed. The arm sizes show no sample ratio mismatch (p = 0.90), and all covariates are balanced, with a largest absolute standardized difference of 0.014.

## Results

The table gives each difference with its 95% interval. Rates are in percentage points.

| Metric | Mens vs no e-mail | Womens vs no e-mail | Mens vs Womens |
| --- | --- | --- | --- |
| Visit rate (primary) | +7.7 (7.0 to 8.3) | +4.5 (3.9 to 5.2) | +3.1 (2.4 to 3.8) |
| Conversion rate | +0.68 (0.50 to 0.86) | +0.31 (0.15 to 0.47) | +0.37 (0.17 to 0.56) |
| Spend per customer | +$0.77 (0.49 to 1.06) | +$0.42 (0.17 to 0.68) | +$0.35 (0.03 to 0.66) |
| Spend per visitor | +$1.64 (-0.30 to 3.57) | +$0.97 (-0.99 to 2.92) | +$0.67 (-1.17 to 2.51) |

Both e-mails increased visits, conversion and spend per customer, and the Mens e-mail outperformed the Womens e-mail on all three, with every difference significant after Holm correction. Spend per visitor did not differ between arms (adjusted p of 0.29 or more): the e-mails increased spend by bringing more customers to the site, not by increasing what each visitor spent. Adjustment for pre-period covariates changed the visit estimates by less than 0.1 points and reduced their variance by at most 0.4% with CUPED and 2.9% with regression adjustment, which reflects the weak relation between past-year purchases and two-week behavior.

## Who responds

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../figures/visit_lift_dark.png">
  <img src="../figures/visit_lift_light.png" alt="Visit-rate lift of each e-mail against no e-mail, overall and by past-year buyer group, with 95% intervals" width="750">
</picture>

Of the three pre-specified subgroups, only past-year buyer type changed the effect on visits (Wald test with 4 degrees of freedom, Holm-adjusted p < 0.001), whereas new versus returning customers and purchase channel did not (Holm-adjusted p = 0.30 and 0.97). The figure shows that the Mens e-mail increased visits in all three buyer groups, with the largest effect among customers who had bought both mens and womens items. The Womens e-mail matched it only among womens-only buyers, and among mens-only buyers it increased visits by 1.1 points (0.2 to 2.0).

## Targeting

A gradient boosting model for each arm was trained on a random half of the customers and evaluated on the other half. It would send the Mens e-mail to 72% of customers, the Womens e-mail to 25% and no e-mail to 3%. On the held-out customers this policy reached a visit rate of 17.8% (17.1 to 18.6), compared with 18.4% (17.6 to 19.2) for sending the Mens e-mail to all. The difference of -0.5 points (-1.2 to 0.1) does not meet the decision rule, which requires a gain. The Qini coefficients were 0.0002 for the Mens e-mail and 0.0034 for the Womens e-mail, against an expected 0 for a random ranking. These results are consistent with the subgroup analysis, in which the two e-mails had similar effects among womens-only buyers (7.4 points for the Womens e-mail, 7.1 for the Mens e-mail) and the Mens e-mail had the larger effect in the other two groups.

## Limitations

Several limitations remain. The data record no unsubscribes or complaints, which leaves the cost of sending unmeasured. The outcomes cover the two weeks after a single send in 2008, which does not measure long-run effects or the effects of repeated sends. Spend was concentrated in few customers: Radcliffe (2008) reported that "of the order of 50" customers produced more than half of the incremental spend, which makes the spend estimates less stable than the visit estimates. The subgroup tests used visits only.

## Next steps

1. Record unsubscribes and complaints in the next send, to allow a guardrail metric in the decision rule.
2. Repeat the test with a longer outcome window before the Mens e-mail becomes the default for future campaigns.

Sources: all numbers come from `results/` (`checks/`, `effects/`, `targeting/`). Radcliffe, N. (2008), [winning entry of the MineThatData challenge](https://www.stochasticsolutions.com/pdf/HillstromChallenge.pdf).
