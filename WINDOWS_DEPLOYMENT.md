# KenHallBot Windows Deployment Guide

This guide is written for someone who is not technical. Follow the steps in order.

## What you are setting up

You are installing KenHallBot on a Windows computer so you can open it in your browser and use the local GUI.

When it is running, you will open:

```text
http://127.0.0.1:5000
```

## Before you start

You will need:

- A Windows PC
- An internet connection
- Your `OPENAI_API_KEY`
- Optional: your `FMP_API_KEY`
- Optional: your `OPENROUTER_API_KEY` if you want to use OpenRouter

## Step 1: Install Python

1. Open your web browser.
2. Go to [python.org/downloads/windows](https://www.python.org/downloads/windows/).
3. Download Python 3.11 or newer.
4. Run the installer.
5. Very important: tick `Add Python to PATH`.
6. Click `Install Now`.
7. Wait until the install finishes.

## Step 2: Download the project

If you already have the project folder on your computer, skip to Step 3.

1. Open your browser.
2. Go to [github.com/cameronhallau/kenbot](https://github.com/cameronhallau/kenbot).
3. Click the green `Code` button.
4. Click `Download ZIP`.
5. When the ZIP finishes downloading, right-click it and choose `Extract All`.
6. Put the extracted folder somewhere easy to find, such as:

```text
C:\KenHallBot
```

## Step 3: Open Command Prompt

1. Press the `Windows` key.
2. Type `cmd`.
3. Click `Command Prompt`.

You will now type the commands below into that window.

## Step 4: Go into the project folder

If your folder is in `C:\KenHallBot`, run:

```bat
cd /d C:\KenHallBot
```

If your folder has a different name or location, replace the path with your own.

## Step 5: Create the app environment

Run these commands one at a time:

```bat
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e .
```

What this does:

- Creates a private Python environment for this app
- Turns that environment on
- Updates pip
- Installs KenHallBot

If `py -3.11` does not work, try:

```bat
py -3 -m venv .venv
```

## Step 6: Add your API keys

1. Open File Explorer.
2. Open your KenHallBot folder.
3. Find the file called `.env.example`.
4. Right-click it and choose `Copy`.
5. Right-click in the same folder and choose `Paste`.
6. Rename the new file to:

```text
.env
```

7. Right-click `.env`.
8. Choose `Open with`.
9. Choose `Notepad`.

You will see something like this:

```text
OPENAI_API_KEY=
FMP_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
LLM_PROVIDER=openai
OPENROUTER_API_KEY=
OPENROUTER_MODEL=openai/gpt-4.1-mini
ARTICLE_OPENROUTER_MODEL=anthropic/claude-sonnet-4.6
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_SITE_URL=
OPENROUTER_APP_NAME=KenHallBot
```

### Minimum setup

Paste your OpenAI key after `OPENAI_API_KEY=` like this:

```text
OPENAI_API_KEY=your_key_here
```

### Optional FMP key

If you have an FMP key, add it here:

```text
FMP_API_KEY=your_key_here
```

### Optional OpenRouter setup

If you want to use OpenRouter instead of OpenAI for the main LLM calls:

1. Change this line:

```text
LLM_PROVIDER=openai
```

to:

```text
LLM_PROVIDER=openrouter
```

2. Add your OpenRouter key here:

```text
OPENROUTER_API_KEY=your_key_here
```

3. Save the file in Notepad.
4. Close Notepad.

## Step 7: Start the app

Go back to Command Prompt and make sure you are still in the project folder.

If needed, run these again:

```bat
cd /d C:\KenHallBot
.venv\Scripts\activate
```

Then start the app:

```bat
kenhallbot-gui
```

If that does not work, use:

```bat
python -m kenhallbot.gui
```

## Step 8: Open the app

1. Open your web browser.
2. Go to:

```text
http://127.0.0.1:5000
```

You should now see the KenHallBot interface.

## How to use it next time

Each time you want to launch it again:

1. Open `Command Prompt`
2. Run:

```bat
cd /d C:\KenHallBot
.venv\Scripts\activate
kenhallbot-gui
```

3. Open:

```text
http://127.0.0.1:5000
```

## How to stop the app

If the app is running in Command Prompt and you want to stop it:

1. Click the Command Prompt window where KenHallBot is running
2. Press `Ctrl` + `C`

That stops the local server.

## How to force-close it if needed

If the app will not stop, or if the old session is still holding port `5000`:

1. Open `Command Prompt`
2. Run:

```bat
netstat -ano | findstr :5000
```

3. Look at the number in the far-right column. That is the PID.
4. Run this, replacing `PID_NUMBER` with the number you found:

```bat
taskkill /PID PID_NUMBER /F
```

Example:

```bat
taskkill /PID 12345 /F
```

This force-stops the app using port `5000`.

## How to relaunch after stopping it

1. Open `Command Prompt`
2. Run:

```bat
cd /d C:\KenHallBot
.venv\Scripts\activate
kenhallbot-gui
```

3. Open:

```text
http://127.0.0.1:5000
```

If `kenhallbot-gui` does not work, use:

```bat
python -m kenhallbot.gui
```

## How to update to the latest version

If you downloaded the folder as a ZIP, the simplest update is:

1. Download the latest ZIP again from [github.com/cameronhallau/kenbot](https://github.com/cameronhallau/kenbot)
2. Extract it
3. Move your `.env` file into the new folder
4. Open `Command Prompt`
5. Run:

```bat
cd /d C:\KenHallBot
.venv\Scripts\activate
pip install -e .
```

Then launch it again with:

```bat
kenhallbot-gui
```

## Where files are saved

Generated output is saved in the `output` folder inside the project.

Important editable files:

- `.env` for your API keys and app settings
- `config\style_notes.md` for writing style guidance
- `config\motley_rules_uk.md` for article rules

## Troubleshooting

### I see `'py' is not recognized`

Python is not installed, or it was installed without `Add Python to PATH`.

Fix:

1. Re-run the Python installer
2. Tick `Add Python to PATH`
3. Try again

### I see `No module named ...`

The app is not installed yet in the virtual environment.

Fix:

```bat
cd /d C:\KenHallBot
.venv\Scripts\activate
pip install -e .
```

### The browser page does not open

Make sure the app is still running in Command Prompt. That window must stay open while you use the app.

Then open:

```text
http://127.0.0.1:5000
```

### Port 5000 is already in use

Close any older KenHallBot Command Prompt windows and try again.

If that does not fix it, run:

```bat
netstat -ano | findstr :5000
taskkill /PID PID_NUMBER /F
```

Then relaunch:

```bat
cd /d C:\KenHallBot
.venv\Scripts\activate
kenhallbot-gui
```

### The app says an API key is missing

Open `.env` in Notepad and make sure your key is pasted after the correct line with no extra spaces.

## Simple one-page launch summary

1. Open `Command Prompt`
2. Run:

```bat
cd /d C:\KenHallBot
.venv\Scripts\activate
kenhallbot-gui
```

3. Open [http://127.0.0.1:5000](http://127.0.0.1:5000)
