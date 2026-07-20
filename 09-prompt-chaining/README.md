# 09 · Prompt Chaining

> Technique reference. Part of the [Prompt Engineering Handbook](../README.md).

## Theory

Prompt chaining decomposes a complex task into a pipeline of smaller prompts, where the output of one step becomes the input to the next. Rather than asking a single mega-prompt to extract, analyze, and format all at once, you run a focused prompt per subtask. Each step does one thing well, is easy to inspect and test in isolation, and can use a model, temperature, or format suited to its job.

Chaining raises reliability because each prompt has a narrow, well-specified task, and it gives you checkpoints: you can validate, retry, or repair a step's output before it flows downstream, instead of debugging one opaque all-in-one response. It also enables control flow — branching on an intermediate result, looping until a condition holds, or fanning out to parallel steps and merging. This is the backbone of many LLM applications: extract then summarize, classify then route, draft then critique then revise.

The trade-off is more calls (higher latency and cost) and the risk of error propagation: a mistake in an early step contaminates everything after it. Mitigate this by validating between steps and keeping each step's contract explicit. Chaining differs from [ReAct](../05-react/README.md): a chain is a predetermined sequence of prompts you orchestrate, whereas ReAct lets the model decide its next action dynamically.

## Example Prompt

```text
Step 1 (extract):
  "List every distinct product mentioned in the review below, one per line.
   Review: <review text>"

Step 2 (classify — run per product from Step 1):
  "Classify the sentiment toward {product} in this review as
   POSITIVE / NEGATIVE / NEUTRAL. Reply with only the label.
   Review: <same review text>"

Step 3 (format):
  "Turn these product/sentiment pairs into a JSON array of
   {product, sentiment} objects: <pairs from Step 2>"
```

## Output

```text
Step 1 output:
  Acme Router
  ZenPhone

Step 2 output:
  Acme Router  -> NEGATIVE
  ZenPhone     -> POSITIVE

Step 3 output (final):
[
  { "product": "Acme Router", "sentiment": "NEGATIVE" },
  { "product": "ZenPhone",   "sentiment": "POSITIVE" }
]
```

*(Model: representative of a modern instruction-tuned chat model.)* Each stage has a single job — extraction, then per-item classification, then formatting. The intermediate lists are inspectable, and the final structured result is assembled only after the earlier steps are validated, so a bad extraction can be caught before it corrupts the output.

## Best Practices

- **Give each step one narrow responsibility** and a clear input/output contract.
- **Validate between steps** — check the intermediate output before feeding it forward, and retry or repair on failure.
- **Use structured output at hand-off points** so the next step parses the previous one reliably.
- **Match the model and settings to each step** (a cheap fast model for extraction, a stronger one for reasoning; low temperature for formatting).
- **Log intermediate outputs** so you can see exactly which step failed when the final result is wrong.
- **Keep the pipeline as short as the task allows**; every extra step adds latency, cost, and a new failure point.

## Common Mistakes

- **Propagating errors unchecked**, so a wrong early step silently corrupts the final answer.
- **Loose hand-offs** where a step emits free text the next step cannot parse.
- **Over-decomposing** into so many steps that latency and cost balloon for little quality gain.
- **No logging of intermediates**, making failures impossible to diagnose.
- **Passing too much context forward**, letting stale or irrelevant data from early steps confuse later ones.
- **Using a rigid chain when the task needs dynamic decisions** — that is a job for an agentic loop like ReAct, not a fixed pipeline.
