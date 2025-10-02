from typing import Any, Optional
from langswarm.core.base.log import GlobalLogger

import ipywidgets as widgets
from IPython.display import display
import sys
import io
import logging
import traceback


class OutputRedirect(io.StringIO):
    """
    Custom output redirection for capturing print() statements.
    Redirects output to a chat log widget.
    """
    def __init__(self, chat_widget):
        super().__init__()
        self.chat_widget = chat_widget

    def write(self, message):
        """Redirect print() statements to the chat log"""
        if message.strip():
            self.chat_widget.value += f"\n{message.strip()}"
        super().write(message)

    def flush(self):
        pass  # Flush is overridden but not needed


class ChatLogHandler(logging.Handler):
    """
    Custom log handler to append log messages to a log widget.
    """
    def __init__(self, log_widget):
        super().__init__()
        self.log_widget = log_widget

    def emit(self, record):
        """ Append formatted log messages to the log widget """
        log_entry = self.format(record)
        formatted_log = f"\n   [LOG] ⮕ {log_entry}\n"
        self.log_widget.value += formatted_log


class JupyterChatInterface:
    """
    A simple chat interface with logging, designed for use in Jupyter notebooks.
    """

    def __init__(self, agent):
        """
        Initializes the chat interface.
        
        :param agent: An LLM agent with a `.chat()` method.
        """
        self.agent = agent
        self.conversation_history = []

        # Create widgets
        self.chat_log = widgets.Textarea(
            value="Chat:",
            placeholder="Chat appears here...",
            layout=widgets.Layout(width="50%", height="300px"),
            disabled=True,
        )

        self.text_input = widgets.Textarea(
            value="",
            placeholder="Type your message here...",
            layout=widgets.Layout(width="100%", height="80px"),
            style={'white_space': 'pre-wrap'}
        )

        self.send_button = widgets.Button(description="Send")

        self.log_window = widgets.Textarea(
            value="Logs:",
            placeholder="Logs appear here...",
            layout=widgets.Layout(width="50%", height="300px"),
            disabled=True,
        )

        # Link button click to handle input
        self.send_button.on_click(self.handle_submit)

        # Redirect stdout (print statements) to chat_log widget
        sys.stdout = OutputRedirect(self.chat_log)

        # Set up logging
        self.log_handler = ChatLogHandler(self.log_window)
        self.log_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        GlobalLogger.initialize(extra_handler=self.log_handler)

    def handle_submit(self, sender):
        """
        Handles user input, sends it to the agent, and updates the chat UI.
        """
        try:
            user_input = self.text_input.value.strip()
            if not user_input:
                return

            # Clear input box
            self.text_input.value = ""

            # Display user message
            self.chat_log.value += f"\n\nUser: {user_input}"
            self.conversation_history.append({"role": "user", "content": user_input})

            # Send user input to agent
            llm_response = self.agent.chat(user_input)  # Replace with actual LLM agent call

            # Store response
            self.conversation_history.append({"role": "assistant", "content": llm_response})

            # Display assistant response
            self.chat_log.value += f"\n\nAssistant: {llm_response}"

        except Exception as e:
            error_message = f"\n[ERROR] ⮕ {type(e).__name__}: {str(e)}"
            self.log_window.value += error_message
            self.chat_log.value += error_message
            print(error_message)
            print(traceback.format_exc())

    def display(self):
        """
        Displays the chat and log interface in a Jupyter notebook.
        """
        ui = widgets.HBox([self.chat_log, self.log_window])
        display(ui, self.text_input, self.send_button)
