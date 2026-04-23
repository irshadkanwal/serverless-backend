---
name: "SESSION_CONTEXT_SYSTEM_MESSAGE"
description: "Prompt SESSION_CONTEXT_SYSTEM_MESSAGE"
category: "summary"
source_file: "summary_prompts"
variables:
  - "current_stage"
  - "emotional_state"
  - "insights"
  - "key_points"
  - "previous_stage"
  - "progress_indicators"
  - "recommendations"
  - "stage_specific_info"
---
Previous stage ({previous_stage}) summary:
- Client's emotional state: {emotional_state}
- Key points: {key_points}
- Insights gained: {insights}
- Progress indicators: {progress_indicators}

Stage-specific information:
{stage_specific_info}

Recommendations for current stage ({current_stage}):
{recommendations}