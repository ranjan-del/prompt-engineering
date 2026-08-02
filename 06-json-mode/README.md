# 06 · JSON Mode

> Technique reference. Part of the [Prompt Engineering Handbook](../README.md).

## Theory

JSON mode is a provider feature that constrains the model's decoding so the response is guaranteed to be syntactically valid JSON. Instead of hoping a plain-text instruction like "reply in JSON" produces parseable output, you set a flag (commonly `response_format={"type": "json_object"}`) and the model can only emit tokens that keep the output well-formed: balanced braces, quoted keys, no trailing commas, no markdown code fences, no chatty preamble.

The key distinction: JSON mode guarantees **syntax**, not **shape**. It ensures `json.loads()` will succeed, but it does not by itself guarantee which keys are present, their types, or their meaning. For that you either describe the desired keys in the prompt (and validate afterwards) or move up to [structured output](../07-structured-output/README.md), which binds the response to a schema. JSON mode is the lightweight option: reliable parsing with minimal setup.

Most providers require you to also mention "JSON" in the prompt and to describe the fields you want, since the flag controls form but the prompt controls content. Always parse and validate the result in code; a syntactically valid object can still be missing a field or carry a wrong type.

## When to Use It

- **Code consumes the response**, not a human. Anything that goes into `json.loads()` should be produced under a syntax guarantee, not a polite request.
- **The shape is simple and stable**: a handful of flat keys you can validate in three lines.
- **The provider supports the flag but not full schema binding**, or the schema feature is not worth the setup for this call.
- **You want to strip the ceremony.** JSON mode removes markdown fences, "Sure, here you go" preambles, and trailing commentary without you having to regex them off.
- **Prototyping an extraction step** before you commit to a formal schema.

## When Not to Use It

- **Downstream code assumes specific keys and types.** JSON mode will happily return `{"result": "Dana Cole"}` when you wanted `name`. Use [structured output](../07-structured-output/README.md), which binds the response to a contract.
- **A human reads the output.** Do not make a person parse JSON to read a summary.
- **The content is long-form prose.** Wrapping an essay in a JSON string field means escaping newlines and quotes and buys you nothing.
- **You skipped validation.** JSON mode plus no validation is a false sense of safety: the parse succeeds and the wrong data flows on silently.
- **The model needs to reason first.** A reasoning trace does not fit a JSON envelope comfortably. Either give the schema a `reasoning` field explicitly, or reason in a prior chained call.
- **You need enum-level control** over categorical fields. JSON mode cannot stop the model returning `"Urgent"` where you expected `"high"`.

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

## Before and After

**Before (asking nicely, flag off):**

```text
Give me the sender's name, email and whether it's urgent as JSON.

Message: "Hi, this is Dana Cole. Please call me back today, it can't wait."
```

A typical response:

````text
Sure! Here's the extracted information:

```json
{
  "sender_name": "Dana Cole",
  "email": "dana.cole@example.com",
  "urgency": "high"
}
```

Let me know if you'd like anything else!
````

What goes wrong: four separate failures. The response is wrapped in prose and a
markdown fence, so `json.loads()` throws until you write fence-stripping code.
The key names drifted (`sender_name`, `urgency`) because none were specified.
The email was **fabricated**, since the prompt never said what to do when a
field is absent. And `urgency` came back as the string `"high"` where the
caller expected a boolean. Only the first of those four is a syntax problem, so
even a lenient parser would not save you.

**After (flag on, keys and null-handling specified):**

```python
# The flag is what enforces valid syntax; the prompt is what controls content.
# Both are required, and most providers also want the word "JSON" in the prompt.
response = client.chat.completions.create(
    model=MODEL,
    response_format={"type": "json_object"},
    max_tokens=200,  # generous enough that the object cannot truncate mid-key
    messages=[{"role": "user", "content": PROMPT}],
)
```

```text
Extract the following fields from the message and return them as a JSON object
with exactly these keys:
  "name"   (string)  the sender's full name
  "email"  (string or null) the sender's email address, or null if absent
  "urgent" (boolean) true only if the sender asks for a same-day response

Do not guess or infer any value that is not stated in the message.
Return only JSON.

Message: "Hi, this is Dana Cole. Please call me back today, it can't wait."
```

Why it is better: the flag removes the fence and the preamble at the decoding
level, so the response is parseable by construction. Naming the exact keys and
their types stops the drift. Stating "or null if absent" plus "do not guess"
converts the fabricated email into an honest `null`, which is the single most
valuable line in the prompt. And the explicit `max_tokens` prevents the quiet
failure mode where a long object is cut off mid-string and the parse breaks for
reasons that have nothing to do with the model's understanding.

## Best Practices

- **Enable the provider's JSON-mode flag** rather than relying on a prompt instruction alone; the flag is what actually enforces valid syntax.
- **Also describe the exact keys and types** in the prompt, because JSON mode controls form, not content.
- **Still parse and validate in code**: check required keys exist and have the right types before trusting the data.
- **Specify how to represent missing data** (`null`, empty string, omitted key) so the model does not guess.
- **Ask for "only JSON"** to suppress any leading explanation, and set a token limit high enough to avoid truncated, unparseable output.
- **Handle parse failures gracefully** with a retry or a repair step, even though they are rare in JSON mode.

## Common Mistakes

- **Assuming valid JSON means correct data**: syntax passing does not mean the schema or values are right.
- **Skipping validation**, so a missing key or wrong type crashes downstream code later.
- **Forgetting to mention JSON in the prompt** when the provider requires it, causing an API error or empty output.
- **Truncation from a low token limit**, which cuts the JSON mid-object and breaks parsing.
- **Not specifying null-handling**, so the model fabricates plausible values for fields it cannot find.
- **Using JSON mode when you need guaranteed structure**: reach for schema-based [structured output](../07-structured-output/README.md) instead.
