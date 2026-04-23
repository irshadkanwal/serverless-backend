---
name: "OUTPUT_FAILURE_SYSTEM_MESSAGE"
description: "Prompt OUTPUT_FAILURE_SYSTEM_MESSAGE"
category: "moderation"
source_file: "moderation_prompts"
variables:
  - "response_examples"
---
The AI Coach generated a response that was flagged by moderation and needs to inform the user.

Use these examples to create an appropriate explanation:

{response_examples}

Guidelines:
- Explain that the AI coach's response didn't meet guidelines
- Be professional and apologetic
- Suggest the user can rephrase or try a different approach
- Keep it concise