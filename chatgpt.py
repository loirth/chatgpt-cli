import os
import re
import sys
import time
import signal
import sqlite3
import logging

from argparse import ArgumentParser
from dataclasses import dataclass, field
from datetime import datetime
from typing import Union, List, Dict

import openai
from rich.console import Console
from rich.markdown import Markdown
from loguru import logger
from openai.error import (
    AuthenticationError,
    APIConnectionError,
    InvalidRequestError,
    APIError,
    RateLimitError,
)

# Constants
API_KEY = ""
DEFAULT_ENGINE = "gpt-3.5-turbo"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 4096


@dataclass
class ConfigGPT:
    """Configuration class for ChatGPT."""
    api_key: str
    temperature: Union[int, float]
    engine: str
    max_tokens: int
    chat_models: List[str] = field(default_factory=lambda: [
        "gpt-4",
        "gpt-4-0613",
        "gpt-4-32k",
        "gpt-4-32k-0613",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-0613",
        "gpt-3.5-turbo-16k",
        "gpt-3.5-turbo-16k-0613",
    ])


class ChatGPT:
    """ChatGpt class for interacting with the OpenAI API."""
    def __init__(self, config: ConfigGPT) -> None:
        self.config = config
        openai.api_key = self.config.api_key

    def send_request(self, messages) -> str:
        """Sends a request to the OpenAI API and returns the generated response."""
        if self.config.engine in self.config.chat_models:
            response = openai.ChatCompletion.create(
                model=self.config.engine, messages=messages
            )
            return response.choices[0].message.content
        else:
            response = openai.Completion.create(
                engine=self.config.engine,
                prompt=messages[-1]["content"],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            return response.choices[0].text

    def create_message(
        self, messages: Union[List, List[Dict]], content, author="user"
    ) -> str:
        """
        Creates a message to send to the OpenAI API
        and handles possible errors.
        """
        try:
            if content.strip().lower() in (
                ":q!", "q", "exit()",
                ): sys.exit(0)
            messages.append({"role": author, "content": content})
            return self.send_request(messages)

        except APIError as error:
            self.handle_error(error)

        except RateLimitError:
            self.handle_error("[-] This is caused by API outage. Please try again later")

        except AuthenticationError:
            self.handle_error(
                f"[-] Incorrect API key provided: {self.config.api_key}. "
                "You can find your API key at "
                "https://platform.openai.com/account/api-keys.")

        except APIConnectionError:
            return self.handle_connection_error(messages, content, author)

        except InvalidRequestError as error:
            self.handle_error(error)

        except Exception as _exception:
            self.handle_error("[-] An unexpected error occurred.", _exception)

    def handle_connection_error(
            self, messages: List[Dict], content, author
        ) -> List[Dict]:
        """
        Handles connection errors when communicating with the OpenAI API.
        """
        logger.error(
            "[-] An internet connection error has occurred. Retrying..."
            ); time.sleep(3)
        return self.create_message(messages, content, author)

    @staticmethod
    def handle_error(error, _exception: Exception = None):
        """Handles various API-related errors and exceptions."""
        logger.error(
            "{}\n{}".format(error, _exception) if _exception else error
            ); sys.exit(1)


@dataclass
class ConfigDB:
    """Configuration class for the database."""
    path: str = os.path.dirname(os.path.abspath(__file__))
    name_db: str = ".chatgpt-history.db"

    @staticmethod
    def readable_timestamp(timestamp):
        """Converts a Unix timestamp to a human-readable date and time."""
        return datetime.utcfromtimestamp(
            timestamp).strftime('%Y-%m-%d %H:%M:%S')


class Database:
    """
    A class representing the message database for ChatGPT.

    This class provides methods for interacting with a SQLite database
    to store and retrieve chat messages.
    """
    def __init__(self, config_db: ConfigDB):
        self.config_db = config_db
        self.path = self.config_db.path
        self.name_database = config_db.name_db
        self.path_database = os.path.join(self.path, self.name_database)
        self.create_database()

    def execute_request(self, query: str, *, parameters: tuple = None,
            action: str = "operation"
        ) -> sqlite3.Cursor:
        """Executes a database query."""
        try:
            with sqlite3.connect(self.path_database) as connection:
                cursor = connection.cursor()

                if parameters is None:
                    cursor.execute(query)
                else:
                    cursor.execute(query, parameters)

                return cursor
        except sqlite3.Error as error:
            logger.error(f"Database {action} error: {error}")

    def create_database(self) -> None:
        """Creates the chat_messages table if it doesn't exist."""
        query = """CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                timestamp INTEGER NOT NULL
                )"""
        self.execute_request(query, action="creation")

    def insert_message(self, question: str, answer: str) -> None:
        """Inserts a chat message into the database."""
        timestamp = int(time.time())
        query = """INSERT INTO chat_messages (
            question, answer, timestamp) VALUES (?, ?, ?)"""
        self.execute_request(query, parameters=(question, answer, timestamp))

    def clear_message_history(self) -> None:
        """Clears all messages from the chat_messages table."""
        query = "DELETE FROM chat_messages"
        self.execute_request(query)
        logger.success("Message history cleared successfully.")

    def get_message_history(self) -> List[Dict[str, str]]:
        """Retrieves the entire chat message history from the database."""
        query = "SELECT question, answer, timestamp FROM chat_messages"
        rows = self.execute_request(query).fetchall()

        if not rows:
            self.handle_error("[-] There is no history in the database yet.")

        history = []
        for row in rows:
            question, answer, timestamp = row
            message = {
                "question": question,
                "answer": answer.strip(),
                "timestamp": self.config_db.readable_timestamp(timestamp),
            }
            history.append(message)

        return history

    def get_last_message(self) -> Union[Dict[str, str], None]:
        """Retrieves the last chat message from the database."""
        query = """SELECT question, answer, timestamp FROM chat_messages
            ORDER BY timestamp DESC LIMIT 1"""
        row = self.execute_request(query).fetchone()

        if row is None:
            self.handle_error("[-] There are no messages in the database yet.")

        question, answer, timestamp = row
        return {
            "question": question, "answer": answer.strip(),
            "timestamp": self.config_db.readable_timestamp(timestamp)
            }

    def delete_last_message(self) -> None:
        """Deletes the last chat message from the database."""
        query = """DELETE FROM chat_messages WHERE id IN (
            SELECT id FROM chat_messages ORDER BY timestamp DESC LIMIT 1)"""
        rows_affected = self.execute_request(query).rowcount

        if not rows_affected:
            self.handle_error("[-] There are no messages in the database yet.")

        logger.success("Last message deleted successfully.")


class CommandLineInterface(Database, ChatGPT):
    """A Command Line Interface for interacting with ChatGPT."""
    def __init__(
            self, rich_console, cgpt_config: ConfigGPT, config_db: ConfigDB
            ) -> None:
        Database.__init__(self, config_db=config_db)
        ChatGPT.__init__(self, config=cgpt_config)

        self.console = rich_console
        self.markdown_pattern = re.compile(r'[\*_\[>\]#`]{1,3}')

    def send_message(self, arr_messages: List[Dict], message: str) -> None:
        """
        Generate an AI response for the given message and display it.
        """
        answer = self.create_message(arr_messages, message)
        self.console.print("> Answer: ", style="bright_yellow bold")

        if self.contains_markdown(answer):
            self.console.print(Markdown(answer), style="bold")
        else:
            self.animated_message(answer)

        self.insert_message(message, answer)

    def run(self, arr_messages: List[Dict]) -> None:
        """Handle user interactions with ChatGPT."""
        message = ""
        arguments = self.parse_arguments()
        if arguments.message:
            message = ' '.join(arguments.message)
            self.send_message(arr_messages, message)
            return

        actions = {
            "last_message": self.view_last_message,
            "clear_history": self.clear_message_history,
            "delete_last_message": self.delete_last_message,
            "view_history": self.view_message_history,
        }

        for argument, value in arguments.__dict__.items():
            if value and argument in actions:
                actions[argument]()
                return

        ask_question = "[bright_green][bold]Ask a question: [/bold][/bright_green]"
        while True:
            message = str(self.console.input(ask_question))
            self.send_message(arr_messages, message)

    def contains_markdown(self, text: str) -> bool:
        """
        Use regular expression to check for markdown patterns,
        including code blocks.
        """
        return bool(self.markdown_pattern.search(text))

    def view_message_history(self) -> None:
        """Display the message history."""
        for message in self.get_message_history():
            self.show_message_info(message)

    def show_message_info(self, message: Dict[str, str]) -> None:
        """Display the detailed information of a message."""
        question = message["question"]
        answer = message["answer"]
        self.console.print(f"> Question: \n{question}", style="bright_green bold")

        if self.contains_markdown(answer):
            self.console.print("> Answer: ", style="bold")
            self.console.print(Markdown(answer), style="bold")
        else:
            self.console.print(f"> Answer: \n{answer}", style="bright_yellow bold")

        self.console.print(f"> Timestamp: \n{message['timestamp']}", style="bold")
        self.console.print("-" * 19, style="bold")

    def view_last_message(self) -> None:
        """View the last message details"""
        self.show_message_info(self.get_last_message())

    def parse_arguments(self) -> ArgumentParser:
        """
        Parse command-line arguments and return the ArgumentParser object.
        """
        parser = ArgumentParser(
            description=(
                "ChatGPT Command Line Interface\n"
                "This is a command line interface for interacting "
                "with ChatGPT, an AI language model."
            ),
            epilog=(
                "For more information, visit "
                "https://github.com/g3dox/chatgpt-cli."
            ),
        )
        parser.add_argument(
            "-m", "--message",
            type=str,
            nargs="+",
            help="Use to ask a question to ChatGPT. "
            "The program will terminate after one interaction.",
        )
        parser.add_argument(
            "-lm", "--last-message",
            action="store_true",
            help="Get the last message from the message history."
        )
        parser.add_argument(
            "-ch", "--clear-history",
            action="store_true",
            help="Clear the entire message history."
        )
        parser.add_argument(
            "-dm", "--delete-last-message",
            action="store_true",
            help="Delete the last message from the message history."
        )
        parser.add_argument(
            "-vh", "--view-history",
            action="store_true",
            help="View the entire message history."
        )

        return parser.parse_args()

    @staticmethod
    def animated_message(message: str, delay=0.03):
        """
        Display the message in an animated manner,
        printing one character at a time."
        """
        for char in message:
            print(char, end='', flush=True)
            time.sleep(delay)
        print()


def configure_logging():
    """Configure the logging settings using loguru library."""
    loguru_settings = "<level>{level: <8}</level> | <level>{message}</level>"
    logging.basicConfig(level=logging.CRITICAL)
    logger.remove()
    logger.add(sys.stderr, colorize=True, format=loguru_settings)


def main():
    """
    Main entry point of the ChatGPT command-line interface.
    It initializes the required components, configures logging,
    and runs the command-line interface for ChatGPT.
    """
    signal.signal(signal.SIGINT, handle_interrupt)

    configure_logging()

    openai_api_key = os.getenv("API_KEY") or API_KEY or None
    arr_messages = []

    rich_console = Console()

    db_config = ConfigDB()
    gpt_config = ConfigGPT(
        openai_api_key,
        DEFAULT_TEMPERATURE,
        DEFAULT_ENGINE,
        DEFAULT_MAX_TOKENS,
    )

    interface = CommandLineInterface(rich_console, gpt_config, db_config)
    interface.run(arr_messages)


def handle_interrupt(signal, frame):
    """Handle interrupt signal from the user (Ctrl+C)"""
    print("\n")
    logger.info("[-] ChatGPT-CLI interrupted by user")
    sys.exit(0)


if __name__ == "__main__":
    main()
