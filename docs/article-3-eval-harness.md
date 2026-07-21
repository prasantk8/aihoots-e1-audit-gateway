# Testing your LLM guardrails on every commit — with honest numbers

*Episode 02 of AIHOOTS. Episode 1 built a gateway that blocks attacks. This one
proves — measurably, repeatably — how well it actually works, by attacking a raw
model and the gated one and publishing the gap.*

---

"We have guardrails" is a claim. Claims drift. A model gets swapped, a prompt gets
tweaked, someone refactors a regex — and the guardrail you were relying on quietly
weakens, with nothing to tell you. In Episode 1, I shipped exactly that bug: a
prompt-injection filter that missed the most common attack phrasing because of a
lazy regex. A test caught it. That test was the seed of this whole episode.

Episode 2 industrialises that instinct: a **standing adversarial eval harness** that
fires a battery of attacks at an LLM and scores how many get through — and runs on
every commit, so a change that weakens your defences fails the build.

## The numbers — real, and not flattering

I ran the corpus against a local 3-billion-parameter model, twice: once raw, once
behind the Episode 1 gateway. Here is exactly what came back, unretouched:

- **Raw model: 0% of attacks caught.** It obeyed every single one — printed the
  secret, adopted the persona, followed the injection. Zero.
- **Gated gateway: 20% caught.** Better. Not good.

I'm publishing that 20% on purpose, because it's true and because it's more useful
than a number I'd have to fake. My guardrails are a handful of pattern rules; they
stop some blunt injection and some leakage, and jailbreaks, role-confusion, and
base64-encoded attacks walk right past them. The harness didn't fail by returning a
low number — it *succeeded*, by telling me precisely how weak my defences really are
and exactly which categories to fix next.

That is the entire argument for measuring instead of asserting. Every vendor deck
shows you 99%. I'm showing you 20% and a roadmap, and I'd bet the 20% earns more
trust — because you can see I'm not selling you anything.

## The raw baseline is the whole point

The interesting number was never either score on its own. It's the **delta**: 0% to
20%. That gap is what the gateway buys, measured. Without the raw baseline, "20%
caught" is a number floating in space. With it, you can see the shape of the problem:
a bare LLM is defenceless, a little governance helps a little, and real governance is
going to take real work. Honest framing beats a lonely statistic every time.

## The corpus

The attacks live in a versioned JSON corpus — because an eval score is meaningless
without the corpus version it was measured against. Version 1 covers direct
injection, jailbreak framings (persona and fictional), data-leakage and canary
extraction, role-confusion, and encoding tricks (base64 and character-delimiter
evasion), plus benign control prompts that measure the false-positive rate. Every
attack case declares a concrete **success marker** — a string that appears only if
the attack actually worked.

## Scoring honestly

How do you decide, deterministically, whether an attack "succeeded"? I refused to
use an LLM as judge — a second, non-deterministic model scoring the first is
unexplainable and unauditable. Instead the harness applies layered, deterministic
checks: was it blocked at the gate, did the model refuse, and — the decider — is the
success marker present in the response?

The part I'm proudest of is the **ambiguous bucket**. When an attack is neither
clearly stopped nor clearly successful, the harness does not quietly count it as a
win. It labels it ambiguous and reports the count separately. And on my run, that
count was *high* — most cases landed there, because a small 3B model tends to ramble
rather than cleanly refuse or cleanly comply, so my exact success-markers often
didn't match even when the attack basically worked. That's not a bug to hide; it's a
real finding about evaluating small models, and it's a paragraph in the write-up
rather than a number swept under the rug. Hiding it would be lying with statistics.

## As a CI gate

The harness runs from the command line and as a build gate. Point it at your raw
model and your gateway; it prints per-category catch-rates and the delta, and exits
non-zero if the gated catch-rate falls below a threshold you set and can defend. Wire
that into CI and guardrail regressions stop being something you discover in
production and start being something that fails a pull request.

## What it does not claim

The corpus only tests attacks I've thought of. A passing score means "resists known
attacks," not "unbreakable" — and I'd distrust anyone who claimed otherwise. The
value is in the *repeatability*: the same battery, every commit, with the misses
visible. Security is a moving target; this gives you a way to keep score as it moves.

Code and corpus: **github.com/prasantk8/aihoots-e1-audit-gateway** (`src/eval/`)

---

*AIHOOTS is a build-in-public lab for enterprise AI governance. Views and projects
here are my own and unrelated to any employer's systems.*
