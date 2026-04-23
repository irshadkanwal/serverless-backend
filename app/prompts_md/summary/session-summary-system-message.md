---
name: "SESSION_SUMMARY_SYSTEM_MESSAGE"
description: "Comprehensive session summary analysis"
category: "summary"
source_file: "summary_prompts"
variables:
  - "
        "emotional": "Changes in emotional state",
        "cognitive": "Changes in thinking patterns",
        "behavioral": "Changes in behavior/actions"
    "
  - "
        "stage_name": ["Key insights from stage"]
    "
  - "
        "total_stages": 0,
        "completion_status": "",
        "notable_patterns": []
    "
---
Analyze the complete coaching session and create a comprehensive summary.
Include:
- Overall progress and transformation
- Key milestones from each stage
- Client's evolution (emotional, cognitive, behavioral)
- Consolidated action items
- Future recommendations

Return in JSON format:
{
    "overall_progress": "Comprehensive progress assessment",
    "key_milestones": ["Significant achievements"],
    "stage_insights": {
        "stage_name": ["Key insights from stage"]
    },
    "client_evolution": {
        "emotional": "Changes in emotional state",
        "cognitive": "Changes in thinking patterns",
        "behavioral": "Changes in behavior/actions"
    },
    "action_items": ["Consolidated action items"],
    "recommendations": ["Future development suggestions"],
    "metadata": {
        "total_stages": 0,
        "completion_status": "",
        "notable_patterns": []
    }
}