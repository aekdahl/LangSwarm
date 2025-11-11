import json
import os
import requests
import functions_framework
from google.cloud import logging

class CloudFunctionHandler:
    """
    A handler for processing LLM prompts in a Google Cloud Function.
    """
    _instance = None  # Store the single instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MySingleton, cls).__new__(cls)
            cls._instance.logger = logging.Client().logger("cloud-llm-handler")
        return cls._instance

    def process_prompt(self, prompt, agent):
        if not prompt:
            return json.dumps({"error": "Prompt is missing."}), 400

        self.logger.log_text(f"Processing prompt: {prompt}")

        try:
            request_json = request.get_json(silent=True)
            if not request_json or "prompt" not in request_json:
                return json.dumps({"error": "Missing 'prompt' in request"}), 400

            return json.dumps({"response": agent.chat(request_json["prompt"])}), 200

        except Exception as e:
            self.logger.log_text(f"Error processing prompt: {str(e)}", severity="ERROR")
            return json.dumps({"error": "An error occurred while processing your request."}), 400

### EXAMPLE GCP DEPLOYMENT ###
# Cloud Function entry point
#@functions_framework.http
#def generate_response(request):
#    return CloudFunctionHandler().process_prompt(prompt, agent)
