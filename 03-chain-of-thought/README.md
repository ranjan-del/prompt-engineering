# 03 · Chain-of-Thought Prompting

> Technique reference. Part of the [Prompt Engineering Handbook](../README.md).

## Theory

Chain-of-thought (CoT) prompting asks the model to produce its intermediate reasoning steps before committing to a final answer. Instead of jumping straight to a conclusion, the model writes out the sub-steps, and this externalized reasoning measurably improves accuracy on arithmetic, logic, and multi-step problems. The gain comes from spending more computation across more tokens and from keeping partial results visible so later steps can build on earlier ones rather than being guessed in a single leap.

The classic trigger is appending "Let's think step by step" (zero-shot CoT), but you can also demonstrate the reasoning style with worked examples that each show their steps (few-shot CoT). CoT is most valuable when the task genuinely decomposes into stages: word problems, code tracing, constraint satisfaction, or any question where a naive one-shot answer is often wrong.

A practical caveat: exposed reasoning is verbose and can be wrong even when the final answer is right, so separate the reasoning from the answer and parse only the answer. Many modern "reasoning" models perform CoT internally, in which case forcing an explicit trace can be redundant. Reach for CoT when accuracy on hard, multi-step tasks matters more than latency and token cost. For even higher reliability, combine it with [self-consistency](../04-self-consistency/README.md).

## Example Prompt

```text
Answer the question. Think step by step, then give the final answer on a new
line prefixed with "Answer:".

Q: A shop sells pens in packs of 12. Maria buys 4 packs and gives away 9 pens.
She then buys 2 more packs. How many pens does she have now?
```

## Output

```text
Step 1: 4 packs x 12 = 48 pens.
Step 2: She gives away 9, leaving 48 - 9 = 39 pens.
Step 3: She buys 2 more packs: 2 x 12 = 24 pens.
Step 4: Total: 39 + 24 = 63 pens.
Answer: 63
```

*(Model: representative of a modern instruction-tuned chat model.)* Each arithmetic step is written out and carried forward, and the final count is isolated on the `Answer:` line so a caller can parse it with a simple regex.

## Best Practices

- **Ask for steps explicitly** ("think step by step", "show your working") when the task is genuinely multi-step.
- **Separate reasoning from the answer** with a clear delimiter (`Answer:`, a JSON field, or XML tags) so downstream code parses only the conclusion.
- **Use few-shot CoT** when you need a specific reasoning style: show 2 to 3 examples that each include their steps.
- **Let the model reason before it answers**, never after; a conclusion stated first anchors the reasoning to justify it.
- **Raise the token budget** so reasoning is not truncated mid-thought.
- **Prefer internal reasoning** on models built for it, and skip explicit CoT where it adds only cost.

## Common Mistakes

- **Using CoT for trivial tasks**, inflating latency and cost for no accuracy gain.
- **Trusting the reasoning trace as ground truth** — models can produce plausible but invalid steps that still land on the right (or wrong) answer.
- **Putting the answer before the reasoning**, which defeats the purpose and yields post-hoc rationalization.
- **Failing to isolate the final answer**, forcing brittle parsing of free-form text.
- **Showing inconsistent example formats** in few-shot CoT, so the model imitates a messy structure.
- **Leaking chain-of-thought to end users** when only the answer is wanted, exposing verbose or sensitive intermediate content.
