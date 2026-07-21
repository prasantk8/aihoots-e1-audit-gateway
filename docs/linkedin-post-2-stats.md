LINKEDIN POST 2 — The Stats Module (E1 bonus)
Tone: the natural "then what happened" follow-up. Teaches something real. Enjoyable.
──────────────────────────────────────────────────

After I built the audit gateway (previous post), I had a log full of data and a
question: can I make it *detect* things automatically?

Not with machine learning. With boring statistics.

Here's the thing about running AI in a real environment: you don't need a neural
network to spot something going wrong. You need to notice when things start
*looking different*.

Block rate suddenly tripled? Either you're under attack, or a control broke.
Prompts getting significantly longer? Classic sign of injection payloads — real
questions are short, attack payloads are walls of text.
One user doing 10x more requests than everyone else? That's the oldest abuse
signal in the book.
Response times splitting into two groups? Something changed underneath.
A model got swapped. A cache broke. Something is degrading.

These aren't exotic detections. They're z-scores and medians. Stuff invented
in the 1800s. And they're *explainable* — which matters enormously when someone
asks "why did this alert fire?" in a regulated environment. You can answer.

(Try explaining why a neural network flagged something. Then try explaining
"the average prompt length jumped 8 standard deviations above baseline."
One of those answers gets you out of the meeting faster.)

The interesting part wasn't building it. It was when my own evaluation harness
caught two real bugs in the statistics themselves.

Bug 1: when all baseline prompts were the same length, the standard deviation
was zero, and dividing by zero silently returned "nothing to see here" —
*exactly* when the data was about to spike. A detector that goes blind on clean
data is worse than no detector.

Bug 2: the outlier-masking problem. One abusive user with 10x the normal volume
*inflated the standard deviation* so much that their own z-score dropped below
the alarm threshold. The outlier was hiding inside the noise it created.

Both fixed by switching to robust statistics — medians and MAD instead of means
and standard deviations. Old solutions to old problems. The point is the tests
were there to catch it before it shipped.

#AIGovernance #Statistics #LLMSecurity #BuildingInPublic
