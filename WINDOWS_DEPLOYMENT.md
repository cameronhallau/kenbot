# KenHallBot Windows Deployment Guide

This guide is for a non-technical user.

The important thing to know is this:

- `Command Prompt` is only used to start the app
- The actual app is a browser GUI
- You use it at `http://127.0.0.1:5000`

## What this app looks like

When KenHallBot is running, you open it in your web browser and use these tabs:

- `Research setup`
- `Write and review`
- `Complete`
- `Settings`

You do not control the app by typing article commands into Command Prompt.

## Before you start

You will need:

- A Windows PC
- An internet connection
- An OpenRouter API key

This guide uses the GUI `Settings` tab to add your key, because that matches how the app works today.

## Step 1: Install Python

1. Open your web browser.
2. Go to [python.org/downloads/windows](https://www.python.org/downloads/windows/).
3. Download Python 3.11 or newer.
4. Run the installer.
5. Tick `Add Python to PATH`.
6. Click `Install Now`.

## Step 2: Download the project

If you already have the project folder on your computer, skip to Step 3.

1. Open your browser.
2. Go to [github.com/cameronhallau/kenbot](https://github.com/cameronhallau/kenbot).
3. Click the green `Code` button.
4. Click `Download ZIP`.
5. When the ZIP finishes downloading, right-click it and choose `Extract All`.
6. Put the extracted folder somewhere simple, for example:

```text
C:\KenHallBot
```

## Step 3: Open Command Prompt

1. Press the `Windows` key.
2. Type `cmd`.
3. Click `Command Prompt`.

## Step 4: Go into the project folder

If your folder is in `C:\KenHallBot`, run:

```bat
cd /d C:\KenHallBot
```

If your folder is somewhere else, replace the path with your own.

## Step 5: Set up the app

Run these commands one at a time:

```bat
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e .
```

If `py -3.11` does not work, try:

```bat
py -3 -m venv .venv
```

## Step 6: Start the local GUI server

Still in Command Prompt, run:

```bat
kenhallbot-gui
```

If that does not work, run:

```bat
python -m kenhallbot.gui
```

Keep that Command Prompt window open while you use the app.

## Step 7: Open the app in your browser

1. Open your web browser.
2. Go to:

```text
http://127.0.0.1:5000
```

You should now see the KenHallBot GUI.

## Step 8: Add your API key in the GUI

1. Click the `Settings` tab.
2. Find the field called `OpenRouter API key`.
3. Paste your key into that field.
4. Leave the default model values in place unless you have been told to change them.
5. Click `Save settings`.

This saves your key and model settings for future use.

## Step 9: Use the app

### Research setup tab

Use `Research setup` to prepare the company information.

1. Click `Refresh movers`
2. Pick a company from the list
3. Check or edit the working brief
4. Click `Build research`

This builds the material that feeds the writing tab.

### Write and review tab

Use `Write and review` to create the article.

1. Click the `Write and review` tab
2. Click `Construct Prompt`
3. Review or edit the prompt text if needed
4. Click `Generate draft`
5. Review or edit the article draft
6. Click `Final details pass` when you want the polished version

### Complete tab

Use `Complete` when you want to save the final article.

1. Click the `Complete` tab
2. Review the completed article
3. Click `Save completed article`

## The only Command Prompt job

Command Prompt is only there to do this:

- start the local server
- keep it running while you use the browser app
- stop it when you are done

All normal app work happens in the web browser.

## How to open it next time

Each time you want to use KenHallBot again:

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

If you want to stop KenHallBot:

1. Click the Command Prompt window where it is running
2. Press `Ctrl` + `C`

That stops the local server on port `5000`.

## How to force-close it if needed

If the app will not stop, or if port `5000` is still busy:

1. Open `Command Prompt`
2. Run:

```bat
netstat -ano | findstr :5000
```

3. Look at the number in the far-right column
4. Run this, replacing `PID_NUMBER` with that number:

```bat
taskkill /PID PID_NUMBER /F
```

Example:

```bat
taskkill /PID 12345 /F
```

## How to relaunch it

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

## Where files are saved

Generated files are saved in the `output` folder inside the project.

If you need to edit writing or rules files manually later, look in the `config` folder.

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

Make sure the Command Prompt window is still open and the app is still running.

Then open:

```text
http://127.0.0.1:5000
```

### Port 5000 is already in use

Run:

```bat
netstat -ano | findstr :5000
taskkill /PID PID_NUMBER /F
```

Then start the app again:

```bat
cd /d C:\KenHallBot
.venv\Scripts\activate
kenhallbot-gui
```

### The app says a key is missing

Open the app in your browser, go to `Settings`, paste your `OpenRouter API key`, and click `Save settings`.

## Simple launch summary

1. Open `Command Prompt`
2. Run:

```bat
cd /d C:\KenHallBot
.venv\Scripts\activate
kenhallbot-gui
```

3. Open [http://127.0.0.1:5000](http://127.0.0.1:5000)
4. Click `Settings`, paste your OpenRouter API key, and click `Save settings`
