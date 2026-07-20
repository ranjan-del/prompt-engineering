# 08 · Prompt Templates

> Technique reference. Part of the [Prompt Engineering Handbook](../README.md).

## Theory

A prompt template is a reusable prompt with named placeholders that are filled in at runtime. Instead of concatenating strings ad hoc for every call, you author the prompt once, mark the parts that vary as variables (for example `{{topic}}` or `{audience}`), and render it with real values on each request. This separates the stable prompt design from the changing data, exactly as templating separates HTML structure from the values injected into it.

Templates make prompts maintainable and testable. You can version a template, review changes in a diff, reuse it across many inputs, and A/B two versions while keeping everything else constant. They also make a system safer and more consistent: the instructions, role, format rules, and few-shot examples live in the template, while only the user-supplied data flows through the variables. Popular frameworks (LangChain `PromptTemplate`, Jinja2, plain `str.format`) all implement the same idea.

The main risk is injection: if user input is dropped into a template unescaped, it can override your instructions or break the template's own delimiters. Keep variable content clearly fenced (quotes, tags, or a delimited block), treat it as data rather than instructions, and never let a raw variable silently redefine the task.

## Example Prompt

```text
Template:
---
You are a {role}. Summarize the text below for a {audience} audience in
{sentence_count} sentences. Use plain language.

Text:
\"\"\"
{input_text}
\"\"\"
---

Rendered with:
  role="technical writer"
  audience="non-technical"
  sentence_count="2"
  input_text="Our API now supports pagination via cursor tokens returned in each response."
```

## Output

```text
Our API can now hand back results in smaller pages instead of all at once.
Each response includes a marker you use to fetch the next page.
```

*(Model: representative of a modern instruction-tuned chat model.)* The same template serves any role, audience, length, and text; only the variables changed. The user-supplied `input_text` is fenced in triple quotes so it is treated as content to summarize, not as new instructions.

## Best Practices

- **Name variables clearly** and keep them for genuinely varying content, not for parts of the instruction that should stay fixed.
- **Fence user-supplied variables** with quotes, tags, or a delimited block so injected text cannot pose as instructions.
- **Version templates** and keep them in source control so prompt changes are reviewable and revertible.
- **Validate that every placeholder is filled** before sending; a missing value should error, not ship a literal `{topic}` to the model.
- **Centralize shared templates** so a fix propagates everywhere instead of being copy-pasted.
- **Test templates against representative inputs**, including edge cases like empty strings and very long text.

## Common Mistakes

- **Unescaped user input** that breaks the template's delimiters or overrides the instructions (prompt injection).
- **Leaving an unfilled placeholder**, sending the model a literal `{{variable}}` token.
- **Over-parameterizing**, turning fixed instructions into variables and losing the consistency a template is meant to provide.
- **Duplicating a template inline** in many places, so a needed change has to be made in all of them.
- **No versioning**, making it impossible to tell which template produced a past result or to roll back a regression.
- **Ignoring whitespace and formatting** in the rendered output, where stray newlines from substitution subtly change model behavior.
