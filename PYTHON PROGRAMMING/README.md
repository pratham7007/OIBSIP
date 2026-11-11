# Python Programming

Five independent applications, each with a beginner-friendly run path and advanced features.

| Task | Folder | Run |
|---|---|---|
| Voice assistant | [task1_voice_assistant](./task1_voice_assistant/) | `python assistant.py` |
| BMI tracker | [task2_bmi_calculator](./task2_bmi_calculator/) | `python bmi_app.py` |
| Password generator | [task3_password_generator](./task3_password_generator/) | `python password_generator.py` |
| Weather app | [task4_weather_app](./task4_weather_app/) | `python weather_app.py` |
| Chat application | [task5_chat_app](./task5_chat_app/) | Start `python chat_server.py`, then `python chat_client.py` |

## Dependencies and configuration

Python 3.10+ is recommended. Install the desktop, plotting, weather, speech, and clipboard
dependencies with `python -m pip install -r requirements.txt`. Microphone access and a
working audio device are required to test speech input/output.

Set `OPENWEATHER_API_KEY` before starting the assistant or weather app to use live weather.
Voice capture is opt-in (`/voice`) and speech recognition sends audio to Google's recognition
service through the library's default recognizer. Email sending is disabled until SMTP settings
are supplied as environment variables and requires typing `SEND` after reviewing the recipient.
No credentials are stored in source.

The chat demo binds only to `127.0.0.1`. Passwords are PBKDF2-hashed in SQLite, but chat
messages and authentication traffic are not end-to-end encrypted. Do not expose this demo
server to a network or use real credentials.
