# 07 · Structured Output

> Technique reference. Part of the [Prompt Engineering Handbook](../README.md).

## Theory

Structured output binds a model's response to a declared schema (typically JSON Schema, or a Pydantic/Zod model that compiles to one), so the result is not just valid JSON ([JSON mode](../06-json-mode/README.md)) but valid *against your contract*. The provider constrains decoding to the schema (often called "strict" or "structured outputs"), guaranteeing the required keys exist, types match, enums stay in range, and no extra fields appear. The parsed object drops straight into typed code with no defensive checking.

This is the difference between "the output parses" and "the output is exactly the object my function expects." Where JSON mode guarantees syntax, structured output guarantees shape. It is the right choice whenever downstream code depends on the response (populating a form, calling an API, writing a database row), and it underpins reliable tool/function calling, where each tool's arguments are defined by a schema the model must satisfy.

Design the schema deliberately. Keep it as flat and minimal as the task allows; mark required fields explicitly and disallow extra properties so the contract is unambiguous. Use enums to constrain categorical fields, and add field descriptions, since the model reads them as guidance. Deeply nested or sprawling schemas are harder for the model to fill reliably and harder for you to validate.

## When to Use It

- **The response feeds typed code**: a dataclass, a Pydantic model, a database row, an API request body.
- **Categorical fields must stay in range.** Enums are the reason to reach for schemas over plain [JSON mode](../06-json-mode/README.md).
- **You are defining tools for an agent.** Tool arguments are exactly a schema-constrained extraction problem.
- **Missing keys would break a later step** and you want that impossible rather than merely unlikely.
- **Multiple services share the contract.** A schema is a document both sides can validate against and version.

## When Not to Use It

- **The output is prose.** Forcing a blog post through a schema adds escaping and structure that serve no one.
- **The schema is deeply nested or has fifty fields.** Fill reliability drops with depth and breadth. Flatten it, or split it across a [chain](../09-prompt-chaining/README.md) of narrower extractions.
- **The shape genuinely varies per input.** A schema is a fixed contract. If half the fields are optional and unused on any given call, you may be modelling the problem wrong.
- **Your provider does not support strict mode.** Non-strict schema "support" is a strong hint, not a guarantee, so keep validating.
- **You need the model to reason.** Schema-constrained decoding leaves no room for working. Add an explicit `reasoning` string field first in the object, or reason in a preceding call.
- **The task is exploratory.** Locking a schema early can hide that you do not yet know what fields you need.

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

## Before and After

**Before (a loose schema described in prose):**

```text
Extract the meeting title, date, attendees and priority as JSON.

Text: "Set up the Q3 budget review for 2026-08-12 with Priya and Tom.
It's high priority."
```

A plausible response:

```json
{
  "title": "Q3 budget review",
  "date": "Aug 12, 2026",
  "attendees": "Priya and Tom",
  "priority": "High",
  "notes": "Scheduled by user request"
}
```

What goes wrong: it is valid JSON and it is still unusable. `date` is a human
string that `date.fromisoformat()` rejects. `attendees` is one string where the
caller expects a list, so iterating it yields characters. `priority` is
`"High"`, which fails a `priority == "high"` comparison and any enum column
constraint. And `notes` is an invented key that a strict deserializer will
reject outright. Every one of these is a shape problem, and no amount of JSON
syntax guarantee catches any of them.

**After (schema-bound, with descriptions and enums):**

```python
# Pydantic models are worth the extra layer over hand-written JSON Schema:
# the same class validates the response AND is the type the rest of the code
# uses, so the contract cannot drift away from the callers.
from enum import Enum
from pydantic import BaseModel, Field

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Meeting(BaseModel):
    # Descriptions are not documentation for humans here. The model reads them
    # as per-field instructions, which is what fixes the date format.
    title: str = Field(description="Short meeting title, no date or names")
    date: str = Field(description="ISO 8601 date, YYYY-MM-DD")
    attendees: list[str] = Field(description="One entry per person, names only")
    priority: Priority

    model_config = {"extra": "forbid"}  # becomes additionalProperties: false
```

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

Text: "Set up the Q3 budget review for 2026-08-12 with Priya and Tom.
It's high priority."
```

Why it is better: each earlier failure is closed by a specific schema feature.
The `description` on `date` pins the format to ISO 8601. Typing `attendees` as
an array makes a single joined string impossible. The enum on `priority`
constrains decoding to three exact lowercase values, so `"High"` cannot be
produced. `additionalProperties: false` blocks the invented `notes` key, and
`required` guarantees nothing is silently omitted. The result deserializes into
`Meeting` with no defensive branching at the call site.

## Best Practices

- **Define the schema explicitly** (JSON Schema, Pydantic, Zod) and pass it through the provider's structured-output feature rather than describing it only in prose.
- **Mark required fields and set `additionalProperties: false`** so the contract is unambiguous and extra keys are impossible.
- **Use enums for categorical fields** to prevent free-text values that break downstream logic.
- **Add field descriptions**: the model uses them as inline instructions for what each field means and how to format it.
- **Keep schemas flat and minimal**; reliability drops as nesting and field count grow.
- **Validate on receipt anyway** as defense in depth, and version the schema alongside the prompt.

## Common Mistakes

- **Over-nested or bloated schemas** that lower fill reliability and complicate validation.
- **Leaving fields optional** when your code assumes they exist, so a missing key breaks a later step.
- **Free-text where an enum belongs**, letting the model return `Urgent` or `HIGH` instead of a controlled value.
- **Omitting field descriptions**, then getting the wrong format (e.g. `Aug 12` instead of an ISO date).
- **Confusing structured output with JSON mode**: JSON mode guarantees syntax only, not your schema.
- **Not evolving the schema with the prompt**, so the two drift out of sync over time.
