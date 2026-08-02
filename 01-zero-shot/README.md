# 01 · Zero-Shot Prompting

> Technique reference. Part of the [Prompt Engineering Handbook](../README.md).

## Theory

Zero-shot prompting asks a model to perform a task using instructions alone, with no worked examples included in the prompt. The model relies entirely on knowledge and task patterns absorbed during pretraining plus the clarity of your instruction. It is the simplest and cheapest technique: one message, one response, minimal token overhead.

Zero-shot works well when the task is common (summarization, translation, classification into obvious categories, reformatting), when the output format is easy to describe in words, and when you do not have representative examples on hand. It tends to struggle when the task is niche, when the desired output style is idiosyncratic, or when category boundaries are subtle. In those cases move to [few-shot](../02-few-shot/README.md).

Reach for zero-shot first. Add examples only when zero-shot output is measurably wrong, because examples cost tokens and can accidentally bias the model toward the surface form of the samples you picked.

## When to Use It

- **The task is common in pretraining data**: summarization, translation, tone rewriting, obvious-category classification, format conversion.
- **The output format is easy to state in words** ("one uppercase label", "three bullets", "a single number").
- **You have no representative examples yet**, or you are still exploring whether the model can do the task at all.
- **Token budget or latency is tight** and every example you add is context you pay for on every call.
- **You need a baseline.** Even when you expect to end up with few-shot, measure zero-shot first so you know what the examples actually bought you.

## When Not to Use It

- **The task is niche or house-specific** (your internal taxonomy, your style guide, your ticket schema). The model has never seen it, so show it: use [few-shot](../02-few-shot/README.md).
- **The output shape is easier to show than to describe.** If your format spec is three paragraphs long, one example replaces all of it.
- **Category boundaries are subtle** and the disagreement is about where the line sits, not what the labels mean. Examples move the line; adjectives do not.
- **The task needs multi-step reasoning** (arithmetic, constraint puzzles, code tracing). Use [chain-of-thought](../03-chain-of-thought/README.md).
- **The answer depends on facts the model cannot know** (today's data, your database, private documents). No amount of prompting fixes missing information: retrieve it, or use tools via [ReAct](../05-react/README.md).
- **You need machine-parseable output with guarantees.** A prose instruction is a request, not a contract. Use [JSON mode](../06-json-mode/README.md) or [structured output](../07-structured-output/README.md).

## Example Prompt

```text
Classify the sentiment of the following customer review as exactly one of:
POSITIVE, NEGATIVE, or NEUTRAL. Respond with only the single label, uppercase,
and nothing else.

Review: "The delivery was three days late, but the product itself works fine."
```

## Output

```text
NEUTRAL
```

*(Model: representative of a modern instruction-tuned chat model.)* The review mixes a negative delivery experience with a positive product experience, so NEUTRAL is the reasonable single-label answer. Because the instruction constrained the output to one word, the model returned exactly one token of content with no explanation.

## Before and After

**Before (vague):**

```text
What do you think about this review?

"The delivery was three days late, but the product itself works fine."
```

What goes wrong: no task, no label set, no format. The model has to guess what
"what do you think" means, and it usually answers with a paragraph of hedged
commentary. Two runs produce two different shapes, so nothing downstream can
parse it, and there is no label to compare against a ground-truth column.

**After (specific):**

```text
Classify the sentiment of the following customer review as exactly one of:
POSITIVE, NEGATIVE, or NEUTRAL.

Rules:
- Weigh the reviewer's opinion of the product, not the logistics.
- If positive and negative signals are balanced, respond NEUTRAL.
- Respond with only the single label, uppercase, and nothing else.

Review: "The delivery was three days late, but the product itself works fine."
```

Why it is better: four things changed. The verb became a specific operation
("classify"), the output space became a closed set of three labels, the
tie-breaking rule removed the ambiguity that made this review hard, and the
format constraint made the response a single parseable token. Notice that the
tie-break rule is doing real work here: without it, POSITIVE and NEUTRAL are
both defensible and the model will flip between them across runs.

## Best Practices

- **State the task, the allowed outputs, and the format explicitly.** "Respond with only the label" prevents chatty preambles.
- **Enumerate categories** for classification so the model cannot invent new ones.
- **Give the model a role or context** when it changes behavior ("You are a strict JSON linter").
- **Specify what to do with edge cases** ("If the review has no sentiment, respond NEUTRAL").
- **Put the instruction before the data**, and delimit the data clearly (quotes, triple backticks, XML-style tags) so the model does not confuse instructions with content.
- **Keep it minimal first**, then add constraints only for the failure modes you actually observe.

## Common Mistakes

- **Assuming the model infers unstated constraints.** If you need lowercase, JSON, or a word limit, say so.
- **Vague verbs.** "Analyze this" produces unpredictable shape; "List three risks, one sentence each" does not.
- **Leaving output format open**, then being surprised by an essay when you wanted one word.
- **Mixing instructions and data without delimiters**, letting user content override your instruction (a prompt-injection risk).
- **Using zero-shot for genuinely hard or ambiguous tasks** and blaming the model instead of switching to few-shot or chain-of-thought.
- **Rewriting the whole prompt when one line is wrong.** Change a single variable at a time, or you cannot tell which edit moved the result.
