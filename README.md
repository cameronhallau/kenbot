# KenHallBot

KenHallBot is a local browser app for researching big UK stock moves and drafting an article from that research.

If you are using a Mac and you are not technical, start here. You only use `Terminal` to start the app. The actual app opens in your web browser.

## What you need before you start

- A Mac
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
5. When the ZIP file finishes downloading, open it to unzip it.
6. Move the extracted folder somewhere easy to find.

A simple choice is:

```text
/Users/yourname/KenHallBot
```

If your Mac saves it as something like `kenbot-main`, that is fine too. Just remember the folder name you end up with.

## Step 2: Install Python

1. Go to [python.org/downloads/macos](https://www.python.org/downloads/macos/).
2. Download Python `3.11` or newer.
3. Run the installer.
4. Follow the installer steps to finish the install.

## Step 3: Open Terminal

1. Press `Command` + `Space`.
2. Type `Terminal`.
3. Open `Terminal`.

## Step 4: Go into the project folder

If your folder is `KenHallBot` in your home folder, type this and press `Enter`:

```bash
cd ~/KenHallBot
```

If your folder is still in `Downloads` and is called `kenbot-main`, use:

```bash
cd ~/Downloads/kenbot-main
```

If your folder has a different name or location, use that path instead.

## Step 5: Set up the app for the first time

Run these commands one at a time:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
pip install -e .
```

This setup step is usually only needed once.

## Step 6: Start the app

Still in the same `Terminal` window, run:

```bash
kenhallbot-gui
```

If that does not work, use:

```bash
python3 -m kenhallbot.gui
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

```bash
cd ~/KenHallBot
source .venv/bin/activate
kenhallbot-gui
```

Then open:

```text
http://127.0.0.1:5000
```

If your folder is not `~/KenHallBot`, use your own path. If `kenhallbot-gui` does not work, use `python3 -m kenhallbot.gui`.

## How to stop the app

1. Click the `Terminal` window where KenHallBot is running.
2. Press `Ctrl` + `C`.

## Where your files are saved

KenHallBot saves generated files in the `output` folder inside the project folder.

## Troubleshooting

### `python3: command not found`

Python is either not installed, or the installation did not finish properly.

Fix:

1. Run the Python installer again.
2. Finish the install.
3. Open a new `Terminal` window and try again.

### The browser page will not open

Make sure the app is still running in `Terminal`, then open:

```text
http://127.0.0.1:5000
```

### `kenhallbot-gui` is not recognized

Use this instead:

```bash
python3 -m kenhallbot.gui
```

## Technical quick start

If you already know your way around Python, the short version is:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
pip install -e .
kenhallbot-gui
```
