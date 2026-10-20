# LLM-Powered File System Assistant

A small Python assistant that uses OpenRouter tool calling to read, search,
list, and create files in a chosen workspace. It uses the OpenAI-compatible
Python SDK with OpenRouter's API endpoint. The LLM decides which tool to call;
the Python application validates and executes each call, then returns its
result to the model.

## Requirements

- Python 3.10+
- An OpenRouter API key

## Setup

From this directory, create and activate a virtual environment, then install
the dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Set your OpenRouter API key in the current PowerShell session:

```powershell
$env:OPENROUTER_API_KEY = "your-api-key"
```

The assistant reads this environment variable when it creates the OpenRouter
client. Do not put API keys in source files or commit them.

## Run

The default workspace is the `resumes` directory in this project. Paths passed
to tools must stay inside the selected workspace. Relative paths are resolved
from that directory.

```powershell
python llm_file_assistant.py "Read all resumes in this workspace"
python llm_file_assistant.py --workspace .\resumes "Find resumes mentioning Python experience"
python llm_file_assistant.py "Create a summary file for resume_john_doe.txt"
```

When `--workspace .\resumes` is used, refer to a resume as
`resume_john_doe.txt` (not `resumes/resume_john_doe.txt`).

The default model is `openrouter/free`. You can choose another OpenRouter model
with `--model`, provided it supports tool calling:

```powershell
python llm_file_assistant.py --model "provider/model-name" "List the files"
```

## Tools

`fs_tools.py` provides:

- `read_file(filepath)`: extracts text from PDF, TXT, and DOCX files and returns
  it with file metadata.
- `list_files(directory, extension=None)`: lists files in one directory,
  optionally filtering by extension.
- `write_file(filepath, content)`: writes UTF-8 text and creates parent folders.
- `search_in_file(filepath, keyword)`: returns case-insensitive matches with
  surrounding context.

Errors are returned as structured results (or an error entry from
`list_files`) rather than being mistaken for successful operations. The
assistant rejects tool paths that resolve outside its workspace.

## Sample data

The `resumes` directory contains five fictional TXT resumes for trying out the
assistant. They use reserved `.invalid` email addresses and are not real people.
