# Robustness

How we show the order is trustworthy, not just a formula we picked.

Related: engine.md, ../ai/jev.md (label and training table).

## Official verifier

data/dataset/verificar_fila_priorizada.py checks the format, coverage and the golden rule. It must pass before anything else.
It also prints indicators we can quote in the pitch: median position of oncologic patients, % with recent ER/hospitalization in the first half, % without urgency in the last third.

## Monte Carlo on the weights

The weights (w1..w5) are a judgment call. Show how much the order depends on them.
- Sample many weight sets around the chosen ones (Dirichlet around the defaults, or +-20% each).
- Recompute the ordering for each sample.
- For each patient, report the range: "stays between positions 8 and 14 in 95% of scenarios".
- Narrow range = robust position. Wide range = send to a human (and to the agent review).

## Backtest without leaking future data

- Compute features as of a past date t, using only events up to t (data/build_features.py --asof).
- Check whether the top-ranked patients really had worsening events after t.
- Metrics: precision@k, AUC.
- Compare against the current method (entry date + manual priority).
- Label and numbers: ../ai/jev.md.

## Queue simulation

- Simulate the queue over time with operating-room capacity (assumed: the dataset has duration and ICU need per procedure, but no capacity).
- Compare: FIFO + manual priority vs our engine.
- Measure: patients past their tier's max wait, worsening while waiting, wait of A1/A2 patients, wait of C/D patients (we do not starve them).

## Sensitivity

- Remove one score part at a time and measure how much the order changes (Kendall tau vs the full model).
- Shows which parts actually drive the ranking.

## Equity

- Check the order does not systematically penalize groups (age, sex, municipality, distance).
- Municipality and distance are not model inputs (logistics only). Age is used as frailty, and we say so.
- Overrides are logged, so bias in overrides can be audited too.
