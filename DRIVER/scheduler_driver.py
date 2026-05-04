# [GOAL] Manage Night Shift Schedule & Short Tasks
# [CONTEXT] User works 9PM-6AM. Prefers "Short Works" then "Rewards".

import datetime

def get_night_shift_plan():
    now = datetime.datetime.now()
    # Simple logic to define the next 'Short Work' block
    return {
        "current_focus": "Lead Generation / Research",
        "next_reward": "15 min Movie Clip/VibeCoding",
        "status": "Night Shift Active"
    }

def schedule_task_tool(task_name, time_str):
    # [OUTPUT] This will eventually plug into Google Calendar API
    return f"Task '{task_name}' logged for {time_str}. I will alert you."