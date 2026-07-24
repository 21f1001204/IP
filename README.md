# IP-or-not + rights_asserted — all 951 cases

This replaces your old per-order IP classifier with a **case-level, evidence-forced** one. For each case it decides `ip_status` (yes / no / unclear) *from the evidence* — it does **not** assume the case is IP — and only then codes the rights.

```
ip_rights_run/
├── ip_and_rights_prompt.txt   the prompt (IP gate + rights, with worked examples)
├── prompts_full/              951 files — prompt + each case's orders, ready to pipe
├── run_all.sh                 run all 951 (resume-safe)   |  `bash run_all.sh test` = 8-case check first
├── parse_all.py               collate -> 3 CSVs
└── raw/                        one JSON answer per case (created on run)
```

Built from your canonical **`cases_order_text_combined.csv`** = **951 cases**:
- **768** your old classifier judged **IP** (and coded with rights),
- **183** your old classifier judged **non-IP** and dropped.

So re-running the 183 is an **audit of the old classifier's non-IP rejections** — the payoff is any case the new classifier flips to `yes` (an IP case wrongly excluded, to be recovered). (2 disk folders, CS_COMM_155 and CS_COMM_195, have no text and are excluded.)

## Run it (Claude Code, on your Pro subscription)

```
echo $ANTHROPIC_API_KEY          # must be empty (subscription, not API billing)
cd "<your path>/Claude_validation/outputs/ip_rights_run"

bash run_all.sh test             # 8 cases first — sanity check
python3 parse_all.py             # look at ip_rights_all.csv

bash run_all.sh                  # then all 951 (skips the 8 already done)
python3 parse_all.py
```

Resume-safe: it skips cases already done AND re-does any that errored or hit "Not logged in", so if you stop mid-way (usage limit, closed laptop) just run it again.

## What you get
- **`ip_rights_all.csv`** — every case: `ip_status`, `ip_evidence`, `rights_asserted`, `rights_evidence` (quote per flag), `notes`, `old_label`, plus OG comparison columns.
- **`ip_rights_RECOVERED_false_negatives.csv`** — ⭐ the key file: cases the old classifier dropped as non-IP but the new one says ARE IP. These are wrongly-excluded cases to add back (with their rights already coded).
- **`ip_rights_FALSE_POSITIVES.csv`** — the other direction: cases the old classifier kept as IP but the new one says are NOT. Review for removal.
- **`ip_rights_OLD_nonIP_reaudit.csv`** — the full 183 old-non-IP set with the new verdict for each.
- **`ip_rights_CHANGED.csv`** — previously-coded IP cases whose rights moved (with evidence + notes).

## Scale / cost on Claude Pro
951 case-level calls of ~8–11k tokens on **Sonnet** (the default). No per-token dollar charge — it draws from your shared Pro usage allowance (5-hour + weekly limits), so you will almost certainly hit the cap partway and finish across a few sessions. That's fine — it's resume-safe. Do **not** switch to Opus for a run this size on Pro; it won't fit the limits.

## After the run
- Cases with `ip_status = "no"` are genuine non-IP suits — drop them from the IP dataset (or keep flagged).
- Cases with `ip_status = "unclear"` are missing their opening/plaint order — fetch the first order from the Delhi HC portal, drop it into `orders/<case_id>/`, rebuild that one payload, and re-run just that case.
- Spot-check `rights_evidence` on any `passing_off` flag whose quote is deception-language only (no literal "passing off") — that's the one place the prompt reads generously.
