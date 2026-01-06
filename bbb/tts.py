#!/usr/bin/env python3
"""
Text-to-speech module for BBB (Boredom Buster Bot)
Supports pico2wave (natural), espeak (robotic), and macOS say.
"""

import os
import shutil
import subprocess
import tempfile
import threading

# TTS lock for thread-safe access
_tts_lock = threading.Lock()

# Cached TTS command
_tts_command = None

# Audio player: prefer paplay (PulseAudio) for system default output
_audio_player = None


def _get_audio_player():
    """Get the best available audio player for WAV files."""
    global _audio_player
    if _audio_player is None:
        # paplay uses PulseAudio and respects system default output
        if shutil.which('paplay'):
            _audio_player = 'paplay'
        # aplay goes direct to ALSA (may default to HDMI)
        elif shutil.which('aplay'):
            _audio_player = 'aplay'
        else:
            _audio_player = None
    return _audio_player


def _play_wav(wav_file):
    """Play a WAV file through the system default audio output."""
    player = _get_audio_player()
    if player == 'paplay':
        # PulseAudio - uses system default output
        subprocess.run(['paplay', wav_file], check=False)
    elif player == 'aplay':
        # ALSA - try to use default device
        subprocess.run(['aplay', '-q', wav_file], check=False)
    else:
        print("⚠️  No audio player available (install pulseaudio)")


def check_tts_available():
    """
    Check which TTS engine is available.
    Prefers pico2wave (natural) over espeak (robotic).
    
    Returns:
        str or None: 'pico2wave', 'espeak', 'say', or None
    """
    if shutil.which('pico2wave'):
        return 'pico2wave'
    elif shutil.which('espeak'):
        return 'espeak'
    elif shutil.which('say'):
        return 'say'
    return None


def init_tts():
    """Initialize TTS and return the available engine."""
    global _tts_command
    _tts_command = check_tts_available()
    audio_player = _get_audio_player()
    
    if _tts_command:
        print(f"🔊 TTS initialized: {_tts_command}")
        if audio_player == 'paplay':
            print("🔊 Audio output: PulseAudio (system default)")
        elif audio_player == 'aplay':
            print("🔊 Audio output: ALSA (install pulseaudio for better routing)")
        else:
            print("⚠️  No audio player found")
    else:
        print("⚠️  No TTS available (install: sudo apt install libttspico-utils)")
    return _tts_command


def get_tts_command():
    """Get the current TTS command."""
    return _tts_command


def get_tts_lock():
    """Get the TTS lock for thread-safe access."""
    return _tts_lock


def speak_with_pico(text):
    """
    Speak using pico2wave (more natural voice) with volume boost.
    
    Args:
        text: The text to speak
    """
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        wav_file = f.name
    
    subprocess.run(['pico2wave', '-l', 'en-US', '-w', wav_file, text], check=False)
    
    # Amplify with sox if available (boost volume 3x)
    if shutil.which('sox'):
        amplified_file = wav_file + '_loud.wav'
        subprocess.run(['sox', wav_file, amplified_file, 'vol', '3.0'], check=False)
        _play_wav(amplified_file)
        try:
            os.unlink(amplified_file)
        except:
            pass
    else:
        _play_wav(wav_file)
    
    try:
        os.unlink(wav_file)
    except:
        pass


def speak_with_espeak(text):
    """
    Speak using espeak.
    
    Args:
        text: The text to speak
    """
    # If paplay is available, output to WAV and play through PulseAudio
    # This ensures audio goes to system default instead of HDMI
    if _get_audio_player() == 'paplay':
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            wav_file = f.name
        # -a 200 = max volume, -s 120 = slower speed, -g 10 = gaps between words
        # -w outputs to WAV file instead of playing directly
        subprocess.run(['espeak', '-a', '200', '-s', '120', '-g', '10', '-w', wav_file, text], check=False)
        _play_wav(wav_file)
        try:
            os.unlink(wav_file)
        except:
            pass
    else:
        # Fall back to direct espeak output (may go to HDMI)
        subprocess.run(['espeak', '-a', '200', '-s', '120', '-g', '10', text], check=False)


def speak_with_say(text):
    """
    Speak using macOS 'say' command.
    
    Args:
        text: The text to speak
    """
    subprocess.run(['say', '-v', 'Fred', text], check=False)


def speak_text_sync(text, is_laugh=False, tts_cmd=None):
    """
    Speak text using system TTS (blocking).
    
    Args:
        text: The text to speak
        is_laugh: If True, speak the laugh text instead
        tts_cmd: TTS command to use (auto-detected if None)
    """
    if tts_cmd is None:
        tts_cmd = _tts_command or check_tts_available()
    
    if not tts_cmd:
        return
    
    with _tts_lock:
        try:
            if is_laugh:
                text = "Ha ha ha ha! That's a good one!"
            
            if tts_cmd == 'pico2wave':
                speak_with_pico(text)
            elif tts_cmd == 'espeak':
                speak_with_espeak(text)
            elif tts_cmd == 'say':
                speak_with_say(text)
        except Exception as e:
            print(f"TTS error: {e}")


def speak_text_async(text, is_laugh=False, tts_cmd=None):
    """
    Speak text in a background thread.
    
    Args:
        text: The text to speak
        is_laugh: If True, speak the laugh text instead
        tts_cmd: TTS command to use (auto-detected if None)
        
    Returns:
        threading.Thread: The thread running the speech
    """
    thread = threading.Thread(target=speak_text_sync, args=(text, is_laugh, tts_cmd))
    thread.start()
    return thread

