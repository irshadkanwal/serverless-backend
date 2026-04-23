---
name: "EXTRACT_USER_MEMORY"
description: "Prompt EXTRACT_USER_MEMORY"
category: "memory"
source_file: "memory_prompts"
variables:
  - "coach_message"
  - "coach_response"
  - "user_message"
---
Conversation Snapshot for Memory:
- Prev Coach Response: "{coach_message}"
- User Response: "{user_message}"
- Next Coach Response: "{coach_response}"

Capture the coaching dynamics and client insights:
- What did the client reveal about their thoughts, feelings, or behaviors?
- What progress, resistance, or breakthrough moments occurred?
- What commitments, realizations, or action items emerged?
- How did the client respond to coaching interventions?
- What themes or patterns became apparent?

Store as a coherent narrative that preserves the context and emotional tone for future sessions.