# 02 · Few-Shot Prompting

> Technique reference. Part of the [Prompt Engineering Handbook](../README.md).

## Theory

Few-shot prompting includes a small number of worked examples (input plus desired output) directly in the prompt before the real input. The examples demonstrate the task, the output format, the tone, and the decision boundaries, letting the model pattern-match rather than guess. This is in-context learning: no weights change, but the model conditions its next response on the demonstrations you provide.

Few-shot is the right step up from [zero-shot](../01-zero-shot/README.md) when the task is specialized, the output format is hard to describe in prose but easy to show, or category boundaries are subtle. Typically two to five examples are enough; returns diminish quickly and each example costs tokens. The examples must be correct and consistent, because the model will faithfully imitate any pattern in them, including mistakes.

Example order and balance matter. For classification, cover each class and avoid ordering all positives before all negatives, which can create a positional bias.

## When to Use It

- **Zero-shot output is close but wrong in a consistent way.** Examples are the cheapest correction for a systematic error.
- **The format is idiosyncratic**: a pipe-delimited line, a house citation style, a bespoke label vocabulary. Showing beats describing.
- **Category boundaries are subtle** and you need to pin down exactly where the line falls (is a feature request a "bug"? is a two-star review "negative" or "neutral"?).
- **You want a specific voice or register** that is hard to name. Three samples of the tone convey what "professional but warm" cannot.
- **You already have labelled data.** If a spreadsheet of past inputs and correct outputs exists, few-shot is nearly free to build.

## When Not to Use It

- **Zero-shot already passes your evaluation.** Examples cost tokens on every single call forever. Do not pay for accuracy you already have.
- **Your examples are not verified correct.** The model imitates faithfully, including your mistakes. Bad examples are worse than none.
- **You cannot cover the space fairly.** Three examples that are all one class teach the model that class is the default answer.
- **The task is hard reasoning, not hard formatting.** Showing input/output pairs without the working teaches the shape, not the skill. Use [chain-of-thought](../03-chain-of-thought/README.md), or few-shot CoT where each example shows its steps.
- **The examples would blow the context budget** on long inputs. Consider fine-tuning, or retrieving the two nearest examples per query instead of shipping twenty static ones.
- **You need a hard structural guarantee.** Examples make the right shape likely, not certain. Use [structured output](../07-structured-output/README.md) for a contract.

## Example Prompt

```text
Extract the product name and the reported issue from each support message.
Respond as "product | issue".

Message: "My Acme Router keeps dropping the WiFi every few minutes."
Answer: Acme Router | intermittent WiFi disconnects

Message: "The ZenPhone screen has a green line down the left side."
Answer: ZenPhone | vertical green line on display

Message: "Coffee spills out the side of my BrewMax whenever it fills."
Answer:
```

## Output

```text
BrewMax | leaks from the side during filling
```

The two demonstrations fixed both the extraction task and the exact `product | issue` output shape, so the model produced a matching third answer with no format explanation.

## Before and After

**Before (inconsistent examples):**

```text
Pull out the product and the problem.

"My Acme Router keeps dropping the WiFi every few minutes."
-> Acme Router has intermittent WiFi disconnects

Message: "The ZenPhone screen has a green line down the left side."
The issue is a vertical green line on the display for the ZenPhone.

"Coffee spills out the side of my BrewMax whenever it fills."
```

What goes wrong: the two demonstrations disagree with each other. One uses an
arrow, the other uses a `Message:` prefix and a full sentence. One puts the
product first, the other puts it last. There is no stable pattern to imitate,
so the model picks whichever it likes on any given call, and the output is a
sentence you now have to parse with a regex that will break next week.

**After (consistent examples):**

```text
Extract the product name and the reported issue from each support message.
Respond as "product | issue". The issue must be a short noun phrase, not a
sentence. If no product is named, use "unknown" as the product.

Message: "My Acme Router keeps dropping the WiFi every few minutes."
Answer: Acme Router | intermittent WiFi disconnects

Message: "The ZenPhone screen has a green line down the left side."
Answer: ZenPhone | vertical green line on display

Message: "It just stopped charging overnight."
Answer: unknown | stopped charging

Message: "Coffee spills out the side of my BrewMax whenever it fills."
Answer:
```

Why it is better: every example now uses the identical `Message:` / `Answer:`
frame and the identical `product | issue` shape, so there is exactly one
pattern to copy. The instruction states the rule the examples demonstrate,
which is belt and braces: the model gets it from both channels. The third
example is an edge case, teaching the "unknown" fallback rather than leaving
the model to invent a product name when none is present. Finally the trailing
`Answer:` cues the model to complete rather than start a new conversation.

## Best Practices

- **Use consistent formatting across every example.** The model imitates structure literally, so identical delimiters and casing throughout are essential.
- **Make examples correct and representative.** Errors in your samples become errors in the output.
- **Cover the range**, including at least one tricky or edge case if boundaries are subtle.
- **Balance and shuffle class labels** for classification to avoid positional and majority bias.
- **Keep the example count small** (2 to 5 typically); stop when quality plateaus.
- **Match example difficulty to the real inputs** you expect at inference time.

## Common Mistakes

- **Inconsistent example formats**, which produce inconsistent outputs.
- **Too many examples**, wasting context and money for little gain, sometimes hurting quality.
- **Biased example sets** (all one class, or ordered by class) that skew predictions.
- **Copying a subtle mistake** into every example and then wondering why every answer repeats it.
- **Examples that leak the answer to the specific test input** rather than teaching the general task.
- **Forgetting delimiters**, so the model cannot tell where an example ends and the query begins.
