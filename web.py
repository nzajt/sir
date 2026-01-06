#!/usr/bin/env python3

from flask import Flask, render_template_string, jsonify, request
import json
import os
import random
import shutil
import subprocess
import threading
import time

app = Flask(__name__)

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
servo_lock = threading.Lock()
servo_error = None  # Store error message for debugging

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
    
    # Only initialize servo in the main Flask process, not the reloader
    # In debug mode, Flask runs twice - skip servo init in the reloader process
    is_reloader = os.environ.get('WERKZEUG_RUN_MAIN') != 'true' and os.environ.get('FLASK_DEBUG') == '1'
    
    if SERVO_ENABLED and not is_reloader:
        servo = ServoController(GPIO_PIN)
        servo.set_angle(MOUTH_CLOSED)
        time.sleep(0.3)
        servo.release()
        print("🤖 Servo initialized on GPIO", GPIO_PIN)
    elif is_reloader:
        print("⏳ Skipping servo init in reloader process...")
        
except Exception as e:
    servo = None
    servo_error = str(e)
    print(f"⚠️  Servo error: {e}")
    print("Running without servo control.")
    import traceback
    traceback.print_exc()


def move_mouth(angle):
    """Move servo to specified angle if available."""
    if servo:
        with servo_lock:
            servo.set_angle(angle)


def mouth_talking_animation(duration=2.0):
    """Animate mouth while talking (open/close pattern)."""
    if not servo:
        return
    
    start_time = time.time()
    while time.time() - start_time < duration:
        with servo_lock:
            servo.set_angle(MOUTH_OPEN)
        time.sleep(0.15)
        with servo_lock:
            servo.set_angle(MOUTH_CLOSED)
        time.sleep(0.1)
    
    with servo_lock:
        servo.set_angle(MOUTH_CLOSED)
        servo.release()


def laugh_animation():
    """
    Animate mouth for laughing: Ha ha ha ha!
    Pattern: closed → open → half → open → half → open → closed
    """
    if not servo:
        return
    
    with servo_lock:
        # Ha
        servo.set_angle(MOUTH_OPEN)
    time.sleep(0.2)
    with servo_lock:
        servo.set_angle(MOUTH_HALF)
    time.sleep(0.15)
    
    # ha
    with servo_lock:
        servo.set_angle(MOUTH_OPEN)
    time.sleep(0.2)
    with servo_lock:
        servo.set_angle(MOUTH_HALF)
    time.sleep(0.15)
    
    # ha
    with servo_lock:
        servo.set_angle(MOUTH_OPEN)
    time.sleep(0.2)
    with servo_lock:
        servo.set_angle(MOUTH_HALF)
    time.sleep(0.15)
    
    # ha!
    with servo_lock:
        servo.set_angle(MOUTH_OPEN)
    time.sleep(0.3)
    
    # Close mouth
    with servo_lock:
        servo.set_angle(MOUTH_CLOSED)
    time.sleep(0.2)
    with servo_lock:
        servo.release()


# Text-to-speech configuration
tts_command = None
tts_lock = threading.Lock()

def check_tts_available():
    """Check which TTS engine is available."""
    if shutil.which('espeak'):
        return 'espeak'
    elif shutil.which('say'):
        return 'say'
    return None

# Initialize TTS
tts_command = check_tts_available()
if tts_command:
    print(f"🔊 TTS initialized: {tts_command}")
else:
    print("⚠️  No TTS available (install espeak: sudo apt install espeak)")

def speak_text_sync(text, is_laugh=False):
    """Speak text using system TTS (blocking)."""
    if not tts_command:
        return
    
    with tts_lock:
        try:
            if is_laugh:
                text = "Ha ha ha ha! That's a good one!"
            
            if tts_command == 'espeak':
                # -a 200 = max volume, -s 120 = slower speed, -g 10 = gaps between words
                subprocess.run(['espeak', '-a', '200', '-s', '120', '-g', '10', text], check=False)
            elif tts_command == 'say':
                subprocess.run(['say', '-v', 'Fred', text], check=False)
        except Exception as e:
            print(f"TTS error: {e}")

def speak_text_async(text, is_laugh=False):
    """Speak text in a background thread."""
    thread = threading.Thread(target=speak_text_sync, args=(text, is_laugh))
    thread.start()
    return thread


def load_jokes():
    jokes_path = os.path.join(SCRIPT_DIR, 'dad_jokes.json')
    with open(jokes_path, 'r') as f:
        data = json.load(f)
        return data['jokes']

JOKES = load_jokes()

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BBB - The Boredom Buster Bot</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Bangers&family=Patrick+Hand&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            min-height: 100vh;
            font-family: 'Patrick Hand', cursive;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            color: #fff;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
            overflow-x: hidden;
        }

        /* Floating emoji background */
        .bg-emoji {
            position: fixed;
            font-size: 2rem;
            opacity: 0.1;
            animation: float 20s infinite ease-in-out;
            pointer-events: none;
            z-index: 0;
        }

        @keyframes float {
            0%, 100% { transform: translateY(0) rotate(0deg); }
            25% { transform: translateY(-20px) rotate(5deg); }
            50% { transform: translateY(0) rotate(0deg); }
            75% { transform: translateY(20px) rotate(-5deg); }
        }

        .container {
            max-width: 700px;
            width: 100%;
            text-align: center;
            z-index: 1;
            position: relative;
        }

        .header {
            margin-bottom: 2rem;
        }

        .title {
            font-family: 'Bangers', cursive;
            font-size: 4.5rem;
            color: #e94560;
            text-shadow: 4px 4px 0 #533483, 8px 8px 0 rgba(0,0,0,0.2);
            letter-spacing: 0.1em;
            animation: titleBounce 2s ease-in-out infinite;
        }

        @keyframes titleBounce {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.02); }
        }

        .subtitle {
            font-size: 1.5rem;
            color: #a2d5f2;
            margin-top: 0.5rem;
            opacity: 0.9;
        }

        .robot-icon {
            font-size: 5rem;
            display: block;
            margin: 1rem auto;
            animation: robotWobble 3s ease-in-out infinite;
        }

        @keyframes robotWobble {
            0%, 100% { transform: rotate(-5deg); }
            50% { transform: rotate(5deg); }
        }

        .joke-card {
            background: linear-gradient(145deg, #533483 0%, #e94560 100%);
            border-radius: 24px;
            padding: 3rem 2rem;
            margin: 2rem 0;
            box-shadow: 
                0 20px 60px rgba(233, 69, 96, 0.3),
                0 0 0 1px rgba(255,255,255,0.1) inset;
            position: relative;
            overflow: hidden;
        }

        .joke-card::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 60%);
            animation: shimmer 8s linear infinite;
        }

        @keyframes shimmer {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .setup {
            font-size: 1.8rem;
            line-height: 1.4;
            margin-bottom: 1.5rem;
            position: relative;
            z-index: 1;
        }

        .punchline-container {
            min-height: 80px;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            z-index: 1;
        }

        .punchline {
            font-size: 2rem;
            font-weight: bold;
            color: #ffd93d;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            opacity: 0;
            transform: translateY(20px) scale(0.8);
            transition: all 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
        }

        .punchline.revealed {
            opacity: 1;
            transform: translateY(0) scale(1);
        }

        .reveal-prompt {
            color: rgba(255,255,255,0.7);
            font-size: 1.2rem;
            cursor: pointer;
            padding: 0.8rem 1.5rem;
            border: 2px dashed rgba(255,255,255,0.4);
            border-radius: 12px;
            transition: all 0.3s ease;
            animation: pulse 2s ease-in-out infinite;
        }

        .reveal-prompt:hover {
            background: rgba(255,255,255,0.1);
            border-color: rgba(255,255,255,0.8);
        }

        @keyframes pulse {
            0%, 100% { opacity: 0.7; }
            50% { opacity: 1; }
        }

        .reveal-prompt.hidden {
            display: none;
        }

        .laugh {
            font-size: 1.5rem;
            margin-top: 1rem;
            opacity: 0;
            transition: opacity 0.5s ease 0.3s;
        }

        .laugh.visible {
            opacity: 1;
        }

        .btn {
            font-family: 'Bangers', cursive;
            font-size: 1.5rem;
            letter-spacing: 0.05em;
            padding: 1rem 2.5rem;
            border: none;
            border-radius: 50px;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .btn-primary {
            background: linear-gradient(135deg, #ffd93d 0%, #ff6b6b 100%);
            color: #1a1a2e;
            box-shadow: 0 8px 30px rgba(255, 217, 61, 0.4);
        }

        .btn-primary:hover {
            transform: translateY(-3px) scale(1.05);
            box-shadow: 0 12px 40px rgba(255, 217, 61, 0.5);
        }

        .btn-primary:active {
            transform: translateY(0) scale(0.98);
        }

        .btn::after {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            background: rgba(255,255,255,0.3);
            border-radius: 50%;
            transform: translate(-50%, -50%);
            transition: width 0.6s ease, height 0.6s ease;
        }

        .btn:active::after {
            width: 300px;
            height: 300px;
        }

        .stats {
            margin-top: 2rem;
            color: #a2d5f2;
            font-size: 1rem;
            opacity: 0.7;
        }

        .controls {
            display: flex;
            gap: 1rem;
            justify-content: center;
            align-items: center;
            flex-wrap: wrap;
        }

        .btn-sound {
            background: rgba(255,255,255,0.1);
            color: #fff;
            border: 2px solid rgba(255,255,255,0.3);
            font-size: 1.2rem;
            padding: 0.8rem 1.5rem;
        }

        .btn-sound:hover {
            background: rgba(255,255,255,0.2);
            border-color: rgba(255,255,255,0.5);
            transform: translateY(-2px);
        }

        .btn-sound.active {
            background: linear-gradient(135deg, #533483 0%, #e94560 100%);
            border-color: #e94560;
            box-shadow: 0 4px 20px rgba(233, 69, 96, 0.4);
        }

        .speaking-indicator {
            display: inline-block;
            margin-left: 0.5rem;
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        .speaking-indicator.active {
            opacity: 1;
            animation: speakPulse 0.5s ease-in-out infinite;
        }

        @keyframes speakPulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.2); }
        }

        .servo-status {
            font-size: 0.85rem;
            margin-top: 0.5rem;
        }

        .servo-status.connected {
            color: #4ade80;
        }

        .servo-status.disconnected {
            color: #f87171;
        }

        .servo-controls {
            margin-top: 1.5rem;
            padding: 1rem;
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.1);
        }

        .servo-controls-title {
            font-size: 1rem;
            color: #a2d5f2;
            margin-bottom: 0.75rem;
        }

        .servo-buttons {
            display: flex;
            gap: 0.5rem;
            justify-content: center;
            flex-wrap: wrap;
        }

        .btn-servo {
            background: rgba(255,255,255,0.1);
            color: #fff;
            border: 1px solid rgba(255,255,255,0.2);
            font-size: 0.9rem;
            padding: 0.5rem 1rem;
            border-radius: 8px;
        }

        .btn-servo:hover {
            background: rgba(255,255,255,0.2);
            border-color: rgba(255,255,255,0.4);
            transform: translateY(-2px);
        }

        .btn-servo:active {
            transform: translateY(0);
            background: rgba(83, 52, 131, 0.5);
        }

        .servo-angle {
            font-size: 0.85rem;
            color: #ffd93d;
            margin-top: 0.5rem;
        }

        .footer {
            margin-top: 3rem;
            color: rgba(255,255,255,0.4);
            font-size: 0.9rem;
        }

        /* Confetti animation on reveal */
        .confetti {
            position: fixed;
            width: 10px;
            height: 10px;
            pointer-events: none;
            z-index: 100;
            animation: confettiFall 3s ease-out forwards;
        }

        @keyframes confettiFall {
            0% {
                transform: translateY(0) rotate(0deg);
                opacity: 1;
            }
            100% {
                transform: translateY(100vh) rotate(720deg);
                opacity: 0;
            }
        }

        @media (max-width: 600px) {
            .title {
                font-size: 3rem;
            }
            .setup {
                font-size: 1.4rem;
            }
            .punchline {
                font-size: 1.6rem;
            }
            .joke-card {
                padding: 2rem 1.5rem;
            }
        }
    </style>
</head>
<body>
    <!-- Floating background emojis -->
    <div class="bg-emoji" style="top: 10%; left: 5%;">🤖</div>
    <div class="bg-emoji" style="top: 20%; right: 10%; animation-delay: -5s;">😂</div>
    <div class="bg-emoji" style="top: 60%; left: 8%; animation-delay: -10s;">🎭</div>
    <div class="bg-emoji" style="top: 80%; right: 15%; animation-delay: -15s;">👨</div>
    <div class="bg-emoji" style="top: 40%; right: 5%; animation-delay: -7s;">🎤</div>
    <div class="bg-emoji" style="bottom: 10%; left: 15%; animation-delay: -12s;">😆</div>

    <div class="container">
        <header class="header">
            <span class="robot-icon">🤖</span>
            <h1 class="title">B.B.B.</h1>
            <p class="subtitle">The Boredom Buster Bot</p>
        </header>

        <div class="joke-card">
            <p class="setup" id="setup">{{ setup }}</p>
            <div class="punchline-container">
                <span class="reveal-prompt" id="revealBtn" onclick="revealPunchline()">
                    👆 Tap to reveal punchline
                </span>
                <p class="punchline" id="punchline">{{ punchline }}</p>
            </div>
            <p class="laugh" id="laugh">😂 Ha ha ha! That's a good one!</p>
        </div>

        <div class="controls">
            <button class="btn btn-primary" onclick="getNewJoke()">
                🎲 Another Joke!
            </button>
            <button class="btn btn-sound" id="soundBtn" onclick="toggleSound()">
                🔇 Sound Off
            </button>
        </div>

        <p class="stats">
            Serving {{ total_jokes }} premium dad jokes 
            <span class="speaking-indicator" id="speakingIndicator">🗣️</span>
        </p>
        <p class="servo-status {{ 'connected' if servo_connected else 'disconnected' }}" id="servoStatus">
            🤖 Servo: {{ 'Connected' if servo_connected else 'Not connected' }}
            {% if servo_error %}
            <br><span style="font-size: 0.8rem; color: #f87171;">Error: {{ servo_error }}</span>
            {% endif %}
        </p>
        <p class="servo-status {{ 'connected' if tts_available else 'disconnected' }}">
            🔊 TTS: {{ tts_engine if tts_available else 'Not available (install espeak)' }}
        </p>

        <!-- Servo Test Controls -->
        <div class="servo-controls">
            <p class="servo-controls-title">🔧 Servo Test</p>
            <div class="servo-buttons">
                <button class="btn btn-servo" onclick="servoUp()">⬆️ Mouth Open</button>
                <button class="btn btn-servo" onclick="servoDown()">⬇️ Mouth Closed</button>
                <button class="btn btn-servo" onclick="servoTest()">🔄 Test Cycle</button>
            </div>
            <p class="servo-angle" id="servoAngle">Angle: --</p>
        </div>

        <footer class="footer">
            <p>The Boredom Buster Bot • Built for science fairs & Raspberry Pi 5</p>
        </footer>
    </div>

    <script>
        let punchlineRevealed = false;
        let soundEnabled = false;
        const servoConnected = {{ 'true' if servo_connected else 'false' }};
        const ttsAvailable = {{ 'true' if tts_available else 'false' }};

        // Servo control functions
        function triggerServoTalk(duration) {
            if (!servoConnected) return;
            fetch('/api/servo/talk?duration=' + duration).catch(() => {});
        }

        function triggerServoLaugh() {
            if (!servoConnected) return;
            fetch('/api/servo/laugh').catch(() => {});
        }

        function triggerServoRelease() {
            if (!servoConnected) return;
            fetch('/api/servo/release').catch(() => {});
        }

        function setServoAngle(angle) {
            fetch('/api/servo/angle?angle=' + angle)
                .then(response => response.json())
                .then(data => {
                    document.getElementById('servoAngle').textContent = 'Angle: ' + angle + '°';
                })
                .catch(() => {
                    document.getElementById('servoAngle').textContent = 'Error!';
                });
        }

        function servoUp() {
            setServoAngle(0);  // Mouth open
        }

        function servoDown() {
            setServoAngle(90);  // Mouth closed
        }

        function servoTest() {
            document.getElementById('servoAngle').textContent = 'Testing...';
            fetch('/api/servo/test')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('servoAngle').textContent = 'Test complete!';
                })
                .catch(() => {
                    document.getElementById('servoAngle').textContent = 'Error!';
                });
        }

        function speak(text, onEnd = null, isLaugh = false, skipServo = false) {
            if (!soundEnabled) {
                if (onEnd) onEnd();
                return;
            }
            
            const indicator = document.getElementById('speakingIndicator');
            indicator.classList.add('active');
            
            // Estimate speech duration (rough: ~80ms per character for espeak)
            const estimatedDuration = Math.max(1, text.length * 0.08);
            
            // Trigger servo animation (unless already triggered externally)
            if (!skipServo) {
                if (isLaugh) {
                    triggerServoLaugh();
                } else {
                    triggerServoTalk(estimatedDuration);
                }
            }
            
            // Call server-side TTS (Pi's speakers via espeak)
            let url;
            if (isLaugh) {
                url = '/api/speak/laugh';
            } else {
                url = '/api/speak?text=' + encodeURIComponent(text);
            }
            
            fetch(url)
                .then(response => response.json())
                .then(data => {
                    // Wait for estimated speech duration before calling onEnd
                    setTimeout(() => {
                        indicator.classList.remove('active');
                        triggerServoRelease();
                        if (onEnd) onEnd();
                    }, estimatedDuration * 1000);
                })
                .catch(() => {
                    indicator.classList.remove('active');
                    triggerServoRelease();
                    if (onEnd) onEnd();
                });
        }

        function toggleSound() {
            soundEnabled = !soundEnabled;
            const btn = document.getElementById('soundBtn');
            
            if (soundEnabled) {
                btn.textContent = '🔊 Sound On';
                btn.classList.add('active');
                // Speak current setup to confirm sound is working
                speak(document.getElementById('setup').textContent);
            } else {
                btn.textContent = '🔇 Sound Off';
                btn.classList.remove('active');
                speechSynthesis.cancel();
                document.getElementById('speakingIndicator').classList.remove('active');
                triggerServoRelease();
            }
        }

        function revealPunchline() {
            if (punchlineRevealed) return;
            punchlineRevealed = true;
            
            document.getElementById('revealBtn').classList.add('hidden');
            document.getElementById('punchline').classList.add('revealed');
            
            const punchline = document.getElementById('punchline').textContent;
            const estimatedDuration = Math.max(1, punchline.length * 0.08);
            
            // Always trigger servo for punchline (regardless of sound)
            triggerServoTalk(estimatedDuration);
            
            if (soundEnabled) {
                // Speak the punchline, then laugh
                speak(punchline, () => {
                    setTimeout(() => {
                        document.getElementById('laugh').classList.add('visible');
                        createConfetti();
                        triggerServoLaugh();
                        speak("Ha ha ha ha! That's a good one!", null, true);
                    }, 300);
                }, false, true);  // skipServo = true since we already triggered it
            } else {
                // No sound - just animate servo and show laugh
                setTimeout(() => {
                    triggerServoRelease();
                    document.getElementById('laugh').classList.add('visible');
                    createConfetti();
                    triggerServoLaugh();
                }, estimatedDuration * 1000);
            }
        }

        function getNewJoke() {
            // Cancel any ongoing speech
            speechSynthesis.cancel();
            triggerServoRelease();
            
            fetch('/api/joke')
                .then(response => response.json())
                .then(data => {
                    punchlineRevealed = false;
                    
                    document.getElementById('setup').textContent = data.setup;
                    document.getElementById('punchline').textContent = data.punchline;
                    document.getElementById('punchline').classList.remove('revealed');
                    document.getElementById('revealBtn').classList.remove('hidden');
                    document.getElementById('laugh').classList.remove('visible');
                    
                    // Always animate servo for setup (even without sound)
                    const estimatedDuration = Math.max(1, data.setup.length * 0.08);
                    triggerServoTalk(estimatedDuration);
                    
                    if (soundEnabled) {
                        // Speak the new setup (skip servo since we triggered it above)
                        speak(data.setup, null, false, true);
                    } else {
                        // No sound - just release servo after animation
                        setTimeout(() => triggerServoRelease(), estimatedDuration * 1000);
                    }
                });
        }

        function createConfetti() {
            const colors = ['#e94560', '#ffd93d', '#533483', '#a2d5f2', '#ff6b6b'];
            for (let i = 0; i < 30; i++) {
                setTimeout(() => {
                    const confetti = document.createElement('div');
                    confetti.className = 'confetti';
                    confetti.style.left = Math.random() * 100 + 'vw';
                    confetti.style.top = '-10px';
                    confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
                    confetti.style.borderRadius = Math.random() > 0.5 ? '50%' : '0';
                    confetti.style.animationDuration = (2 + Math.random() * 2) + 's';
                    document.body.appendChild(confetti);
                    
                    setTimeout(() => confetti.remove(), 4000);
                }, i * 50);
            }
        }

        // Keyboard support
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space' && !punchlineRevealed) {
                e.preventDefault();
                revealPunchline();
            } else if (e.code === 'Enter') {
                getNewJoke();
            } else if (e.code === 'KeyS') {
                toggleSound();
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    joke = random.choice(JOKES)
    return render_template_string(
        HTML_TEMPLATE,
        setup=joke['setup'],
        punchline=joke['punchline'],
        total_jokes=len(JOKES),
        servo_connected=(servo is not None),
        servo_error=servo_error,
        tts_available=(tts_command is not None),
        tts_engine=tts_command
    )

@app.route('/api/joke')
def api_joke():
    joke = random.choice(JOKES)
    return jsonify(joke)

@app.route('/api/servo/talk')
def api_servo_talk():
    """Trigger talking mouth animation."""
    if not servo:
        return jsonify({'status': 'no_servo'})
    
    duration = float(request.args.get('duration', 2.0))
    # Run animation in background thread so it doesn't block
    thread = threading.Thread(target=mouth_talking_animation, args=(duration,))
    thread.start()
    return jsonify({'status': 'ok', 'duration': duration})

@app.route('/api/servo/laugh')
def api_servo_laugh():
    """Trigger laugh animation."""
    if not servo:
        return jsonify({'status': 'no_servo'})
    
    # Run animation in background thread
    thread = threading.Thread(target=laugh_animation)
    thread.start()
    return jsonify({'status': 'ok'})

@app.route('/api/servo/release')
def api_servo_release():
    """Release the servo."""
    if not servo:
        return jsonify({'status': 'no_servo'})
    
    with servo_lock:
        servo.release()
    return jsonify({'status': 'ok'})

@app.route('/api/servo/status')
def api_servo_status():
    """Get servo connection status."""
    return jsonify({
        'connected': servo is not None,
        'gpio_pin': GPIO_PIN if servo else None,
        'error': servo_error
    })

@app.route('/api/servo/angle')
def api_servo_angle():
    """Set servo to a specific angle."""
    if not servo:
        return jsonify({'status': 'no_servo', 'error': 'Servo not connected'})
    
    try:
        angle = int(request.args.get('angle', 90))
        angle = max(0, min(180, angle))
        
        with servo_lock:
            servo.set_angle(angle)
        
        return jsonify({'status': 'ok', 'angle': angle})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)})

@app.route('/api/servo/test')
def api_servo_test():
    """Run a servo test cycle."""
    if not servo:
        return jsonify({'status': 'no_servo', 'error': 'Servo not connected'})
    
    def test_cycle():
        with servo_lock:
            # Move to closed (90°)
            servo.set_angle(MOUTH_CLOSED)
        time.sleep(0.5)
        
        with servo_lock:
            # Move to open (0°)
            servo.set_angle(MOUTH_OPEN)
        time.sleep(0.5)
        
        with servo_lock:
            # Move to half (45°)
            servo.set_angle(MOUTH_HALF)
        time.sleep(0.5)
        
        with servo_lock:
            # Back to closed
            servo.set_angle(MOUTH_CLOSED)
        time.sleep(0.3)
        
        with servo_lock:
            servo.release()
    
    # Run test in background thread
    thread = threading.Thread(target=test_cycle)
    thread.start()
    
    return jsonify({'status': 'ok', 'message': 'Test cycle started'})

@app.route('/api/speak')
def api_speak():
    """Speak text through Pi's speakers."""
    text = request.args.get('text', '')
    if not text:
        return jsonify({'status': 'error', 'error': 'No text provided'})
    
    if not tts_command:
        return jsonify({'status': 'no_tts', 'error': 'No TTS engine available'})
    
    # Speak in background thread
    speak_text_async(text)
    return jsonify({'status': 'ok', 'text': text})

@app.route('/api/speak/laugh')
def api_speak_laugh():
    """Speak the laugh through Pi's speakers."""
    if not tts_command:
        return jsonify({'status': 'no_tts', 'error': 'No TTS engine available'})
    
    # Speak laugh in background thread
    speak_text_async("", is_laugh=True)
    return jsonify({'status': 'ok'})

@app.route('/api/tts/status')
def api_tts_status():
    """Get TTS status."""
    return jsonify({
        'available': tts_command is not None,
        'engine': tts_command
    })

if __name__ == '__main__':
    # use_reloader=False prevents Flask from starting twice and causing "GPIO busy"
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
