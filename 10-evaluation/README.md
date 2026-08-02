# 10 · Evaluation

> Technique reference. Part of the [Prompt Engineering Handbook](../README.md).

## Theory

Evaluation is how you measure whether a prompt actually works, replacing "it looked good when I tried it once" with repeatable evidence. You assemble a dataset of representative inputs (and, where possible, expected outputs), run the prompt over all of them, and score the results against explicit criteria. Without this, prompt changes are guesswork: an edit that fixes one case can quietly break five others, and you would never know.

Scoring methods fall on a spectrum. **Deterministic checks** are cheapest and most reliable when the task has a right answer: exact match, numeric tolerance, regex, JSON-schema validity, or a unit-test-style assertion. **Reference-based metrics** compare against a gold answer for fuzzier tasks. **LLM-as-judge** uses a separate model call with a rubric to grade open-ended outputs (helpfulness, faithfulness, tone) that no simple metric captures; it is flexible but must itself be calibrated against human judgment, because judges have biases (favoring longer answers, or their own style). **Human review** remains the ground truth for high-stakes or subjective quality.

Treat evaluation as a permanent test suite, not a one-off. Hold out the examples you grade on from the ones you used to design the prompt, so you measure generalization rather than memorization. Track a few aligned metrics over time, and re-run the suite on every prompt or model change to catch regressions before they ship.

## When to Use It

- **Always, once a prompt is in production.** Any prompt real users depend on needs a regression suite, exactly like any other code path.
- **Before and after every prompt change.** Without a baseline you cannot tell an improvement from a lateral move.
- **When changing model or provider.** A prompt tuned on one model is not portable, and the evaluation suite is how you find out what broke.
- **When choosing between approaches.** Zero-shot versus few-shot is an empirical question, and one anecdote does not answer it.
- **When you need to justify a decision** to someone else. "Accuracy went from 71 to 88 percent on 200 held-out cases" ends an argument that opinion cannot.

## When Not to Use It

There is no case for shipping a production prompt unmeasured, but the *method*
should match the stakes:

- **Skip formal evaluation for genuinely throwaway work**: a one-off script, an exploratory question. Building a test set costs more than the task is worth.
- **Do not use LLM-as-judge where a deterministic check works.** If the answer is a number or a label, compare it. A judge is slower, costs money, and introduces its own error.
- **Do not use an uncalibrated judge on high-stakes output.** Medical, legal, and safety decisions need human review, not a model grading a model.
- **Do not evaluate against a test set you also tuned on.** That number is memorization and it will not survive contact with real traffic.
- **Do not build an elaborate harness before you have a working prompt.** Get something that functions, then measure it.
- **Do not chase a metric that does not track what users care about.** A rising score on a proxy metric while user complaints rise is a sign the metric is wrong, not the users.

## Example Prompt

```text
You are grading a customer-support reply. Score it 1-5 on each criterion and
return JSON with keys "accuracy", "tone", "completeness", and "reason".

Rubric:
- accuracy: is the information correct and on-topic?
- tone: is it polite and professional?
- completeness: does it fully address the question?

Question: "How do I reset my password?"
Reply to grade: "Click 'Forgot password' on the login page and follow the
emailed link. Let me know if you need anything else!"
```

## Output

```json
{
  "accuracy": 5,
  "tone": 5,
  "completeness": 4,
  "reason": "Correct, polite, and actionable; loses one point for not noting the reset link expires."
}
```

*(Model: representative of a modern instruction-tuned chat model used as an LLM judge.)* The rubric forces the judge to score fixed dimensions rather than give a vague overall impression, and the `reason` field makes the score auditable so you can spot when the judge itself is miscalibrated.

## Before and After

**Before (a vague judge prompt):**

```text
Is this a good customer support reply? Rate it out of 10.

Question: "How do I reset my password?"
Reply: "Click 'Forgot password' on the login page and follow the emailed link.
Let me know if you need anything else!"
```

What goes wrong: "good" is undefined, so the judge invents its own criteria and
a different set on every call. Scores are not reproducible, and because the
scale has no anchors, an 8 from one run is not comparable to an 8 from another.
There is no justification, so you cannot tell whether the judge penalized a real
gap or simply preferred longer answers, which is a well-documented judge bias.
Worst of all, a single number averages away the dimension you actually care
about: this reply might be perfectly accurate but incomplete, and 8/10 hides
that completely.

**After (anchored rubric, per-dimension scores, reason first):**

```text
You are grading a customer-support reply against a rubric. Score each
criterion on the 1-5 scale defined below. Be strict: 5 means nothing could
reasonably be improved.

accuracy     1 = factually wrong  3 = partly correct  5 = fully correct and on-topic
tone         1 = rude or robotic  3 = neutral         5 = polite and professional
completeness 1 = ignores the ask  3 = partial answer  5 = fully resolves the question

Judge only against the rubric. Do not reward length, formatting, or
enthusiasm. Write the reason BEFORE the scores.

Return JSON with keys "reason" (string), then "accuracy", "tone",
"completeness" (integers 1-5).

Question: "How do I reset my password?"
Reply to grade: "Click 'Forgot password' on the login page and follow the
emailed link. Let me know if you need anything else!"
```

Why it is better: each criterion has a named scale with anchored endpoints and a
midpoint, so scores mean the same thing across runs and across graders. Scoring
three dimensions separately surfaces that completeness is the weak axis rather
than burying it in an average. The explicit instruction not to reward length
targets a known judge bias head on. Putting `reason` first in the JSON matters
more than it looks: the judge writes its justification before committing to
numbers, which is [chain-of-thought](../03-chain-of-thought/README.md) applied
to grading, and it also gives you an audit trail for spotting a miscalibrated
judge. The structured output means results go straight into a table you can
track per release.

**Calibration is not optional.** Before trusting this at scale, have a human
grade 50 of the same items and check the agreement. If the judge and the human
diverge systematically, fix the rubric rather than the humans.

## Best Practices

- **Build a held-out test set** separate from the examples used to design the prompt, so you measure generalization.
- **Prefer deterministic checks** (exact match, schema validity, numeric tolerance) wherever the task allows; they are cheap and unambiguous.
- **Write an explicit rubric for LLM-as-judge** with defined scales and criteria, and ask the judge to justify each score.
- **Calibrate the judge against human labels** on a sample before trusting it at scale.
- **Re-run the full suite on every change** to prompt, model, or parameters, and track metrics over time to catch regressions.
- **Report per-category results, not just an average**, so a failure mode in one slice is not hidden by strong performance elsewhere.

## Common Mistakes

- **Grading on the same examples used to design the prompt**, which measures memorization, not real performance.
- **Judging by eyeballing a handful of outputs** instead of scoring a representative set.
- **Trusting an uncalibrated LLM judge**, inheriting its biases (length preference, self-preference) as if they were quality.
- **Using a single vague metric** that averages away the specific failures you most need to see.
- **Never re-running evaluation**, so silent regressions from a prompt or model update reach production.
- **Testing only happy-path inputs**, missing edge cases, adversarial prompts, and empty or malformed data.
