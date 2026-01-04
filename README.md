# SIR
## The Robot that tells jokes and wins science fairs

SIR is a joke-telling program that randomly selects and delivers dad jokes from a collection of 500+ jokes. Available as both a command-line tool and a web interface.

## How it Works

SIR reads from a JSON file (`dad_jokes.json`) containing a collection of jokes, each with a setup and punchline. When you ask for a joke, SIR:

1. Loads all jokes from the JSON file
2. Randomly selects one joke
3. Displays the setup (and speaks it if `--speak` is used)
4. Waits for you to press Enter (CLI) or tap (Web)
5. Reveals the punchline with a dad laugh!

## Web Interface

Start the web server:

```bash
pip install -r requirements.txt
python3 web.py
```

Then open your browser to `http://localhost:5000` (or `http://<raspberry-pi-ip>:5000` from another device).

**Features:**
- Beautiful, animated interface
- Tap or click to reveal punchlines
- Confetti celebration on each joke!
- Keyboard shortcuts: Space to reveal, Enter for new joke
- Works great on Raspberry Pi 5

## Command Line Usage

```bash
python3 sir.py joke
```

Or use the shorthand:

```bash
python3 sir.py j
```

### Text-to-Speech

To have SIR speak the jokes out loud with a dad-like voice, use the `--speak` or `-s` flag:

```bash
python3 sir.py joke --speak
```

```bash
python3 sir.py j -s
```

**Voice Features:**
- Uses "Fred" voice on macOS for that classic dad sound
- Speaks at normal pace for natural delivery
- Adds a hearty dad laugh after each punchline: "Ha ha ha ha! That's a good one!"

## Example

Without speech:
```
$ python3 sir.py joke

Why can't a nose be 12 inches long?
Press Enter for the punchline...
Because then it would be a foot!
```

With speech:
```
$ python3 sir.py joke --speak

Why can't a nose be 12 inches long?
[SIR speaks in dad voice: "Why can't a nose be 12 inches long?"]
Press Enter for the punchline...
Because then it would be a foot!
[SIR speaks: "Because then it would be a foot!"]
[SIR laughs: "Ha ha ha ha! That's a good one!"]
```

## Requirements

- Python 3.x
- `dad_jokes.json` file in the same directory

### For Web Interface:
```bash
pip install -r requirements.txt
```

### Optional (for CLI text-to-speech):
- **macOS**: Built-in `say` command (already available)
- **Linux/Raspberry Pi**: Install `espeak` package
  ```bash
  # Ubuntu/Debian/Raspberry Pi OS
  sudo apt-get install espeak
  
  # CentOS/RHEL/Fedora
  sudo yum install espeak
  ```
- **Windows**: Install espeak or use Windows Speech Platform

## Raspberry Pi 5 Setup

```bash
# Install dependencies
sudo apt update
sudo apt install python3-pip espeak

# Install Flask
pip install -r requirements.txt

# Run the web server
python3 web.py
```

Access from any device on your network at `http://<pi-ip-address>:5000`

## File Structure

- `sir.py` - Command line interface
- `web.py` - Flask web interface
- `dad_jokes.json` - Collection of 500+ dad jokes
- `requirements.txt` - Python dependencies
- `README.md` - This file
