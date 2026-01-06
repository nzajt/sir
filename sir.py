#!/usr/bin/env python3

import json
import os
import random
import sys
import threading
import time

# Get the directory where this script lives
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Add lib to path for imports
sys.path.insert(0, SCRIPT_DIR)

from bbb.servo import (
    init_servo,
    get_servo,
    move_mouth,
    mouth_talking_animation,
    laugh_animation,
    MOUTH_CLOSED,
)
from bbb.tts import (
    check_tts_available,
    speak_text_sync,
)

# Initialize servo
servo, servo_error = init_servo()


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


def speak_text(text, tts_cmd=None, is_laugh=False):
    """Speak text with synchronized mouth movement."""
    if tts_cmd == 'pico2wave' or tts_cmd == 'espeak':
        if is_laugh:
            if servo:
                animation_thread = threading.Thread(target=laugh_animation)
                animation_thread.start()
            speak_text_sync("", is_laugh=True, tts_cmd=tts_cmd)
            if servo:
                animation_thread.join()
        else:
            if servo:
                duration = max(1.0, len(text) / 8)
                animation_thread = threading.Thread(target=mouth_talking_animation, args=(duration,))
                animation_thread.start()
            speak_text_sync(text, tts_cmd=tts_cmd)
            if servo:
                animation_thread.join()
                
    elif tts_cmd == 'say':
        if is_laugh:
            if servo:
                animation_thread = threading.Thread(target=laugh_animation)
                animation_thread.start()
            speak_text_sync("", is_laugh=True, tts_cmd=tts_cmd)
            if servo:
                animation_thread.join()
        else:
            if servo:
                duration = max(1.0, len(text) / 10)
                animation_thread = threading.Thread(target=mouth_talking_animation, args=(duration,))
                animation_thread.start()
            speak_text_sync(text, tts_cmd=tts_cmd)
            if servo:
                animation_thread.join()


def tell_joke(joke, use_speech=False):
    tts_cmd = check_tts_available() if use_speech else None
    
    # Close mouth at start
    if servo:
        move_mouth(MOUTH_CLOSED)
        time.sleep(0.2)
    
    print(f"\n{joke['setup']}")
    if use_speech and tts_cmd:
        speak_text(joke['setup'], tts_cmd)
    
    # Release servo while waiting for input
    if servo:
        servo.release()
    
    input("Press Enter for the punchline...")
    
    print(f"{joke['punchline']}\n")
    if use_speech and tts_cmd:
        speak_text(joke['punchline'], tts_cmd)
        time.sleep(0.5)
        speak_text("", tts_cmd, is_laugh=True)
    
    # Make sure servo is released at the end
    if servo:
        time.sleep(0.3)
        servo.release()


def main():
    if len(sys.argv) > 1 and sys.argv[1].lower() in ['joke', 'tell', 'j']:
        use_speech = '--speak' in sys.argv or '-s' in sys.argv
        
        if use_speech and not check_tts_available():
            print("Warning: No text-to-speech engine found. Install espeak or use macOS 'say' command.")
            print("Continuing without speech...")
            use_speech = False
        
        # Show servo status
        if servo:
            print("🤖 Servo connected - mouth will animate!")
        
        try:
            jokes = load_jokes()
            joke = get_random_joke(jokes)
            tell_joke(joke, use_speech)
        finally:
            # Clean up servo
            if servo:
                servo.cleanup()
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
        print("")
        if servo:
            print("  🤖 Servo: Connected (GPIO 18)")
        else:
            print("  🤖 Servo: Not available (run on Raspberry Pi)")


if __name__ == "__main__":
    main()
