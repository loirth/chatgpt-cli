# ChatGPT Command Line Interface (CLI)

The ChatGPT CLI is a command-line interface for interacting with ChatGPT, an AI language model powered by OpenAI. This CLI allows you to have a conversational experience with ChatGPT, ask questions, and receive responses in real-time. The conversation history can also be managed, including viewing, clearing, and deleting individual messages.

## Installation

To use the ChatGPT CLI, follow the steps below:

1. **Clone the Repository:** Clone the repository containing the CLI code to your local machine.

2. **Install Required Packages:** Ensure that you have Python 3 and pip installed on your system. Use pip to install the required packages from the "requirements.txt" file:

    ```bash
    pip3 install -r requirements.txt
    ```

3. **Set Up OpenAI API Key**: To use the OpenAI API, you need an API key. Set your OpenAI API key as an environment variable with the name API_KEY or replace the API_KEY variable in the code with your actual API key.

4. **Run the CLI**: You are now ready to use the ChatGPT CLI. Run the CLI script using Python:
    ```bash
    python3 chatgpt.py
    ```

## Usage

Once you have installed the CLI and set up your OpenAI API key, you can start interacting with ChatGPT. The CLI provides various commands and options to manage the conversation history and communicate with the language model.

### Basic Usage

1. **Asking a Question**: You can interact with ChatGPT by simply typing your question or message and pressing Enter. The CLI will then display the AI-generated response.

### Command-Line Options

The ChatGPT CLI supports several command-line options that allow you to perform specific actions and manage the conversation history:

1. **Asking a Single Question**: To ask a single question to ChatGPT, you can use the -m or --message option followed by your question. The CLI will display the AI-generated response and then terminate.

    ```bash
    python3 chatgpt.py -m What is the meaning of life?
    ```

2. **Viewing the Last Message**: To view the last message from the conversation history, use the -lm or --last-message option.

    ```bash
    python3 chatgpt.py -lm
    ```

3. **Clearing the Entire History**: To clear the entire conversation history, use the -ch or --clear-history option. Note that this action cannot be undone.

    ```bash
    python3 chatgpt.py -ch
    ```

4. **Deleting the Last Message**: To delete the last message from the conversation history, use the -dm or --delete-last-message option. This will remove the last message permanently.

    ```bash
    python3 chatgpt.py -dm
    ```

5. **Viewing the Entire History**: To view the entire conversation history, use the -vh or --view-history option.

    ```bash
    python3 chatgpt.py -vh
    ```
## Contact

If you encounter any issues, have suggestions, or want to contribute, please visit the GitHub repository for this project: https://github.com/g3dox/chatgpt-cli.

Feel free to open an issue or submit a pull request. Your feedback and contributions are welcome!

## Disclaimer

Please note that the ChatGPT CLI uses the OpenAI API, and your usage may be subject to OpenAI's terms of service. Ensure you comply with their policies while using this CLI.

This project is not officially affiliated with or endorsed by OpenAI. It's an independent project created for educational and personal purposes.
