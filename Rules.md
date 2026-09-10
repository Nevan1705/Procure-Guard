# Core Workflow & Rules

## 1. Primary Workflow
- **Order of Operations:** Input -> Read Rules -> Act
- Always read and review this Rules.md document before acting on any new input.

## 2. Problem Solving & Execution
- **Task Dissection:** Always dissect the given problem into smaller tasks. Complete each task one by one.
- **Strict Scoping:** Do NOT touch or meddle with functionalities that do not need to be changed for the given scope of the task. Always stay strictly within scope.
- **Context Maintenance:** Always maintain and actively update a CONTEXT.md file to keep track of the current project state and ongoing work.

## 3. Subagents & Orchestration
- **Parallel Execution:** To complete tasks that can be parallelized, use subagents with good tracking (using fast/Flash high models).
- **Pro Orchestration:** The 'Pro' model must act as the Orchestrator. 
- **Evaluation:** After each subagent completes its job, the Pro model must evaluate the results before proceeding.

## 4. Code Quality
- **Double Checking:** Always double-check the code.
- **No Hallucinations:** DO NOT hallucinate functionality, APIs, or logic.

## 5. Testing & Commits
- **Test Code Management:** Test case code must be deleted after a major change is completed.
- **Version Control:** All major changes must be committed with a meaningful commit message.
- **Git Pushing:** DO NOT execute \git push\ unless explicitly instructed by the user.
## 6. UI & Design
- **Design System:** Always when adding new UI components, it should follow the style of the current project which is described in DESIGN.md.
