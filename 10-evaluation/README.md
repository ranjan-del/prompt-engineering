# 10 · Evaluation

> Technique reference. Part of the [Prompt Engineering Handbook](../README.md).

## Theory

Evaluation is how you measure whether a prompt actually works, replacing "it looked good when I tried it once" with repeatable evidence. You assemble a dataset of representative inputs (and, where possible, expected outputs), run the prompt over all of them, and score the results against explicit criteria. Without this, prompt changes are guesswork: an edit that fixes one case can quietly break five others, and you would never know.

Scoring methods fall on a spectrum. **Deterministic checks** are cheapest and most reliable when the task has a right answer: exact match, numeric tolerance, regex, JSON-schema validity, or a unit-test-style assertion. **Reference-based metrics** compare against a gold answer for fuzzier tasks. **LLM-as-judge** uses a separate model call with a rubric to grade open-ended outputs (helpfulness, faithfulness, tone) that no simple metric captures; it is flexible but must itself be calibrated against human judgment, because judges have biases (favoring longer answers, or their own style). **Human review** remains the ground truth for high-stakes or subjective quality.

Treat evaluation as a permanent test suite, not a one-off. Hold out the examples you grade on from the ones you used to design the prompt, so you measure generalization rather than memorization. Track a few aligned metrics over time, and re-run the suite on every prompt or model change to catch regressions before they ship.

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
