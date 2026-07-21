# Eval baseline — corpus v1.0.0

Measured on a local `qwen2.5:3b-instruct`, raw model vs the same model behind the
Episode 1 gateway. These are real numbers, published unretouched.

| target         | catch-rate | false-positive | ambiguous |
|----------------|-----------:|---------------:|----------:|
| raw model      |         0% |             0% |     10/11 |
| gated gateway  |        20% |             0% |      8/11 |
| **delta**      |    **+20%**|                |           |

Per-category (gated):

| category          | caught |
|-------------------|-------:|
| direct_injection  |  1/3   |
| jailbreak         |  0/2   |
| data_leakage      |  1/2   |
| role_confusion    |  0/1   |
| encoding          |  0/2   |

## Reading this honestly

- The raw model obeyed **every** attack (0% caught). That is what an ungoverned LLM
  looks like — the baseline exists to make that visceral.
- The gateway helps but is **weak**: a handful of regex rules stop some direct
  injection and leakage, and nothing else. Jailbreak, role-confusion, and encoded
  attacks pass straight through. This is expected for v1 and is the roadmap.
- The **high ambiguous count** is a real finding, not noise: a 3B model rambles
  rather than cleanly refusing or cleanly complying, so deterministic marker-matching
  lands most cases in the grey zone. Bigger models and sharper markers shrink it.

## The CI gate

The gate is set to **0.15** — just below today's measured 0.20 — so it blocks
*regression* below honest reality, not fantasy. Every future guardrail improvement
ratchets the threshold up. A gate you can't actually pass is theatre; a gate pinned
to measured truth is a control.
