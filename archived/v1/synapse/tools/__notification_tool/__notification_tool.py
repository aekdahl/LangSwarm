class LangSwarmReminderTool(BaseTool):
    """LangSwarm-compatible tool for reminders using Google Cloud Scheduler."""

    name = "LangSwarm Reminder"
    description = "A tool for scheduling and retrieving reminders."

    instructions = """
    - **set_reminder**: Schedule a new reminder.
      Example: {"action": "set", "date": "2025-03-01 12:00:00", "message": "Check project status"}

    - **get_reminders**: Retrieve upcoming reminders.
      Example: {"action": "get"}

    - **remove_reminder**: Delete a reminder.
      Example: {"action": "remove", "id": "reminder-123"}
    """

    def __init__(self):
        super().__init__()
        self.cloud_manager = GoogleCloudManager()

    def execute_action(self, params):
        """Handles incoming requests for reminders."""
        action = params.get("action")
        if action == "set":
            return self.set_reminder(params["date"], params["message"])
        elif action == "remove":
            return self.remove_reminder(params["id"])
        else:
            return "Unknown action."

    def set_reminder(self, date, message):
        """Schedules a reminder via Cloud Scheduler."""
        cron_schedule = self._convert_to_cron(date)
        job_id = f"reminder-{hash(message)}"
        return self.cloud_manager.create_cloud_scheduler_job(job_id, cron_schedule, message, "https://example.com/reminder")

    def remove_reminder(self, job_id):
        """Removes a scheduled reminder."""
        return self.cloud_manager.delete_cloud_scheduler_job(job_id)

    def _convert_to_cron(self, date_str):
        """Converts a datetime string into a cron format."""
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        return f"{dt.minute} {dt.hour} {dt.day} {dt.month} *"
