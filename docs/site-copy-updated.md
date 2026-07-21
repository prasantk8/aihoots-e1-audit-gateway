AIHOOTS SITE COPY — updated plain-language version
These are the text blocks to update on ai.aihoots.com.
Replace the existing section text with the versions below.
──────────────────────────────────────────────────────────

=== HERO ===

Eyebrow:   // AI governance, built in the open

Headline:  Proof, not slideware.

Subline:   Most AI governance advice comes in slide decks.
           This is the version where I actually build the systems,
           test them until they fail, and publish the real numbers.
           Including the embarrassing ones.

Button 1:  See the work →
Button 2:  Read the code

=== SECTION: WHAT ===

Kicker: THE PROBLEM WORTH SOLVING

Headline: "We have AI guardrails" is a claim.
          Claims drift.

Body: A model gets swapped. A regex gets refactored. A prompt gets tweaked.
      And the guardrail you were relying on quietly stops working, with nothing
      to tell you.

      AIHOOTS is a lab that builds the controls — audit trails, detection,
      evaluation — that turn "we think we're safe" into "here's what we measured."
      Built in the open, rebuilt-by-a-stranger verified, and honest about what
      the numbers actually say.

Cards (keep three, update text):

  Card 1 title: Working systems, not decks
  Card 1 body:  Every episode is something that runs. You can clone it,
                docker compose up, and watch it work — or fail — yourself.

  Card 2 title: Honest numbers
  Card 2 body:  My guardrails scored 20% on an adversarial test. That's in
                the article. The AI industry defaults to polished benchmarks;
                this is what it looks like to measure honestly.

  Card 3 title: Reproducible by design
  Card 3 body:  Every system comes with a step-by-step rebuild guide.
                If a stranger can't follow it on a clean machine, it's not done.

=== SECTION: PRINCIPLES ===

Kicker: HOW THIS WORKS

Headline: Build it completely. Then explain it honestly.

Body: Nothing gets announced before it works. No "coming soon." The pattern is:
      build the whole thing, measure it (including the embarrassing results),
      document every decision and its alternatives, then publish.

Cards:
  BUILD:   End to end, privately — gateway + model in a container, CI green,
           security gates passing.
  VERIFY:  A stranger on a clean machine follows the rebuild guide.
           If it breaks, it goes back for a fix.
  MEASURE: The system is attacked. The catch-rate is published, whatever it is.
  PUBLISH: The code, the numbers, and the story — together.

=== SECTION: EPISODES ===

Kicker: EPISODES

Headline: Each one is a complete system. Each one is honest about its limits.

Episode 1: LLM Audit Gateway
  A proxy that records every AI interaction in a tamper-evident log —
  the kind where changing one record immediately names itself. Found and
  fixed a real injection-detection bug along the way.
  Status: ● LIVE

Episode 1+: Your audit log is a security dataset
  The same log, now running four statistical detectors for anomalous
  behaviour. Caught two real stats bugs using its own evaluation harness.
  (Zero machine learning. All explainable to a human.)
  Status: ● LIVE

Episode 2: Testing your guardrails on every commit
  An adversarial eval harness. 9 attacks, two targets: raw model (0% caught)
  vs the gated gateway (20% caught). Published the real numbers.
  The CI gate now fails if the catch-rate regresses below today's reality.
  Status: ● LIVE

Episode 3: Governing an Autonomous Agent  [coming]
  A real agent framework — running locally, freshly installed — put behind
  the gateway. Before/after adversarial defense rates. Public methodology.
  Status: planned

=== FOOTER ===

AIHOOTS is a build-in-public lab for AI governance.
Views and projects are the author's own and are not connected to,
representative of, or derived from any employer's systems.
