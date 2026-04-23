---
name: "EXTRACT_COACH_MESSAGE_MEMORY"
description: "Prompt EXTRACT_COACH_MESSAGE_MEMORY"
category: "memory"
source_file: "memory_prompts"
variables:
  - "coach_response"
---
Coach's response in session: "{coach_response}"

Extract and store ONLY IF this contains:
- Specific observations about the client's goals, emotions, behaviour patterns, or progress.
- Important questions that probe deeper issues or encourage reflection
- Acknowledgments of progress or breakthroughs
- Identified challenges or areas for future exploration
- Coaching strategies or approaches that were introduced
- A commitment, milestone, or next step agreed on with the client.

If none of these elements are present, return NOTHING.