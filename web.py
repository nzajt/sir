#!/usr/bin/env python3

from flask import Flask, render_template_string, jsonify
import json
import os
import random

app = Flask(__name__)

# Get the directory where this script lives
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

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
    <title>SIR - Dad Joke Robot</title>
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
            <h1 class="title">S.I.R.</h1>
            <p class="subtitle">Super Intelligent Robot (of Dad Jokes)</p>
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

        <button class="btn btn-primary" onclick="getNewJoke()">
            🎲 Another Joke!
        </button>

        <p class="stats">Serving {{ total_jokes }} premium dad jokes</p>

        <footer class="footer">
            <p>Built for science fairs & Raspberry Pi 5</p>
        </footer>
    </div>

    <script>
        let punchlineRevealed = false;

        function revealPunchline() {
            if (punchlineRevealed) return;
            punchlineRevealed = true;
            
            document.getElementById('revealBtn').classList.add('hidden');
            document.getElementById('punchline').classList.add('revealed');
            
            setTimeout(() => {
                document.getElementById('laugh').classList.add('visible');
                createConfetti();
            }, 300);
        }

        function getNewJoke() {
            fetch('/api/joke')
                .then(response => response.json())
                .then(data => {
                    punchlineRevealed = false;
                    
                    document.getElementById('setup').textContent = data.setup;
                    document.getElementById('punchline').textContent = data.punchline;
                    document.getElementById('punchline').classList.remove('revealed');
                    document.getElementById('revealBtn').classList.remove('hidden');
                    document.getElementById('laugh').classList.remove('visible');
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
        total_jokes=len(JOKES)
    )

@app.route('/api/joke')
def api_joke():
    joke = random.choice(JOKES)
    return jsonify(joke)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

