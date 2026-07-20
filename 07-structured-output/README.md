# 07 · Structured Output

> Technique reference. Part of the [Prompt Engineering Handbook](../README.md).

## Theory

Structured output binds a model's response to a declared schema — typically JSON Schema, or a Pydantic/Zod model that compiles to one — so the result is not just valid JSON ([JSON mode](../06-json-mode/README.md)) but valid *against your contract*. The provider constrains decoding to the schema (often called "strict" or "structured outputs"), guaranteeing the required keys exist, types match, enums stay in range, and no extra fields appear. The parsed object drops straight into typed code with no defensive checking.

This is the difference between "the output parses" and "the output is exactly the object my function expects." Where JSON mode guarantees syntax, structured output guarantees shape. It is the right choice whenever downstream code depends on the response — populating a form, calling an API, writing a database row — and it underpins reliable tool/function calling, where each tool's arguments are defined by a schema the model must satisfy.

Design the schema deliberately. Keep it as flat and minimal as the task allows; mark required fields explicitly and disallow extra properties so the contract is unambiguous. Use enums to constrain categorical fields, and add field descriptions, since the model reads them as guidance. Deeply nested or sprawling schemas are harder for the model to fill reliably and harder for you to validate.

## Example Prompt

```text
Extract meeting details into an object matching this schema:

{
  "type": "object",
  "properties": {
    "title":    { "type": "string" },
    "date":     { "type": "string", "description": "ISO 8601 date" },
    "attendees":{ "type": "array", "items": { "type": "string" } },
    "priority": { "type": "string", "enum": ["low", "medium", "high"] }
  },
  "required": ["title", "date", "attendees", "priority"],
  "additionalProperties": false
}

Text: "Set up the Q3 budget review for 2026-08-12 with Priya and Tom. It's high priority."
```

## Output

```json
{
  "title": "Q3 budget review",
  "date": "2026-08-12",
  "attendees": ["Priya", "Tom"],
  "priority": "high"
}
```

*(Model: representative of a modern chat model with schema-constrained structured output.)* Every required key is present with the correct type, the date is normalized to ISO 8601 as the description asked, and `priority` is one of the allowed enum values. Because `additionalProperties` is false, the model could not add stray keys, so the object validates without any post-processing.

## Best Practices

- **Define the schema explicitly** (JSON Schema, Pydantic, Zod) and pass it through the provider's structured-output feature rather than describing it only in prose.
- **Mark required fields and set `additionalProperties: false`** so the contract is unambiguous and extra keys are impossible.
- **Use enums for categorical fields** to prevent free-text values that break downstream logic.
- **Add field descriptions** — the model uses them as inline instructions for what each field means and how to format it.
- **Keep schemas flat and minimal**; reliability drops as nesting and field count grow.
- **Validate on receipt anyway** as defense in depth, and version the schema alongside the prompt.

## Common Mistakes

- **Over-nested or bloated schemas** that lower fill reliability and complicate validation.
- **Leaving fields optional** when your code assumes they exist, so a missing key breaks a later step.
- **Free-text where an enum belongs**, letting the model return `Urgent` or `HIGH` instead of a controlled value.
- **Omitting field descriptions**, then getting the wrong format (e.g. `Aug 12` instead of an ISO date).
- **Confusing structured output with JSON mode** — JSON mode guarantees syntax only, not your schema.
- **Not evolving the schema with the prompt**, so the two drift out of sync over time.
