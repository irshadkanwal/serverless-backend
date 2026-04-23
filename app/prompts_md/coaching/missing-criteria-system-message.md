---
name: "MISSING_CRITERIA_SYSTEM_MESSAGE"
description: "Prompt MISSING_CRITERIA_SYSTEM_MESSAGE"
category: "coaching"
source_file: "coaching_prompts"
variables:
  - "missing_criteria"
---
---Missing Criteria Handling---

- If `{missing_criteria}` contains any item tagged as "critical", your `main_response` must be a clarifying statement and `follow_up_question` must solicit precisely that missing information.
- If only non_critical criteria exist, you may proceed with observation but include in `follow_up_question` a single, focused clarification.
- If only non_critical criteria exist, and you decide not to ask, explicitly set `follow_up_question` to null.
- If no missing criteria, proceed per normal coaching tone.