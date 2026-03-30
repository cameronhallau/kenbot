# KenHallBot

KenHallBot is a local browser app for researching big UK stock moves and drafting an article from that research.

If you are using Windows and you are not technical, start here. You only use `Command Prompt` to start the app. The actual app opens in your web browser.

## What you need before you start

- A Windows computer
- An internet connection
- Python `3.11` or newer
- An `OpenRouter` API key
- An `FMP` API key

You will add the API keys inside the app later.

## Step 1: Download the project files

1. Open your browser.
2. Go to [github.com/cameronhallau/kenbot](https://github.com/cameronhallau/kenbot).
3. Click the green `Code` button.
4. Click `Download ZIP`.
5. When the ZIP file finishes downloading, right-click it and choose `Extract All`.
6. Move the extracted folder somewhere easy to find.

A simple choice is:

```text
C:\KenHallBot
```

If Windows extracts it as something like `kenbot-main`, that is fine too. Just remember the folder name you end up with.

## Step 2: Install Python

1. Go to [python.org/downloads/windows](https://www.python.org/downloads/windows/).
2. Download Python `3.11` or newer.
3. Run the installer.
4. Tick `Add Python to PATH`.
5. Click `Install Now`.

## Step 3: Open Command Prompt

1. Press the `Windows` key.
2. Type `cmd`.
3. Open `Command Prompt`.

## Step 4: Go into the project folder

If your folder is `C:\KenHallBot`, type this and press `Enter`:

```bat
cd /d C:\KenHallBot
```

If your folder has a different name or location, use that path instead.

## Step 5: Set up the app for the first time

Run these commands one at a time:

```bat
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e .
```

If the first command does not work, try this instead:

```bat
py -3 -m venv .venv
```

This setup step is usually only needed once.

## Step 6: Start the app

Still in the same `Command Prompt` window, run:

```bat
kenhallbot-gui
```

If that does not work, use:

```bat
python -m kenhallbot.gui
```

Leave that window open while you use KenHallBot.

## Step 7: Open KenHallBot in your browser

Open your browser and go to:

```text
http://127.0.0.1:5000
```

If everything is working, you will see the KenHallBot interface.

## Step 8: Add your API keys

1. Click the `Settings` tab.
2. Paste your `OpenRouter API key` into the `OpenRouter API key` box.
3. Paste your `FMP API key` into the `FMP API key` box.
4. Leave the model names as they are unless you have been told to change them.
5. Click `Save settings`.

## Step 9: Use the app

The main tabs are:

- `Research setup`: find movers, choose a company, and build the research notes
- `Write and review`: create the draft, edit it, and run the final details pass
- `Complete`: review and save the finished article
- `Settings`: save your keys, models, prompts, style notes, and rules

## What to do next time

After the first setup, you usually only need these commands:

```bat
cd /d C:\KenHallBot
.venv\Scripts\activate
kenhallbot-gui
```

Then open:

```text
http://127.0.0.1:5000
```

If your folder is not `C:\KenHallBot`, use your own path. If `kenhallbot-gui` does not work, use `python -m kenhallbot.gui`.

## How to stop the app

1. Click the `Command Prompt` window where KenHallBot is running.
2. Press `Ctrl` + `C`.

## Where your files are saved

KenHallBot saves generated files in the `output` folder inside the project folder.

## Troubleshooting

### `'py' is not recognized`

Python is either not installed, or it was installed without `Add Python to PATH`.

Fix:

1. Run the Python installer again.
2. Tick `Add Python to PATH`.
3. Try the setup steps again.

### The browser page will not open

Make sure the app is still running in `Command Prompt`, then open:

```text
http://127.0.0.1:5000
```

### `kenhallbot-gui` is not recognized

Use this instead:

```bat
python -m kenhallbot.gui
```

## Technical quick start

If you already know your way around Python, the short version is:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
kenhallbot-gui
```
