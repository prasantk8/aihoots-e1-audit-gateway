LINKEDIN POST 1 — The Gateway (E1)
Tone: a real person telling a real story. No jargon opener. No "I'm excited to share."
──────────────────────────────────────────────────

Here's a thing nobody talks about when companies rush to add AI:

The AI will do whatever you ask it to. Including things you didn't intend to allow.

Ask a corporate AI chatbot to "ignore its previous instructions" and — more often
than you'd think — it will. Ask it to repeat its system prompt back to you. Ask it
to pretend it's a different AI with no rules. These aren't exotic hacks. They're
the first things a curious teenager tries.

The industry answer is "add guardrails." Fine. But here's the unglamorous question
nobody asks: *how do you know your guardrails are actually working?*

I wanted to build the answer from scratch and show my work publicly. So I did.

I built an LLM audit gateway: a transparent layer that sits in front of any AI
model and records every single interaction in a tamper-evident log — the kind
where if you change one record, a verifier immediately tells you which one was
altered and when.

Think of it like a CCTV system for your AI. Except instead of footage that can be
deleted, every frame is cryptographically chained to the one before it. You can't
rewrite history without leaving fingerprints.

It also enforces basic rules — blocks injection attempts, strips out email
addresses and card numbers before they reach the model, logs every decision it
makes with a reason.

What I found interesting wasn't the working parts. It was the bugs my own tests
caught.

My injection detector was silently missing the most common attack phrase in
existence — "ignore all previous instructions" — because of a regex that only
matched *one* of the words "all" or "previous", not both. The guardrail looked
fine in a demo. It would have failed on the most basic real attack.

A test caught it. The test was more valuable than the guardrail.

Everything's built in the open: one command to run the whole stack, full security
pipeline (scanning, SBOM, the works), and a step-by-step rebuild guide that a
stranger on a clean machine can follow.

If you're building AI products in a regulated environment — banking, insurance,
healthcare — I think you'll find the design decisions interesting. The link is in
the comments.

#AI #AIGovernance #LLMSecurity #DevSecOps #BuildingInPublic
