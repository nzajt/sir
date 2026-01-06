#!/usr/bin/env python3

import json
import os
import random
import sys
import subprocess
import shutil
import time
import threading

# Get the directory where this script lives
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Servo configuration
SERVO_ENABLED = True
GPIO_PIN = 18
MOUTH_CLOSED = 90   # Degrees when mouth is closed
MOUTH_OPEN = 0      # Degrees when mouth is fully open
MOUTH_HALF = 45     # Degrees for half-open mouth

# Try to import servo control (only works on Raspberry Pi)
servo = None
try:
    os.environ['GPIOZERO_PIN_FACTORY'] = 'lgpio'
    from gpiozero import PWMOutputDevice
    
    class ServoController:
        """Simple servo controller for mouth movement."""
        
        def __init__(self, gpio_pin, min_duty=0.025, max_duty=0.125, freq=50):
            self.gpio = gpio_pin
            self.min_duty = min_duty
            self.max_duty = max_duty
            self.pwm = PWMOutputDevice(gpio_pin, frequency=freq, initial_value=0)
            self.current_angle = None
        
        def angle_to_duty(self, angle):
            angle = max(0, min(180, angle))
            duty_range = self.max_duty - self.min_duty
            return self.min_duty + (angle / 180.0) * duty_range
        
        def set_angle(self, angle):
            """Move servo to angle (0-180)."""
            angle = max(0, min(180, angle))
            self.pwm.value = self.angle_to_duty(angle)
            self.current_angle = angle
        
        def release(self):
            """Stop PWM signal."""
            self.pwm.value = 0
        
        def cleanup(self):
            self.pwm.value = 0
            self.pwm.close()
    
    if SERVO_ENABLED:
        servo = ServoController(GPIO_PIN)
        servo.set_angle(MOUTH_CLOSED)
        time.sleep(0.3)
        servo.release()
        
except Exception as e:
    servo = None
    # Only show warning if servo was supposed to be enabled
    if SERVO_ENABLED and '--speak' in sys.argv or '-s' in sys.argv:
        print(f"Note: Servo not available ({e})")
        print("Running without servo control.\n")


def move_mouth(angle):
    """Move servo to specified angle if available."""
    if servo:
        servo.set_angle(angle)


def mouth_talking_animation(duration=0.5):
    """Animate mouth while talking (open/close pattern)."""
    if not servo:
        return
    
    start_time = time.time()
    while time.time() - start_time < duration:
        move_mouth(MOUTH_OPEN)
        time.sleep(0.15)
        move_mouth(MOUTH_CLOSED)
        time.sleep(0.1)
    
    move_mouth(MOUTH_CLOSED)
    servo.release()


def laugh_animation():
    """
    Animate mouth for laughing: Ha ha ha ha!
    Pattern: closed → open → half → open → half → open → closed
    """
    if not servo:
        return
    
    # Ha
    move_mouth(MOUTH_OPEN)
    time.sleep(0.2)
    move_mouth(MOUTH_HALF)
    time.sleep(0.15)
    
    # ha
    move_mouth(MOUTH_OPEN)
    time.sleep(0.2)
    move_mouth(MOUTH_HALF)
    time.sleep(0.15)
    
    # ha
    move_mouth(MOUTH_OPEN)
    time.sleep(0.2)
    move_mouth(MOUTH_HALF)
    time.sleep(0.15)
    
    # ha!
    move_mouth(MOUTH_OPEN)
    time.sleep(0.3)
    
    # Close mouth
    move_mouth(MOUTH_CLOSED)
    time.sleep(0.2)
    servo.release()


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
    # Prefer pico2wave (more natural) over espeak (robotic)
    if shutil.which('pico2wave'):
        return 'pico2wave'
    elif shutil.which('say'):
        return 'say'
    elif shutil.which('espeak'):
        return 'espeak'
    else:
        return None


def speak_with_pico(text):
    """Speak using pico2wave (more natural voice)."""
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        wav_file = f.name
    subprocess.run(['pico2wave', '-l', 'en-US', '-w', wav_file, text], check=False)
    subprocess.run(['aplay', '-q', wav_file], check=False)
    os.unlink(wav_file)

def speak_text(text, tts_cmd=None, is_laugh=False):
    """Speak text with synchronized mouth movement."""
    if tts_cmd == 'pico2wave':
        if is_laugh:
            if servo:
                animation_thread = threading.Thread(target=laugh_animation)
                animation_thread.start()
            speak_with_pico("Ha ha ha ha! That's a good one!")
            if servo:
                animation_thread.join()
        else:
            if servo:
                duration = max(1.0, len(text) / 8)
                animation_thread = threading.Thread(target=mouth_talking_animation, args=(duration,))
                animation_thread.start()
            speak_with_pico(text)
            if servo:
                animation_thread.join()
                
    elif tts_cmd == 'say':
        if is_laugh:
            # Start laugh animation in parallel with speech
            if servo:
                animation_thread = threading.Thread(target=laugh_animation)
                animation_thread.start()
            subprocess.run(['say', '-v', 'Fred', 'Ha ha ha ha! That\'s a good one!'], check=False)
            if servo:
                animation_thread.join()
        else:
            # Animate mouth while speaking
            if servo:
                # Estimate speech duration (rough: 10 chars per second)
                duration = max(1.0, len(text) / 10)
                animation_thread = threading.Thread(target=mouth_talking_animation, args=(duration,))
                animation_thread.start()
            subprocess.run(['say', '-v', 'Fred', text], check=False)
            if servo:
                animation_thread.join()
                
    elif tts_cmd == 'espeak':
        if is_laugh:
            if servo:
                animation_thread = threading.Thread(target=laugh_animation)
                animation_thread.start()
            subprocess.run(['espeak', '-a', '200', '-s', '120', '-g', '10', 'Ha ha ha ha! That\'s a good one!'], check=False)
            if servo:
                animation_thread.join()
        else:
            if servo:
                duration = max(1.0, len(text) / 8)  # espeak is a bit slower
                animation_thread = threading.Thread(target=mouth_talking_animation, args=(duration,))
                animation_thread.start()
            subprocess.run(['espeak', '-a', '200', '-s', '120', '-g', '10', text], check=False)
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
