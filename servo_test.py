#!/usr/bin/env python3
"""
Servo Test Script for Raspberry Pi 5
=====================================
For: HobbyPark 25KG Servo (180° control angle)

Uses gpiozero with lgpio backend for Pi 5 compatibility.
Includes jitter mitigation by releasing servo after movement.

WIRING:
-------
Servo Wire Color -> Raspberry Pi 5
  Brown (GND)   -> Pin 6 (Ground)
  Red (VCC)     -> External 5-7.4V power supply (NOT from Pi!)
  Orange (SIG)  -> Pin 12 (GPIO 18) - or any GPIO pin

IMPORTANT: 
- Do NOT power the servo from the Pi's 5V pin! 
- A 25KG servo draws too much current and will brown out the Pi.
- Use a separate 5V-7.4V power supply for the servo.
- Connect the ground of the power supply to the Pi's ground (Pin 6).

SETUP (Raspberry Pi 5):
-----------------------
sudo apt update
sudo apt install python3-gpiozero python3-lgpio

# Run this script:
python3 servo_test.py

JITTER MITIGATION:
------------------
Software PWM on Pi can cause jitter. This script mitigates it by:
1. Releasing the servo after each movement (stops PWM signal)
2. Using short, precise movements
3. Option to use a PCA9685 servo driver board (recommended for production)
"""

import sys
import time
import os

# Set lgpio as the pin factory before importing gpiozero
os.environ['GPIOZERO_PIN_FACTORY'] = 'lgpio'

try:
    from gpiozero import PWMOutputDevice
except ImportError:
    print("Error: gpiozero not installed!")
    print("Run: sudo apt install python3-gpiozero python3-lgpio")
    sys.exit(1)

# Configuration
GPIO_PIN = 18  # GPIO 18 = Physical Pin 12

# Servo pulse width calibration
# Standard servo: 0.5ms - 2.5ms pulse for 180° range
# PWM frequency is 50Hz (20ms period), so duty cycle:
#   0° = 0.5ms / 20ms = 0.025 (2.5%)
#   180° = 2.5ms / 20ms = 0.125 (12.5%)
MIN_DUTY = 0.025   # Duty cycle for 0° (adjust if needed)
MAX_DUTY = 0.125   # Duty cycle for 180° (adjust if needed)
PWM_FREQ = 50      # Standard servo frequency (Hz)

# Jitter mitigation settings
SETTLE_TIME = 0.3      # Time to let servo reach position before releasing
AUTO_RELEASE = True    # Release servo after movement to prevent jitter


class ServoController:
    """PWM-based servo controller with jitter mitigation for Pi 5."""
    
    def __init__(self, gpio_pin, min_duty=0.025, max_duty=0.125, freq=50):
        self.gpio = gpio_pin
        self.min_duty = min_duty
        self.max_duty = max_duty
        self.freq = freq
        self.current_angle = None
        self.pwm = None
        self._init_pwm()
    
    def _init_pwm(self):
        """Initialize PWM output."""
        try:
            self.pwm = PWMOutputDevice(
                self.gpio,
                frequency=self.freq,
                initial_value=0
            )
        except Exception as e:
            print(f"Error initializing PWM: {e}")
            print("\nTroubleshooting:")
            print("1. Make sure lgpio is installed: sudo apt install python3-lgpio")
            print("2. Check that GPIO pin is not in use")
            print("3. Try running with sudo if permission denied")
            sys.exit(1)
    
    def angle_to_duty(self, angle):
        """Convert angle (0-180) to duty cycle."""
        angle = max(0, min(180, angle))
        duty_range = self.max_duty - self.min_duty
        return self.min_duty + (angle / 180.0) * duty_range
    
    def set_angle(self, angle, hold=False):
        """
        Move servo to specified angle (0-180 degrees).
        
        Args:
            angle: Target angle (0-180)
            hold: If True, keep PWM signal active (may cause jitter)
        """
        angle = max(0, min(180, angle))
        duty = self.angle_to_duty(angle)
        
        self.pwm.value = duty
        self.current_angle = angle
        
        # Wait for servo to reach position
        time.sleep(SETTLE_TIME)
        
        # Release to prevent jitter (unless hold is requested)
        if AUTO_RELEASE and not hold:
            self.release()
    
    def set_angle_quick(self, angle):
        """Set angle without waiting or releasing (for sweeps)."""
        angle = max(0, min(180, angle))
        duty = self.angle_to_duty(angle)
        self.pwm.value = duty
        self.current_angle = angle
    
    def release(self):
        """Stop PWM signal (servo won't hold position but won't jitter)."""
        self.pwm.value = 0
    
    def hold(self):
        """Re-engage servo at current angle."""
        if self.current_angle is not None:
            duty = self.angle_to_duty(self.current_angle)
            self.pwm.value = duty
    
    def cleanup(self):
        """Release resources."""
        if self.pwm:
            self.pwm.value = 0
            self.pwm.close()


def sweep_test(servo):
    """Perform a full sweep test from 0° to 180° and back."""
    print("\n🔄 Sweep Test: 0° → 180° → 0°")
    print("-" * 30)
    
    # Sweep from 0 to 180
    for angle in range(0, 181, 10):
        servo.set_angle_quick(angle)
        print(f"  → {angle}°")
        time.sleep(0.1)
    
    time.sleep(0.3)
    
    # Sweep from 180 to 0
    for angle in range(180, -1, -10):
        servo.set_angle_quick(angle)
        print(f"  → {angle}°")
        time.sleep(0.1)
    
    servo.release()
    print("✓ Sweep complete! (servo released)")


def position_test(servo):
    """Test specific positions: 0°, 45°, 90°, 135°, 180°."""
    print("\n📍 Position Test")
    print("-" * 30)
    
    positions = [0, 45, 90, 135, 180, 90]
    
    for pos in positions:
        print(f"\nMoving to {pos}°...")
        servo.set_angle(pos, hold=True)  # Hold during test
        time.sleep(0.7)
    
    servo.release()
    print("\n✓ Position test complete! (servo released)")


def interactive_mode(servo):
    """Interactive mode for manual servo control."""
    print("\n🎮 Interactive Mode")
    print("-" * 30)
    print("Commands:")
    print("  0-180  : Move to angle (e.g., '90' for center)")
    print("  sweep  : Perform sweep test")
    print("  center : Move to 90° (center)")
    print("  min    : Move to 0°")
    print("  max    : Move to 180°")
    print("  hold   : Keep servo engaged (holds position, may jitter)")
    print("  release: Release servo (stops jitter, won't hold)")
    print("  quit   : Exit program")
    print()
    print("💡 Tip: Servo auto-releases after movement to prevent jitter")
    print("   Use 'hold' if you need it to maintain position under load")
    print()
    
    while True:
        try:
            cmd = input("Enter command: ").strip().lower()
            
            if cmd == 'quit' or cmd == 'q':
                break
            elif cmd == 'sweep':
                sweep_test(servo)
            elif cmd == 'center':
                print("  → Moving to 90°...")
                servo.set_angle(90)
                print("  → Done (released)")
            elif cmd == 'min':
                print("  → Moving to 0°...")
                servo.set_angle(0)
                print("  → Done (released)")
            elif cmd == 'max':
                print("  → Moving to 180°...")
                servo.set_angle(180)
                print("  → Done (released)")
            elif cmd == 'hold':
                servo.hold()
                print("  → Servo engaged (holding position)")
                print("    ⚠️  May jitter - type 'release' to stop")
            elif cmd == 'release':
                servo.release()
                print("  → Servo released")
            else:
                try:
                    angle = int(cmd)
                    if 0 <= angle <= 180:
                        print(f"  → Moving to {angle}°...")
                        servo.set_angle(angle)
                        print("  → Done (released)")
                    else:
                        print("  ⚠ Angle must be 0-180")
                except ValueError:
                    print("  ⚠ Unknown command. Type 'quit' to exit.")
        
        except KeyboardInterrupt:
            print("\n")
            break


def main():
    print("=" * 50)
    print("🤖 Servo Test for Raspberry Pi 5")
    print("   HobbyPark 25KG Servo (180°)")
    print("   Using gpiozero + lgpio (Pi 5 compatible)")
    print("=" * 50)
    print(f"\nUsing GPIO pin: {GPIO_PIN} (Physical pin 12)")
    print("\n⚠️  IMPORTANT: Use external power for the servo!")
    print("   Do NOT power from Pi's 5V pin.\n")
    
    # Create servo controller
    print("Initializing servo...")
    servo = ServoController(GPIO_PIN, MIN_DUTY, MAX_DUTY, PWM_FREQ)
    print("✓ Servo initialized!\n")
    
    try:
        # Center the servo first
        print("Centering servo (90°)...")
        servo.set_angle(90)
        print("✓ Centered (released to prevent jitter)\n")
        time.sleep(0.5)
        
        # Run tests
        sweep_test(servo)
        time.sleep(0.5)
        
        position_test(servo)
        time.sleep(0.5)
        
        # Enter interactive mode
        interactive_mode(servo)
        
    except KeyboardInterrupt:
        print("\n\nInterrupted!")
    
    finally:
        print("\nCleaning up...")
        servo.cleanup()
        print("✓ Done!")


if __name__ == "__main__":
    main()
