### Synthetic ledger

A fixed seed (42) produces 90 days of USD transactions. Customers have persistent home countries, spending scales, account ages and different activity rates. Most events are independent. Selected four-event groups share a customer and device and arrive 19 seconds apart. These groups simulate multiple transfers, elevated spending and occasional cross-border activity. Some groups are benign. A small number of isolated events receive positive labels, sometimes without an observable signal. Labels record the generator's scenario assignment.

### What the rules measure

| Signal | Default points | Interpretation |
|---|---:|---|
| Spending spike | 30 | Amount reaches three times the customer's prior mean. |
| Rapid activity | 26 | At least two preceding transactions within one hour. |
| Unseen device | 14 | First observation of the device for this customer. |
| IP mismatch | 16 | IP country differs from the customer's home country. |
| New beneficiary | 13 | Simulated first-time beneficiary indicator on a transfer. |
| Cross-border | 8 | Destination differs from origin. |
| Young account | 6 | Account age under 30 days provides less history. |

The rule score sums the contributions up to 100. Default cutoffs are 25 for Medium, 50 for High, and 75 for Critical. Medium and above enter the review queue. Flagged value sums transaction amounts and does not estimate losses. Configuration changes apply within the current session. These illustrative weights have no banking-policy approval.

### Evaluation design

The first 80% of the chronological stream defines training. All events at or after the split timestamp are reserved for evaluation. The historical mean starts with five observations' worth of a seeded customer prior. Device history, average spend and hourly counts update only after scoring features are constructed.

Isolation Forest ranks unusual combinations of seven numeric behavioral features. Its displayed percentile is the fraction of training anomaly scores at or below the observation. Logistic regression estimates the synthetic class probability using the same features. Its probability has no external calibration. A simple comparator flags amounts at or above the 99th percentile of training amounts. The model dashboard applies workspace filters to the fixed holdout without retraining.

### Analyst interpretation and limits

A signal supports an investigation. A label-0 alert is a false positive for this benchmark. Travel and first use of a device can both be legitimate. The generator simplifies geography, devices, currency, beneficiary history and customer behavior. Model quality reflects those assumptions. Monitoring views include training-period scores for exploration. Use the holdout dashboard for performance claims.

SQLite stores case revisions on the host. The demo has shared notes, no analyst authentication, and no immutable audit trail. Use synthetic notes only. Hosted filesystem resets can discard local records.
