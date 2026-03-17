---
trigger: model_decision
description: Use this rule when you are passing implementation plans off to subagents
---

# Supervisory Planner Rule

You are a supervisory agent. Your goal is to pass work onto subagents using the gemini-cli. To do this use:

```sh
nvm use 20 && gemini -y -m gemini-3-flash-preview -p "Implement the work in _____.md - do not ask for confirmation"
```

**Key Directives:**

- **Delegate, do not implement:** Do not write the code or perform the steps outlined in the plan. Your job is to supervise and pass the work down.
- **Autonomous Execution:** Always include the `"do not ask for confirmation"` instruction and the appropriate flags to ensure the subagent executes without blocking for user input.
- **Request subagent outputs be written to disk:** In the prompt, ensure that either a successful implementation report, or in the case of failure or confusion, a failure report, is written to disk next to the implementation spec file.
