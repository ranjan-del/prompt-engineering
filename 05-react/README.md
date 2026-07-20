# 05 · ReAct (Reason + Act)

> Technique reference. Part of the [Prompt Engineering Handbook](../README.md).

## Theory

ReAct interleaves reasoning with actions so a model can use external tools instead of relying only on what it memorized. The model emits a loop of **Thought** (reason about what to do next), **Action** (call a tool with an input), and **Observation** (the result the tool returns), repeating until it has enough information to produce a final answer. Reasoning decides which action to take; the observation grounds the next thought in real data rather than a guess.

This is the foundation of tool-using agents. It lets a model look up current facts, run calculations, query a database, search a codebase, or call an API, then incorporate the result. Reasoning alone (like [chain-of-thought](../03-chain-of-thought/README.md)) can drift into confident fabrication; acting alone has no plan. ReAct combines them: the thoughts keep the tool calls purposeful, and the observations keep the reasoning honest.

In practice the loop runs in your code, not in one model turn. You send the prompt plus tool definitions, the model responds with an action, your code executes the tool and appends the observation, then you call the model again with the updated transcript. Modern APIs formalize this as native tool/function calling, but the ReAct pattern is the same underneath. Always cap the number of iterations so a confused agent cannot loop forever.

## Example Prompt

```text
You can use these tools:
- search(query): returns a short web snippet
- calc(expression): evaluates arithmetic

Use this format, one step per turn:
Thought: <your reasoning>
Action: <tool>[<input>]
Observation: <result, filled in by the system>
... (repeat) ...
Final Answer: <answer>

Question: What is the population of France divided by the population of Norway,
rounded to the nearest whole number?
```

## Output

```text
Thought: I need both populations, then a division. Start with France.
Action: search[population of France]
Observation: France has about 68,000,000 people.

Thought: Now I need Norway's population.
Action: search[population of Norway]
Observation: Norway has about 5,500,000 people.

Thought: Divide 68,000,000 by 5,500,000.
Action: calc[68000000 / 5500000]
Observation: 12.36

Final Answer: About 12.
```

*(Model: representative of a modern tool-using chat model.)* Each `Observation` is produced by the host system executing the tool, not by the model. The model reasons about which tool to call, waits for the real result, and only answers once the arithmetic is grounded in retrieved data.

## Best Practices

- **Describe each tool precisely** — name, purpose, argument schema, and what it returns — so the model calls it correctly.
- **Execute tools in your code** and feed back real observations; never let the model hallucinate an observation.
- **Enforce a step limit** and a stop condition so a stuck agent halts instead of looping indefinitely.
- **Validate and sanitize tool inputs** before running them; treat model-chosen arguments as untrusted, especially for code-execution or shell tools.
- **Keep the transcript tight** — summarize or drop stale observations so the context window does not fill with old tool output.
- **Prefer native tool/function-calling APIs** when available; they structure the action step and reduce parsing errors versus free-text `Action:` lines.

## Common Mistakes

- **Letting the model write its own observations**, which reintroduces the fabrication that tools were meant to prevent.
- **No iteration cap**, so a confused loop burns tokens without terminating.
- **Vague tool descriptions**, causing wrong tool choice or malformed arguments.
- **Executing tool inputs without validation**, opening injection and code-execution risks.
- **Overloading the agent with dozens of tools**, which degrades selection accuracy; expose only what the task needs.
- **Not handling tool errors** — a failed call should return an error observation the model can react to, not crash the loop.
