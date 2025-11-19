# SIR
## The Robot that tells jokes and wins science fairs

SIR is a command line joke-telling program that randomly selects and delivers dad jokes from a collection of 500+ jokes.

## How it Works

SIR reads from a JSON file (`dad_jokes.json`) containing a collection of jokes, each with a setup and punchline. When you ask for a joke, SIR:

1. Loads all jokes from the JSON file
2. Randomly selects one joke
3. Displays the setup (and speaks it if `--speak` is used)
4. Waits for you to press Enter
5. Reveals the punchline (and speaks it if `--speak` is used)

## Usage

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

### Optional (for text-to-speech):
- **macOS**: Built-in `say` command (already available)
- **Linux**: Install `espeak` package
  ```bash
  # Ubuntu/Debian
  sudo apt-get install espeak
  
  # CentOS/RHEL/Fedora
  sudo yum install espeak
  ```
- **Windows**: Install espeak or use Windows Speech Platform

## File Structure

- `sir.py` - The main program
- `dad_jokes.json` - Collection of 500+ dad jokes
- `README.md` - This file
