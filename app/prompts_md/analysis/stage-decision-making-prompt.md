---
name: "STAGE_DECISION_MAKING_PROMPT"
description: "Stage Transition Decision-Making Process"
category: "analysis"
source_file: "analysis_prompts"
variables: []
---
## Stage Transition Decision-Making Process
1. STAY in the current stage if:
   - Current stage objectives are not adequately addressed
   - Client would benefit from more time in this stage
   - Any critical missing criteria for the current stage are still present
   - Non‑critical missing criteria exist and require clarification before progressing
   - Non‑critical missing criteria exist and can be clarified without
  reverting to previous stages
   - Set transition_required to False

2. PROCEED to the next sequential stage if:
   - Current stage objectives have been accomplished
   - Client shows readiness for the next stage
   - All transition criteria from analysis guidelines are met
   - Set transition_required to True

3. SKIP AHEAD to a future stage if:
   - Client has clearly accomplished intermediate stage objectives
   - Client shows advanced understanding or progress
   - Client explicitly expressed a desire to move faster
   - Intermediate stages would provide minimal value
   - Client message covers multiple stages at once
   - Client directly addresses topics from later stages
   - No blocking by missing criteria for intermediate stages
   - No critical missing criteria exist for any intermediate stage
   - Set transition_required to True

4. RETURN to a previous stage if:
- Multiple attempts (3+) to satisfy critical missing criteria have failed
- Client shows confusion or frustration after repeated clarifications
- Conversation cycles in the same stage exceed 5 exchanges without progress
- Critical missing criteria suggest unresolved issues from earlier stages
- Client's responses indicate that foundational understanding is lacking

When these conditions are detected:
- Provide clear reasoning explaining why returning is necessary
- Identify which previous stage can best address the root issues
- Set transition_required to True
- Set next_stage as follows:
    - by default, the immediately preceding stage in the sequence
    - if foundational gaps are detected, step back two stages or more
      previous stage depending on the stage at which the issues raised
      in the identified missing criteria were discussed