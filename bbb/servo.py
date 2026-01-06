#!/usr/bin/env python3
"""
Servo controller module for BBB (Boredom Buster Bot)
Handles servo initialization and mouth animations.
"""

import os
import time
import threading

# Servo configuration
SERVO_ENABLED = True
GPIO_PIN = 18
MOUTH_CLOSED = 90   # Degrees when mouth is closed
MOUTH_OPEN = 0      # Degrees when mouth is fully open
MOUTH_HALF = 45     # Degrees for half-open mouth

# Global servo instance and lock
_servo = None
_servo_lock = threading.Lock()
_servo_error = None


class ServoController:
    """PWM-based servo controller for Raspberry Pi."""
    
    def __init__(self, gpio_pin, min_duty=0.025, max_duty=0.125, freq=50):
        os.environ['GPIOZERO_PIN_FACTORY'] = 'lgpio'
        from gpiozero import PWMOutputDevice
        
        self.gpio = gpio_pin
        self.min_duty = min_duty
        self.max_duty = max_duty
        self.pwm = PWMOutputDevice(gpio_pin, frequency=freq, initial_value=0)
        self.current_angle = None
    
    def angle_to_duty(self, angle):
        """Convert angle (0-180) to duty cycle."""
        angle = max(0, min(180, angle))
        duty_range = self.max_duty - self.min_duty
        return self.min_duty + (angle / 180.0) * duty_range
    
    def set_angle(self, angle):
        """Move servo to angle (0-180)."""
        angle = max(0, min(180, angle))
        self.pwm.value = self.angle_to_duty(angle)
        self.current_angle = angle
    
    def release(self):
        """Stop PWM signal (servo won't hold position but won't jitter)."""
        self.pwm.value = 0
    
    def cleanup(self):
        """Release resources."""
        self.pwm.value = 0
        self.pwm.close()


def init_servo(skip_if_reloader=False):
    """
    Initialize the servo controller.
    
    Args:
        skip_if_reloader: If True, skip init in Flask reloader process
        
    Returns:
        tuple: (servo instance or None, error message or None)
    """
    global _servo, _servo_error
    
    if not SERVO_ENABLED:
        return None, "Servo disabled"
    
    # Check for Flask reloader
    if skip_if_reloader:
        is_reloader = os.environ.get('WERKZEUG_RUN_MAIN') != 'true' and os.environ.get('FLASK_DEBUG') == '1'
        if is_reloader:
            print("⏳ Skipping servo init in reloader process...")
            return None, "Reloader process"
    
    try:
        _servo = ServoController(GPIO_PIN)
        _servo.set_angle(MOUTH_CLOSED)
        time.sleep(0.3)
        _servo.release()
        print(f"🤖 Servo initialized on GPIO {GPIO_PIN}")
        return _servo, None
    except Exception as e:
        _servo = None
        _servo_error = str(e)
        print(f"⚠️  Servo error: {e}")
        return None, str(e)


def get_servo():
    """Get the global servo instance."""
    return _servo


def get_servo_lock():
    """Get the servo lock for thread-safe access."""
    return _servo_lock


def get_servo_error():
    """Get the servo error message if any."""
    return _servo_error


def move_mouth(angle, use_lock=False):
    """Move servo to specified angle if available."""
    if _servo:
        if use_lock:
            with _servo_lock:
                _servo.set_angle(angle)
        else:
            _servo.set_angle(angle)


def mouth_talking_animation(duration=2.0, use_lock=False):
    """Animate mouth while talking (open/close pattern)."""
    if not _servo:
        return
    
    start_time = time.time()
    while time.time() - start_time < duration:
        if use_lock:
            with _servo_lock:
                _servo.set_angle(MOUTH_OPEN)
        else:
            _servo.set_angle(MOUTH_OPEN)
        time.sleep(0.15)
        
        if use_lock:
            with _servo_lock:
                _servo.set_angle(MOUTH_CLOSED)
        else:
            _servo.set_angle(MOUTH_CLOSED)
        time.sleep(0.1)
    
    if use_lock:
        with _servo_lock:
            _servo.set_angle(MOUTH_CLOSED)
            _servo.release()
    else:
        _servo.set_angle(MOUTH_CLOSED)
        _servo.release()


def laugh_animation(use_lock=False):
    """
    Animate mouth for laughing: Ha ha ha ha!
    Pattern: closed → open → half → open → half → open → closed
    """
    if not _servo:
        return
    
    def set_angle(angle):
        if use_lock:
            with _servo_lock:
                _servo.set_angle(angle)
        else:
            _servo.set_angle(angle)
    
    # Ha
    set_angle(MOUTH_OPEN)
    time.sleep(0.2)
    set_angle(MOUTH_HALF)
    time.sleep(0.15)
    
    # ha
    set_angle(MOUTH_OPEN)
    time.sleep(0.2)
    set_angle(MOUTH_HALF)
    time.sleep(0.15)
    
    # ha
    set_angle(MOUTH_OPEN)
    time.sleep(0.2)
    set_angle(MOUTH_HALF)
    time.sleep(0.15)
    
    # ha!
    set_angle(MOUTH_OPEN)
    time.sleep(0.3)
    
    # Close mouth
    set_angle(MOUTH_CLOSED)
    time.sleep(0.2)
    
    if use_lock:
        with _servo_lock:
            _servo.release()
    else:
        _servo.release()

