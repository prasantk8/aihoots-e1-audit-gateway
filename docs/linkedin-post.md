LINKEDIN POST — E1 (condensed distribution version)
Paste into LinkedIn; the domain post is the archive, this is the reach.
─────────────────────────────────────────────────────────

Every AI regulation asks for the same thing: prove what your AI was asked, what it
answered, and what controls acted on it.

Most teams meet this with ordinary logs. But ordinary logs have a fatal flaw for
audit: whoever runs the system can edit them. An audit trail you can silently
rewrite isn't evidence — it's a diary.

So I built the control that closes the gap: a tamper-evident LLM audit gateway.

An OpenAI-compatible proxy that sits in front of any model and records every
request, response, and policy decision in a hash-chained log. Change one historical
record and an independent verifier catches exactly which one. No blockchain, no key
management — just the right old idea applied well.

Two things I'm keeping honest about it:

1) It ships with the security pipeline it deserves — SAST, dependency + secret
scanning, SBOM, non-root container. Governed AI, built with governed engineering.

2) My own tests caught a real bug: my prompt-injection blocklist missed "ignore ALL
PREVIOUS instructions" — the most common jailbreak phrasing — because of a lazy
regex. The integration test failed, I fixed it. Your guardrail is only as good as
the adversarial cases you actually test.

It's the first episode of AIHOOTS — a build-in-public lab where I build AI
governance as working, reproducible systems instead of slideware. Full code + a
rebuild-it-yourself guide in the repo.

Would you run something like this in front of your LLMs? What would you want it to
catch?

[link to aihoots.com post]  [link to GitHub repo]

#AIGovernance #LLM #DevSecOps #AISafety #MLOps
