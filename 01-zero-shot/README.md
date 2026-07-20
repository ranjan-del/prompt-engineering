# 01 · Zero-Shot Prompting

> Technique reference. Part of the [Prompt Engineering Handbook](../README.md).

## Theory

Zero-shot prompting asks a model to perform a task using instructions alone, with no worked examples included in the prompt. The model relies entirely on knowledge and task patterns absorbed during pretraining plus the clarity of your instruction. It is the simplest and cheapest technique: one message, one response, minimal token overhead.

Zero-shot works well when the task is common (summarization, translation, classification into obvious categories, reformatting), when the output format is easy to describe in words, and when you do not have representative examples on hand. It tends to struggle when the task is niche, when the desired output style is idiosyncratic, or when category boundaries are subtle. In those cases move to [few-shot](../02-few-shot/README.md).

Reach for zero-shot first. Add examples only when zero-shot output is measurably wrong, because examples cost tokens and can accidentally bias the model toward the surface form of the samples you picked.

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
