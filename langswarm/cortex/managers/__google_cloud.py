import os
import requests
from google.auth import default
from google.auth.transport.requests import Request
from google.cloud import scheduler_v1

class GoogleCloudManager:
    """
    A centralized class to manage Google Cloud interactions for LangSwarm tools.
    
    - Handles API authentication and tokens.
    - Provides standardized methods for interacting with Google Cloud services.
    - Implements permission checks to restrict tool usage.

    Supports:
    - Cloud Scheduler
    - Firestore (future)
    - Pub/Sub (future)
    """

    def __init__(self, project_id=None, region="us-central1"):
        """
        Initializes the Google Cloud Manager.
        
        :param project_id: The Google Cloud project ID. Defaults to env variable.
        :param region: The default region for cloud services.
        """
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.region = region
        self.credentials, self.project_id = default()
        self.auth_header = self._generate_auth_header()

        if not self.project_id:
            raise ValueError("Google Cloud Project ID is required.")

    def _generate_auth_header(self):
        """Generates an authorization header using Google Cloud authentication."""
        self.credentials.refresh(Request())
        return {"Authorization": f"Bearer {self.credentials.token}"}

    ## === 🌟 Cloud Scheduler (Used for Reminders) === ##
    def create_cloud_scheduler_job(self, job_id, schedule, payload, target_url):
        """
        Creates a Cloud Scheduler job to trigger an API at a scheduled time.

        :param job_id: A unique identifier for the scheduled job.
        :param schedule: A cron-style schedule (e.g., "0 12 * * *").
        :param payload: The JSON payload to send in the request.
        :param target_url: The endpoint that will receive the reminder.
        """
        job_name = f"projects/{self.project_id}/locations/{self.region}/jobs/{job_id}"
        api_url = f"https://cloudscheduler.googleapis.com/v1/{job_name}"

        job_data = {
            "name": job_name,
            "schedule": schedule,
            "timeZone": "UTC",
            "httpTarget": {
                "uri": target_url,
                "httpMethod": "POST",
                "body": payload.encode("utf-8").hex(),
                "headers": {"Content-Type": "application/json"},
            },
        }

        response = requests.put(api_url, json=job_data, headers=self.auth_header)
        if response.status_code == 200:
            return f"Scheduled job '{job_id}' successfully created."
        return f"Failed to create job: {response.text}"

    def delete_cloud_scheduler_job(self, job_id):
        """
        Deletes a Cloud Scheduler job.

        :param job_id: The unique identifier of the job to delete.
        """
        job_name = f"projects/{self.project_id}/locations/{self.region}/jobs/{job_id}"
        api_url = f"https://cloudscheduler.googleapis.com/v1/{job_name}"

        response = requests.delete(api_url, headers=self.auth_header)
        if response.status_code == 200:
            return f"Job '{job_id}' deleted successfully."
        return f"Failed to delete job: {response.text}"

    ## === 🌟 Placeholder for Firestore or Pub/Sub === ##
    def store_data_firestore(self, collection, document_id, data):
        """
        Future feature: Store structured data in Firestore.
        """
        pass

    def publish_to_pubsub(self, topic_name, message):
        """
        Future feature: Publish messages to Pub/Sub for event-driven processing.
        """
        pass
