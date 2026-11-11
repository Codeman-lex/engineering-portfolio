projects.push(...[
  {
    "slug": "veritas",
    "name": "Veritas",
    "field": "AI evaluation & reliability",
    "summary": "Compare two candidate responses against the same evidence, then trace a failed score back to the exact criterion.",
    "problem": "A plausible answer can quote the wrong invoice total while returning valid JSON. A single pass rate hides that distinction.",
    "contribution": "A versioned evaluation lab for five task families, side-by-side response fixtures, threshold experiments, error analysis and human review history.",
    "pictures": [
      {
        "src": "media/veritas-workbench.jpg",
        "name": "Response workbench",
        "caption": "Response workbench in the running synthetic workspace."
      },
      {
        "src": "media/veritas-experiments.jpg",
        "name": "Experiment register",
        "caption": "Experiment register in the running synthetic workspace."
      }
    ],
    "decisions": [
      [
        "Grade known claims",
        "Exact and numeric checks make failures reproducible. A semantic judge could accept paraphrases but would need its own validation. Tests include a valid object with the wrong field type."
      ],
      [
        "Freeze the evidence",
        "A content hash identifies each dataset. SQLite stores the response, criterion results, grader version and threshold at run time. Snapshots use more space but preserve old results when a dataset changes."
      ],
      [
        "Keep human judgments alongside scores",
        "Reviewers can assign a different score, explain it and mark ambiguity. Appending reviews preserves disagreement. A test checks that two reviews leave the automated snapshot intact."
      ]
    ],
    "evaluation": [
      [
        "Five task families",
        "Each family contains 60 generated examples. The benchmark contains factual lookup, invoice extraction, formatting, numerical analysis and uncertainty."
      ],
      [
        "200 versus 258 strict passes",
        "With a 100-point cutoff, 200 of 300 direct-answer fixtures and 258 of 300 evidence-first fixtures passed. Incorrect answers were injected by construction. This exercises the grader and makes no claim about model quality."
      ]
    ],
    "limits": "Known reference facts support narrow claims. Paraphrases, open-ended reasoning and subjective usefulness require human review. Candidate responses are authored fixtures.",
    "next": [
      [
        "Validate the rubric",
        "Collect independently scored responses from two reviewers, measure agreement and inspect ambiguous cases."
      ],
      [
        "Test live candidates",
        "Record actual model outputs with prompt, model version and decoding parameters before comparing them."
      ]
    ],
    "verify": "Open Experiment register and record both fixture sets at 100. Expect 200 and 258 passing responses. Inspect a failed field and append a reviewer score.",
    "flow": [
      "Versioned dataset",
      "Candidate fixtures",
      "Criterion checks",
      "Run snapshot",
      "Human review"
    ],
    "tools": [
      "Python",
      "SQLite",
      "Pandas",
      "Streamlit"
    ],
    "source": "media/veritas.zip",
    "reproduceIntro": "Extract the project ZIP and open its directory in a terminal with Python 3.13.",
    "commands": "python3 -m venv .venv\nsource .venv/bin/activate\npython -m pip install -r requirements.txt\npython -m pytest -q\nstreamlit run app.py",
    "credit": "AI coding tools assisted implementation and testing. The examples are synthetic."
  },
  {
    "slug": "aegis",
    "name": "Aegis",
    "field": "Compliance operations & automation",
    "summary": "Follow a fictional onboarding case from document intake through validation to a reasoned human decision.",
    "problem": "A changed address can disappear when a reviewer overwrites a form. The next reviewer needs both the old evidence and the reason for the change.",
    "contribution": "A case desk with structured document intake, configurable checks, correction and escalation workflows, case aging, decision timing and an append-only application audit history.",
    "pictures": [
      {
        "src": "media/aegis-case-desk.jpg",
        "name": "Case desk",
        "caption": "Case desk in the running synthetic workspace."
      },
      {
        "src": "media/aegis-intake.jpg",
        "name": "Intake simulator",
        "caption": "Intake simulator in the running synthetic workspace."
      }
    ],
    "decisions": [
      [
        "Use structured packets",
        "JSON allows field-by-field extraction with known expected values and a 64 KiB limit. OCR would require an additional recognition benchmark. Tests reject unsupported types and oversized packets."
      ],
      [
        "Separate completeness from inconsistency",
        "An absent address triggers a request for evidence. A conflicting address identifies two values to reconcile. The completeness test removes every document and verifies the manual-review category."
      ],
      [
        "Commit decisions with their evidence",
        "SQLite writes the case revision and audit snapshot in one transaction. A stale revision is rejected. The workflow test corrects an address, approves the case and verifies that the original mismatch survives."
      ]
    ],
    "evaluation": [
      [
        "40 reproducible starting cases",
        "Generated individual and business records exercise missing documents, expiry and mismatched addresses. Seeded handling times are simulated."
      ],
      [
        "Correction and stale-write checks",
        "The automated workflow covers correction, approval, rejection of an invalid transition, stale edits and reopening. Browser verification also submitted a fresh synthetic case."
      ]
    ],
    "limits": "Selectable demo reviewers provide attribution inside the simulation. Production deployment would require authenticated actors, enforced roles, retention rules and independently protected logs.",
    "next": [
      [
        "Strengthen access control",
        "Authenticate reviewers and enforce permissions at each transition."
      ],
      [
        "Measure review effort",
        "Track real handling intervals separately from time spent waiting for applicant information."
      ]
    ],
    "verify": "Open case 40, inspect its expired identity and mismatched address, then use the intake simulator to submit a clean business case. Record a reasoned decision and inspect its audit snapshot.",
    "flow": [
      "Intake packet",
      "Field extraction",
      "Validation",
      "Human decision",
      "Audit snapshot"
    ],
    "tools": [
      "Python",
      "SQLite",
      "Pandas",
      "Streamlit"
    ],
    "source": "media/aegis.zip",
    "reproduceIntro": "Extract the project ZIP and open its directory in a terminal with Python 3.13.",
    "commands": "python3 -m venv .venv\nsource .venv/bin/activate\npython -m pip install -r requirements.txt\npython -m pytest -q\nstreamlit run app.py",
    "credit": "AI coding tools assisted implementation and testing. The examples are synthetic."
  }
]);
