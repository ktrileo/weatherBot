# **Warsaw Weather Bot 🤖☀️**

A simple Discord bot providing current weather and daily forecasts for Warsaw, Poland, via the Open-Meteo API.
Developed with help from AI for test intentions.

## **Features**

* **Weather Data:** Current conditions & daily forecast (temp, humidity, precipitation, daylight).  
* **Location:** Warsaw, Poland.  
* **Robust API:** openmeteo-requests with caching and retries.  
* **API Call Counter:** Tracks requests.  
* **Clear Output:** Formatted messages with units and emojis.  
* **Modular & Secure:** Organized code, uses environment variables for sensitive data.  
* **Logging:** Provides operational insights.

## **Project Structure**
```
weatherbot/  
├── main.py             # Bot's core logic, Discord event handlers, and command registration.
├── config.py           # Centralized configurable settings for the bot and external APIs.
├── weather_service.py  # Handles all Open-Meteo API calls and initial data parsing.
├── utils.py            # Contains general utility functions (e.g., timestamp formatting).
├── requirements.txt    # Lists all Python package dependencies.
├── .env.example        # Template file for environment variables (sensitive data).
└── .gitignore          # Specifies files and directories to be ignored by Git (e.g., virtual environment, .env).
```
## **Setup Guide**

### **Prerequisites**

* Python 3.9+  
* Discord Bot Token ([Developer Portal](https://discord.com/developers/applications))  
* A Discord Server.

### **Installation**

1. Create your\_bot\_project and add files.  
2. Set up virtual environment:  
   python3 \-m venv venv  
   source venv/bin/activate \# Windows: .\\venv\\Scripts\\activate

3. Install dependencies:  
   pip install \-r requirements.txt

### **Configuration**

1. Copy .env.example to .env.  
2. Edit .env with DISCORD\_BOT\_TOKEN and DISCORD\_GUILD\_NAME. **Do not commit .env\!**  
3. Adjust config.py for specific settings.

### **Discord Bot Configuration**

1. **Enable Message Content Intent:** In [Developer Portal](https://discord.com/developers/applications) \-\> Bot, enable "MESSAGE CONTENT INTENT".  
2. **Invite Bot:** Use OAuth2 URL Generator (scope bot, permissions Read Messages/View Channels, Send Messages).

### **Running the Bot**

From your\_bot\_project directory (venv active):  
python main.py

## **Usage**

* **\!weather**: Get weather for Warsaw.  
* **\!apicount**: Display API call count.
