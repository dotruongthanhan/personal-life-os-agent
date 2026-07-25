# Personal Life OS Agent

The Personal Life OS Agent is an intelligent Discord bot designed to act as a personal assistant. It integrates with Google Calendar and weather services to provide daily briefings, on-demand information, and event management through a conversational interface powered by Google's Gemini AI.

## ✨ Core Features

- **🤖 Smart Conversational AI**: Utilizes Google's Gemini model to understand natural language requests, enabling users to interact with the bot without needing to remember specific commands.
- **📞 AI-Powered Function Calling**: The bot can intelligently decide when to call external tools to fetch data or perform actions, such as:
    - Creating or updating events in Google Calendar.
    - Fetching today's agenda.
    - Looking up weather forecasts.
- **📅 Google Calendar Integration**:
    - **Daily Briefings**: Automatically sends a direct message every morning with a summary of the day's events.
    - **Event Reminders**: Proactively sends notifications for upcoming events based on user-defined reminder settings in Google Calendar.
    - **Event Management**: Create, update, and view calendar events using natural language (e.g., "remind me to call mom tomorrow at 5pm").
    - **Multi-Calendar Support**: Aggregates events from multiple Google Calendars specified in the configuration.
- **🌤️ Weather Forecasts**:
    - Get the current weather or a forecast for any city.
    - The bot provides actionable advice based on the weather, like what to wear.
- **🔄 Automated & Manual Sync**:
    - Automatically syncs with Google Calendar every 15 minutes to stay updated with the latest event changes.
    - Provides a `!sync` command for immediate manual synchronization.
- **⚙️ Customizable**: Easily configured through environment variables for Discord tokens, user IDs, API keys, and calendar IDs.

## 🛠️ Architecture & Tech Stack

The project is modular, with responsibilities separated into different services:

- **`main.py`**: The core of the Discord bot. It handles Discord events (`on_ready`, `on_message`), manages cron-style background tasks for briefings and reminders, and routes commands.
- **`gemini_services.py`**: Manages all interactions with the Google Gemini API. It constructs the prompts, handles the function-calling loop, and executes the corresponding tool functions.
- **`google_services.py`**: A dedicated module for all Google Calendar API interactions. It handles authentication (OAuth 2.0), fetching events, creating/updating events, and parsing calendar data.
- **`weather_service.py`**: Interfaces with the OpenWeatherMap API to fetch geographical coordinates and weather forecast data.
- **`tools_config.py`**: Defines the function schemas (tools) that the Gemini model can use. This file acts as the bridge between the AI and the Python functions in other modules.
- **`keep_alive.py`**: A simple Flask web server to ensure the bot remains online when deployed on hosting platforms like Koyeb or Replit.

**Technology Stack:**
- **Language**: Python
- **AI**: Google Gemini (`gemini-3.1-flash-lite-preview`)
- **Discord Bot**: `discord.py`
- **APIs**: Google Calendar API, OpenWeatherMap API
- **Libraries**: `google-api-python-client`, `google-auth-oauthlib`, `requests`, `python-dotenv`

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- A Discord Bot Token
- Google Cloud project with the Google Calendar API enabled
- An OpenWeatherMap API Key
- A Gemini API Key

### Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd personal-life-os-agent
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Google API Credentials:**
    - Follow the Google Calendar API Python Quickstart to enable the API and download your `credentials.json` file.
    - Place the `credentials.json` file in the root directory of the project.

4.  **Configure Environment Variables:**
    Create a `.env` file in the root directory and populate it with your credentials:

    ```env
    # Discord
    DISCORD_BOT_TOKEN="your_discord_bot_token"
    DISCORD_USER_IDS="your_discord_user_id,another_user_id" # Comma-separated list of user IDs to interact with

    # APIs
    GEMINI_API_KEY="your_gemini_api_key"
    OPENWEATHER_API_KEY="your_openweathermap_api_key"

    # Google Calendar
    # Add one or more calendar IDs. Use 'primary' for the default calendar.
    CALENDAR_ID_PERSONAL="primary"
    # CALENDAR_ID_WORK="your_work_calendar_id@group.calendar.google.com"

    # General Settings
    CITY="hanoi" # Default city for weather
    ```

5.  **First Run & Authentication:**
    Run the bot for the first time locally. It will prompt you to authenticate with Google via your browser.
    ```bash
    python main.py
    ```
    This will create a `token.json` file, storing your OAuth token for future runs.

## 🤖 Bot Commands

- `!help`: Displays the list of available commands.
- `!ping`: Checks the bot's latency.
- `!weather [city] [YYYY-MM-DD]`: Fetches the weather forecast. Defaults to your configured city and the current day.
- `!briefing`: Manually triggers the daily briefing.
- `!sync`: Manually forces a sync with Google Calendar to fetch the latest event reminders.
- `!list`: Shows the list of currently scheduled reminders.
- **Natural Language**: Talk to the bot directly! For example:
    - "What's on my schedule today?"
    - "Create an event for 'Team Meeting' tomorrow at 10 AM for 90 minutes."
    - "What will the weather be like in London this Friday?"
