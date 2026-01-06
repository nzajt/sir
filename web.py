#!/usr/bin/env python3

from flask import Flask, render_template_string, jsonify, request
import json
import os
import random
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
        print("🤖 Servo initialized on GPIO", GPIO_PIN)
        
except Exception as e:
    servo = None
    print(f"Note: Servo not available ({e})")
    print("Running without servo control.")


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
        </p>

        <footer class="footer">
            <p>The Boredom Buster Bot • Built for science fairs & Raspberry Pi 5</p>
        </footer>
    </div>

    <script>
        let punchlineRevealed = false;
        let soundEnabled = false;
        let selectedVoice = null;
        const servoConnected = {{ 'true' if servo_connected else 'false' }};

        // Initialize speech synthesis and find a good "dad" voice
        function initVoices() {
            const voices = speechSynthesis.getVoices();
            // Prefer deeper/male voices for the dad effect
            const preferredVoices = ['Daniel', 'Fred', 'Alex', 'Ralph', 'Albert', 'Bruce', 'Google UK English Male', 'Microsoft David', 'en-US', 'en-GB'];
            
            for (const preferred of preferredVoices) {
                const found = voices.find(v => v.name.includes(preferred) || v.lang.includes(preferred));
                if (found) {
                    selectedVoice = found;
                    break;
                }
            }
            // Fallback to first English voice or any voice
            if (!selectedVoice) {
                selectedVoice = voices.find(v => v.lang.startsWith('en')) || voices[0];
            }
        }

        // Chrome loads voices asynchronously
        if (speechSynthesis.onvoiceschanged !== undefined) {
            speechSynthesis.onvoiceschanged = initVoices;
        }
        initVoices();

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

        function speak(text, onEnd = null, isLaugh = false) {
            if (!soundEnabled || !('speechSynthesis' in window)) {
                if (onEnd) onEnd();
                return;
            }
            
            // Cancel any ongoing speech
            speechSynthesis.cancel();
            
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.voice = selectedVoice;
            utterance.rate = 0.9;  // Slightly slower for dad delivery
            utterance.pitch = 0.9; // Slightly lower pitch
            
            const indicator = document.getElementById('speakingIndicator');
            indicator.classList.add('active');
            
            // Estimate duration for servo animation (rough: ~100ms per character at 0.9 rate)
            const estimatedDuration = Math.max(1, text.length * 0.08);
            
            // Trigger servo animation
            if (isLaugh) {
                triggerServoLaugh();
            } else {
                triggerServoTalk(estimatedDuration);
            }
            
            utterance.onend = () => {
                indicator.classList.remove('active');
                triggerServoRelease();
                if (onEnd) onEnd();
            };
            utterance.onerror = () => {
                indicator.classList.remove('active');
                triggerServoRelease();
            };
            
            speechSynthesis.speak(utterance);
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
            
            // Speak the punchline, then laugh
            speak(punchline, () => {
                setTimeout(() => {
                    document.getElementById('laugh').classList.add('visible');
                    createConfetti();
                    speak("Ha ha ha ha! That's a good one!", null, true);
                }, 300);
            });
            
            // If sound is off, just show the laugh immediately
            if (!soundEnabled) {
                setTimeout(() => {
                    document.getElementById('laugh').classList.add('visible');
                    createConfetti();
                }, 300);
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
                    
                    // Speak the new setup
                    speak(data.setup);
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
        servo_connected=(servo is not None)
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
        'gpio_pin': GPIO_PIN if servo else None
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
