# Local Chat Application

**Internship:** Oasis Infobyte - OIBSIP
**Track:** Python Programming
**Assignment:** Task 5

## Objective & description

Demonstrate a local client/server chat application with account storage.

## Tech stack

Python 3.10+, tkinter, SQLite, and task-specific libraries.

## Features implemented

- Separate server and client processes
- Local account/message storage
- PBKDF2 password hashes; server binds only to 127.0.0.1

## How to run / setup

Install dependencies using `python -m pip install -r requirements.txt`, then Open two terminals in this folder. Run `python chat_server.py` in the first, then `python chat_client.py` in the second. The server binds to 127.0.0.1 only.

Primary deliverable: [`chat_server.py`](./chat_server.py).

> Live microphone, remote speech recognition, weather API, SMTP, and local chat runtime require the respective hardware/services and were not claimed as tested.

## Generated outputs

- [outputs/smoke_test_results.txt](./outputs/smoke_test_results.txt)
