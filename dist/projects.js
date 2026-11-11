// Add one record per completed project. Keep evidence and downloads project-specific.
const projects = [{
  slug: "sentinel-ai",
  name: "Sentinel AI",
  field: "Financial technology",
  summary: "A fraud investigation workspace that takes an analyst from an unusual payment to the evidence behind it.",
  tools: ["Python", "scikit-learn", "SQLite", "Streamlit"],
  pictures: [
    {src:"media/overview.jpg", name:"Risk overview", caption:"An analyst can select a high-priority transaction and inspect the rules and customer history behind its score."},
    {src:"media/simulator.jpg", name:"Risk simulator", caption:"Changing the amount, device or transfer frequency reveals how the rules and models respond to the same hypothetical payment."}
  ],
  source: "media/sentinel-ai.zip",
  problem: "A flagged payment creates work for a reviewer. To decide what to investigate, the reviewer needs to know what changed, whether that behavior is unusual for the customer, and how often the detector raises a false alarm.",
  contribution: "This build connects a reproducible transaction generator, three detection methods and an analyst workspace. A reviewer can inspect individual signals, compare them with earlier customer activity, save a case note and export the findings.",
  decisions: [
    ["Generate the history first", "A seeded generator creates 100,000 events across 90 days. Each customer's spending average, known devices and recent activity use only events already observed."],
    ["Score each payment three ways", "Weighted rules explain individual signals. Isolation Forest ranks unusual combinations. Logistic regression estimates the synthetic label probability. The simulator calls the same scoring functions."],
    ["Keep the case next to the evidence", "SQLite stores the ledger and case notes. Revision checks prevent one analyst's stale save from overwriting another edit. Streamlit handles exploration and Plotly renders the detailed charts."]
  ],
  evaluation: {
    context:"On the final 20,000 transactions, 414 carried a synthetic positive label. Select a method to see the review workload at its documented cutoff.",
    methods:[
      {name:"Rules",cutoff:"Rule score ≥ 25",tp:356,fp:627},
      {name:"Isolation Forest",cutoff:"Anomaly percentile ≥ 98",tp:259,fp:117},
      {name:"Logistic regression",cutoff:"Synthetic probability ≥ 0.50",tp:216,fp:98},
      {name:"Amount baseline",cutoff:"Amount ≥ training 99th percentile",tp:102,fp:109}
    ],positives:414,
    takeaway:"At these cutoffs, switching from rules to Isolation Forest would remove 510 false alerts and miss 97 additional synthetic positives. Choosing a threshold means deciding how much review capacity to spend for additional recall."
  },
  reproduceIntro:"Download and extract the source, open the sentinel-ai folder in a terminal and use Python 3.13. The first run generates the database locally. No API key is required.",
  commands:"python3 -m venv .venv\nsource .venv/bin/activate\npython -m pip install -r requirements-dev.txt\npython -m pytest -q\nstreamlit run app.py",
  verify:"The nine tests cover data validation, scoring, persistence and the seven-page workflow. In the default ledger, the overview should show 100,000 transactions and 5,580 flagged for review. Select a queue row, save a synthetic note and reopen the transaction.",
  limits:"The labels come from a generator, and evaluation uses one chronological split. A strong result here measures how well a detector recognizes the simulated behavior. It cannot establish real banking performance.",
  next:[
    ["Test generalization", "Repeat evaluation across seeds, unseen customers and different fraud patterns. Report the spread of precision and recall at the same review budget."],
    ["Evaluate calibration", "Compare predicted probabilities with observed positive rates in held-out bins. Test whether threshold choices remain stable as prevalence changes."],
    ["Strengthen case management", "Add authenticated analysts, durable storage and an append-only case history. Verify simultaneous edits and recovery after a restart."]
  ],
  credit:"AI coding tools assisted implementation, debugging and interface design. All transactions and labels are synthetic."
}];
