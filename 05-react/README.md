# 05 · ReAct (Reason + Act)

> Technique reference. Part of the [Prompt Engineering Handbook](../README.md).

## Theory

ReAct interleaves reasoning with actions so a model can use external tools instead of relying only on what it memorized. The model emits a loop of **Thought** (reason about what to do next), **Action** (call a tool with an input), and **Observation** (the result the tool returns), repeating until it has enough information to produce a final answer. Reasoning decides which action to take; the observation grounds the next thought in real data rather than a guess.

This is the foundation of tool-using agents. It lets a model look up current facts, run calculations, query a database, search a codebase, or call an API, then incorporate the result. Reasoning alone (like [chain-of-thought](../03-chain-of-thought/README.md)) can drift into confident fabrication; acting alone has no plan. ReAct combines them: the thoughts keep the tool calls purposeful, and the observations keep the reasoning honest.

In practice the loop runs in your code, not in one model turn. You send the prompt plus tool definitions, the model responds with an action, your code executes the tool and appends the observation, then you call the model again with the updated transcript. Modern APIs formalize this as native tool/function calling, but the ReAct pattern is the same underneath. Always cap the number of iterations so a confused agent cannot loop forever.

## When to Use It

- **The answer depends on information the model does not have**: live data, private documents, your database, the current state of a system.
- **The task needs a real computation or side effect**: arithmetic that must be exact, a file written, a ticket created, an API called.
- **The number of steps is not known in advance.** If step 3 depends on what step 2 returned, a fixed pipeline cannot express it but an agent loop can.
- **Grounding matters more than fluency.** Observations from real tools are the antidote to confident fabrication.
- **You want an auditable trail.** The Thought / Action / Observation transcript is a log of exactly what was consulted and when.

## When Not to Use It

- **The step sequence is fixed and known.** If it is always extract, then classify, then format, hard-code that as [prompt chaining](../09-prompt-chaining/README.md). A deterministic pipeline is cheaper, faster, and cannot wander.
- **The model already knows the answer** from pretraining and the fact is stable. Do not spend a search call establishing that water boils at 100C.
- **Tools have irreversible side effects and there is no human in the loop.** Deleting records, sending mail, moving money: gate these behind confirmation, or expose read-only tools only.
- **Latency budgets are tight.** Each loop iteration is a full round trip plus tool execution, so a five-step agent is five times the wait.
- **You have twenty tools to expose.** Selection accuracy falls as the tool list grows. Split into narrower agents or route to a subset first.
- **Tool inputs cannot be validated.** If the model chooses arguments for a shell or SQL tool and nothing checks them, you have built a remote code execution path, not a feature.

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

## Before and After

**Before (tools named but no protocol):**

```text
You have a search tool and a calculator. Use them if you need to.

What is the population of France divided by the population of Norway, rounded
to the nearest whole number?
```

What goes wrong: nothing tells the model how to call a tool or when to stop, so
it does the only thing it can and writes the whole exchange itself, inventing
its own observations:

```text
I'll search for the population of France. It's 67 million. Now Norway, which
is 5.4 million. 67 / 5.4 = 12.4, so the answer is 12.
```

No tool ever ran. The numbers came from memory and may be years stale, the
division was done in-model rather than by the calculator, and the host code has
no structured action to intercept. This is the failure ReAct exists to prevent,
and it is easy to miss because the transcript looks like tool use.

**After (explicit loop protocol and stop conditions):**

```text
You can use these tools:
- search(query): returns a short web snippet
- calc(expression): evaluates arithmetic

Rules:
- Emit exactly ONE step per turn, then stop and wait.
- Never write an Observation yourself. The system fills it in.
- If a tool returns an error, reason about it and try a different action.
- Do all arithmetic with calc, never in your head.
- After at most 6 actions, answer with what you have.

Format:
Thought: <your reasoning>
Action: <tool>[<input>]
Observation: <result, filled in by the system>
... (repeat) ...
Final Answer: <answer>

Question: What is the population of France divided by the population of
Norway, rounded to the nearest whole number?
```

Why it is better: "one step per turn, then stop" gives the host code a place to
interrupt, execute the real tool, and append a real observation, which is the
whole mechanism. Forbidding self-written observations closes the fabrication
path directly. Routing arithmetic to `calc` removes a known weak spot. The
six-action cap bounds cost and guarantees termination, and the error rule turns
a failed call into something the model can recover from rather than a dead loop.
In production you would express this same protocol through your provider's
native tool-calling API, which enforces the action format for you instead of
relying on the model to format `Action:` lines correctly.

## Best Practices

- **Describe each tool precisely** (name, purpose, argument schema, and what it returns) so the model calls it correctly.
- **Execute tools in your code** and feed back real observations; never let the model hallucinate an observation.
- **Enforce a step limit** and a stop condition so a stuck agent halts instead of looping indefinitely.
- **Validate and sanitize tool inputs** before running them; treat model-chosen arguments as untrusted, especially for code-execution or shell tools.
- **Keep the transcript tight**: summarize or drop stale observations so the context window does not fill with old tool output.
- **Prefer native tool/function-calling APIs** when available; they structure the action step and reduce parsing errors versus free-text `Action:` lines.

## Common Mistakes

- **Letting the model write its own observations**, which reintroduces the fabrication that tools were meant to prevent.
- **No iteration cap**, so a confused loop burns tokens without terminating.
- **Vague tool descriptions**, causing wrong tool choice or malformed arguments.
- **Executing tool inputs without validation**, opening injection and code-execution risks.
- **Overloading the agent with dozens of tools**, which degrades selection accuracy; expose only what the task needs.
- **Not handling tool errors**: a failed call should return an error observation the model can react to, not crash the loop.
