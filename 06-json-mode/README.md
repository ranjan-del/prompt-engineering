# 06 · JSON Mode

> Technique reference. Part of the [Prompt Engineering Handbook](../README.md).

## Theory

JSON mode is a provider feature that constrains the model's decoding so the response is guaranteed to be syntactically valid JSON. Instead of hoping a plain-text instruction like "reply in JSON" produces parseable output, you set a flag (commonly `response_format={"type": "json_object"}`) and the model can only emit tokens that keep the output well-formed: balanced braces, quoted keys, no trailing commas, no markdown code fences, no chatty preamble.

The key distinction: JSON mode guarantees **syntax**, not **shape**. It ensures `json.loads()` will succeed, but it does not by itself guarantee which keys are present, their types, or their meaning. For that you either describe the desired keys in the prompt (and validate afterwards) or move up to [structured output](../07-structured-output/README.md), which binds the response to a schema. JSON mode is the lightweight option: reliable parsing with minimal setup.

Most providers require you to also mention "JSON" in the prompt and to describe the fields you want, since the flag controls form but the prompt controls content. Always parse and validate the result in code; a syntactically valid object can still be missing a field or carry a wrong type.

## Example Prompt

```text
Extract the following fields from the message and return them as a JSON object
with exactly these keys: "name" (string), "email" (string or null),
"urgent" (boolean). Return only JSON.

Message: "Hi, this is Dana Cole. Please call me back today, it can't wait."
```

With the API's JSON-mode flag enabled, the response is constrained to valid JSON.

## Output

```json
{
  "name": "Dana Cole",
  "email": null,
  "urgent": true
}
```

*(Model: representative of a modern instruction-tuned chat model with JSON mode enabled.)* No email was present, so the model returned `null` rather than inventing one; the urgency cue ("can't wait", "today") maps to `true`. The output parses directly with a standard JSON parser, with no code fences or surrounding prose to strip.

## Best Practices

- **Enable the provider's JSON-mode flag** rather than relying on a prompt instruction alone; the flag is what actually enforces valid syntax.
- **Also describe the exact keys and types** in the prompt, because JSON mode controls form, not content.
- **Still parse and validate in code** — check required keys exist and have the right types before trusting the data.
- **Specify how to represent missing data** (`null`, empty string, omitted key) so the model does not guess.
- **Ask for "only JSON"** to suppress any leading explanation, and set a token limit high enough to avoid truncated, unparseable output.
- **Handle parse failures gracefully** with a retry or a repair step, even though they are rare in JSON mode.

## Common Mistakes

- **Assuming valid JSON means correct data** — syntax passing does not mean the schema or values are right.
- **Skipping validation**, so a missing key or wrong type crashes downstream code later.
- **Forgetting to mention JSON in the prompt** when the provider requires it, causing an API error or empty output.
- **Truncation from a low token limit**, which cuts the JSON mid-object and breaks parsing.
- **Not specifying null-handling**, so the model fabricates plausible values for fields it cannot find.
- **Using JSON mode when you need guaranteed structure** — reach for schema-based [structured output](../07-structured-output/README.md) instead.
