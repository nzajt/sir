#!/usr/bin/env python3

import json
import os
import random
import sys
import subprocess
import shutil
import time

# Get the directory where this script lives
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def load_jokes():
    try:
        jokes_path = os.path.join(SCRIPT_DIR, 'dad_jokes.json')
        with open(jokes_path, 'r') as f:
            data = json.load(f)
            return data['jokes']
    except FileNotFoundError:
        print("Error: dad_jokes.json file not found!")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in dad_jokes.json!")
        sys.exit(1)

def get_random_joke(jokes):
    return random.choice(jokes)

def check_tts_available():
    if shutil.which('say'):
        return 'say'
    elif shutil.which('espeak'):
        return 'espeak'
    else:
        return None

def speak_text(text, tts_cmd=None, is_laugh=False):
    if tts_cmd == 'say':
        if is_laugh:
            subprocess.run(['say', '-v', 'Fred', 'Ha ha ha ha! That\'s a good one!'], check=False)
        else:
            subprocess.run(['say', '-v', 'Fred', text], check=False)
    elif tts_cmd == 'espeak':
        if is_laugh:
            subprocess.run(['espeak', 'Ha ha ha ha! That\'s a good one!'], check=False)
        else:
            subprocess.run(['espeak', text], check=False)

def tell_joke(joke, use_speech=False):
    tts_cmd = check_tts_available() if use_speech else None
    
    print(f"\n{joke['setup']}")
    if use_speech and tts_cmd:
        speak_text(joke['setup'], tts_cmd)
    
    input("Press Enter for the punchline...")
    
    print(f"{joke['punchline']}\n")
    if use_speech and tts_cmd:
        speak_text(joke['punchline'], tts_cmd)
        time.sleep(0.5)
        speak_text("", tts_cmd, is_laugh=True)


def main():
    if len(sys.argv) > 1 and sys.argv[1].lower() in ['joke', 'tell', 'j']:
        use_speech = '--speak' in sys.argv or '-s' in sys.argv
        
        if use_speech and not check_tts_available():
            print("Warning: No text-to-speech engine found. Install espeak or use macOS 'say' command.")
            print("Continuing without speech...")
            use_speech = False
            
        jokes = load_jokes()
        joke = get_random_joke(jokes)
        tell_joke(joke, use_speech)
    else:
        print("Usage: python sir.py joke [--speak|-s]")
        print("Alternative: python sir.py j [--speak|-s]")
        print("")
        print("Options:")
        print("  --speak, -s    Tell the joke out loud using text-to-speech")
        tts_cmd = check_tts_available()
        if tts_cmd:
            print(f"  Text-to-speech engine detected: {tts_cmd}")
        else:
            print("  No text-to-speech engine found")

if __name__ == "__main__":
    main()