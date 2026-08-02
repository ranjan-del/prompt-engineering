# 09 · Prompt Chaining

> Technique reference. Part of the [Prompt Engineering Handbook](../README.md).

## Theory

Prompt chaining decomposes a complex task into a pipeline of smaller prompts, where the output of one step becomes the input to the next. Rather than asking a single mega-prompt to extract, analyze, and format all at once, you run a focused prompt per subtask. Each step does one thing well, is easy to inspect and test in isolation, and can use a model, temperature, or format suited to its job.

Chaining raises reliability because each prompt has a narrow, well-specified task, and it gives you checkpoints: you can validate, retry, or repair a step's output before it flows downstream, instead of debugging one opaque all-in-one response. It also enables control flow: branching on an intermediate result, looping until a condition holds, or fanning out to parallel steps and merging. This is the backbone of many LLM applications: extract then summarize, classify then route, draft then critique then revise.

The trade-off is more calls (higher latency and cost) and the risk of error propagation: a mistake in an early step contaminates everything after it. Mitigate this by validating between steps and keeping each step's contract explicit. Chaining differs from [ReAct](../05-react/README.md): a chain is a predetermined sequence of prompts you orchestrate, whereas ReAct lets the model decide its next action dynamically.

## When to Use It

- **One prompt is doing three jobs** and quality drops on all of them. Split it.
- **You need a checkpoint mid-task**: validate, repair, or ask a human before the result flows on.
- **Different steps want different settings.** Cheap fast model for extraction, stronger model for judgement, temperature 0 for formatting.
- **The steps are known in advance.** A fixed pipeline is the right tool when the sequence does not depend on intermediate results.
- **You need to know which stage failed.** Per-step logging turns "the output was wrong" into "step 2 misclassified".
- **Fan-out work**: one extraction produces N items, and each item is processed independently and in parallel.

## When Not to Use It

- **A single prompt already does the job well.** Each extra step is latency, cost, and a new place to fail.
- **The next action depends on what the model discovers.** That is dynamic control flow and belongs in a [ReAct](../05-react/README.md) loop, not a fixed chain.
- **Steps cannot be validated.** The value of chaining is catching errors between stages. Without checks you have just made error propagation more expensive.
- **The pipeline is latency-critical.** Five sequential calls means five round trips, and users feel every one.
- **Splitting destroys context** the later steps need. Some tasks genuinely require seeing everything at once, and a summarize-then-analyze chain throws away the detail the analysis needed.
- **You are decomposing to twelve steps.** Over-decomposition compounds per-step error rates: ten steps at 97 percent each is about 74 percent end to end.

## Example Prompt

```text
Step 1 (extract):
  "List every distinct product mentioned in the review below, one per line.
   Review: <review text>"

Step 2 (classify, run per product from Step 1):
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

*(Model: representative of a modern instruction-tuned chat model.)* Each stage has a single job: extraction, then per-item classification, then formatting. The intermediate lists are inspectable, and the final structured result is assembled only after the earlier steps are validated, so a bad extraction can be caught before it corrupts the output.

## Before and After

**Before (one mega-prompt):**

```text
Read this review, find all the products mentioned, work out the sentiment
toward each one, and give me a JSON array of objects with product and
sentiment. Also make sure the sentiment is only POSITIVE, NEGATIVE or NEUTRAL.

Review: <long multi-product review text>
```

What goes wrong: the model is juggling extraction, per-item classification, and
serialization in one pass, and quality degrades on all three. It reliably
misses the third and fourth products mentioned late in a long review, because
attention to the extraction subtask fades as it starts composing JSON. When the
output is wrong you get one opaque blob and no way to tell whether the product
was never extracted or was extracted and then misclassified. And there is
nowhere to insert a check: the array is the first thing you see.

**After (three narrow steps with a gate between each):**

```python
# Step 1 runs at temperature 0 on a cheap model: extraction is a mechanical
# task and creativity is a defect here.
products = extract_products(review)          # -> ["Acme Router", "ZenPhone"]

# Gate. An empty extraction is a real outcome (a review may name no product),
# but a 40-item extraction from a 3-line review means step 1 hallucinated,
# and we must not spend 40 classification calls proving it.
if len(products) > MAX_PRODUCTS:
    raise PipelineError(f"step 1 extracted {len(products)} products")

# Step 2 fans out: one focused classification per product, run in parallel.
# Each call sees the full review, so no context is lost by the split.
pairs = [(p, classify_sentiment(review, p)) for p in products]

# Gate. Reject anything outside the label set before it reaches the formatter,
# rather than discovering an invalid enum value in the database next week.
for product, sentiment in pairs:
    assert sentiment in {"POSITIVE", "NEGATIVE", "NEUTRAL"}, sentiment

# Step 3 is pure serialization and does not need a model call at all.
result = [{"product": p, "sentiment": s} for p, s in pairs]
```

Why it is better: each model call now has exactly one job, so the extraction
prompt is not competing with the formatting instructions for attention.
Classification is per product, which means the model considers one entity at a
time instead of tracking four in parallel, and those calls run concurrently so
the fan-out costs little wall-clock time. The gates catch a bad step before it
contaminates the next one, and the failure message names the stage. Note step 3
disappeared entirely: once the pieces are validated, building the JSON is
ordinary code, and a chain step that a list comprehension can do should not be
a model call.

## Best Practices

- **Give each step one narrow responsibility** and a clear input/output contract.
- **Validate between steps**: check the intermediate output before feeding it forward, and retry or repair on failure.
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
- **Using a rigid chain when the task needs dynamic decisions**: that is a job for an agentic loop like ReAct, not a fixed pipeline.
