# 04 · Self-Consistency

> Technique reference. Part of the [Prompt Engineering Handbook](../README.md).

## Theory

Self-consistency improves on plain [chain-of-thought](../03-chain-of-thought/README.md) by sampling the same prompt many times at a non-zero temperature and then taking the answer that appears most often. The insight is that a hard problem usually has many valid reasoning paths that converge on the correct answer, but only scattered, uncorrelated ways of being wrong. Greedy single-shot decoding commits to one path and rides it to whatever conclusion it reaches; sampling several independent paths and voting lets the correct answer win by agreement.

Concretely: send the prompt N times (say 5 to 40) with temperature high enough to produce diverse reasoning (often 0.5 to 0.8), extract the final answer from each completion, and return the majority (the mode). It reliably lifts accuracy on arithmetic, commonsense, and symbolic reasoning benchmarks over a single CoT sample, at the cost of N times the tokens and latency.

Self-consistency only works when answers are comparable and countable so votes can be tallied: a number, a label, a short canonical string. It does not apply to open-ended generation like essays or code, where there is no single answer to vote on. Reach for it when correctness matters more than cost and the task has a well-defined answer.

## Example Prompt

```text
Answer the question. Think step by step, then give the final answer on a new
line prefixed with "Answer:".

Q: A tank holds 240 litres and starts full. It drains at 8 litres per minute
for 6 minutes, then is refilled at 20 litres per minute for 4 minutes. How
many litres are in the tank now?
```

Run this prompt 5 times at temperature 0.7 and tally the `Answer:` lines.

## Output

```text
Sample 1 -> Answer: 272
Sample 2 -> Answer: 272
Sample 3 -> Answer: 232   (forgot the tank starts full)
Sample 4 -> Answer: 272
Sample 5 -> Answer: 272

Majority vote: 272  (4 of 5)
```

*(Model: representative of a modern instruction-tuned chat model, temperature 0.7.)* Four samples reach 272 (240 - 48 + 80) by slightly different phrasings of the same arithmetic; one sample slips on a sub-step. Majority voting discards the outlier and returns the correct answer, which a single greedy sample might have missed.

## Best Practices

- **Use a non-zero temperature** (roughly 0.5 to 0.8) so paths genuinely diverge; temperature 0 makes all samples identical and defeats the method.
- **Force an easily extractable final answer** (an `Answer:` line, a JSON field) so votes can be parsed and tallied automatically.
- **Normalize before counting** — trim whitespace, lowercase, round numbers to a canonical form — so equivalent answers vote together.
- **Pick N to balance cost and confidence**; accuracy climbs fast then plateaus, so 5 to 10 samples often capture most of the gain.
- **Track the vote margin** as a cheap confidence signal: a near-tie means the model is genuinely unsure.
- **Combine with chain-of-thought** — the reasoning diversity is what makes voting effective.

## Common Mistakes

- **Sampling at temperature 0**, producing N identical completions and no diversity to vote over.
- **Applying it to open-ended tasks** (prose, code, design) where there is no single answer to count.
- **Voting over too few samples**, so noise dominates and the majority is unstable.
- **Failing to normalize answers**, so `272`, `272 litres`, and `272.0` split the vote and none wins.
- **Ignoring the cost multiplier** — N samples means roughly N times the tokens, latency, and price.
- **Trusting a razor-thin majority** as if it were a confident answer.
