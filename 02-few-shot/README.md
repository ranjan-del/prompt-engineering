# 02 · Few-Shot Prompting

> Technique reference. Part of the [Prompt Engineering Handbook](../README.md).

## Theory

Few-shot prompting includes a small number of worked examples (input plus desired output) directly in the prompt before the real input. The examples demonstrate the task, the output format, the tone, and the decision boundaries, letting the model pattern-match rather than guess. This is in-context learning: no weights change, but the model conditions its next response on the demonstrations you provide.

Few-shot is the right step up from [zero-shot](../01-zero-shot/README.md) when the task is specialized, the output format is hard to describe in prose but easy to show, or category boundaries are subtle. Typically two to five examples are enough; returns diminish quickly and each example costs tokens. The examples must be correct and consistent, because the model will faithfully imitate any pattern in them, including mistakes.

Example order and balance matter. For classification, cover each class and avoid ordering all positives before all negatives, which can create a positional bias.

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
