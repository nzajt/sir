#!/usr/bin/env python3
"""
Servo Test Script for Raspberry Pi 5 (Jitter-Free Version)
===========================================================
For: HobbyPark 25KG Servo (180° control angle)

Uses pigpio for hardware-timed PWM to eliminate jitter.

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

SETUP:
------
# Install pigpio on Raspberry Pi 5:
sudo apt update
sudo apt install pigpio python3-pigpio

# Start the pigpio daemon (required):
sudo pigpiod

# To start pigpiod automatically on boot:
sudo systemctl enable pigpiod

# Run this script:
python3 servo_test.py
"""

import sys
import time

try:
    import pigpio
except ImportError:
    print("Error: pigpio not installed!")
    print("Run: sudo apt install pigpio python3-pigpio")
    print("Then start daemon: sudo pigpiod")
    sys.exit(1)

# Configuration
GPIO_PIN = 18  # GPIO 18 = Physical Pin 12

# Servo pulse width calibration (microseconds)
# Standard servo: 500-2500µs for full 180° range
# Adjust these if your servo doesn't reach full range
MIN_PULSE = 500   # Pulse width for 0° (microseconds)
MAX_PULSE = 2500  # Pulse width for 180° (microseconds)

# Auto-release: Stop PWM signal after moving to prevent jitter
# Set to 0 to keep servo engaged (holding position)
AUTO_RELEASE_DELAY = 0.5  # Seconds to wait before releasing (0 = never release)


class Servo:
    """Hardware PWM servo controller using pigpio (jitter-free)."""
    
    def __init__(self, pi, gpio_pin, min_pulse=500, max_pulse=2500):
        self.pi = pi
        self.gpio = gpio_pin
        self.min_pulse = min_pulse
        self.max_pulse = max_pulse
        self.current_angle = None
        
    def angle_to_pulse(self, angle):
        """Convert angle (0-180) to pulse width in microseconds."""
        angle = max(0, min(180, angle))
        pulse_range = self.max_pulse - self.min_pulse
        return int(self.min_pulse + (angle / 180.0) * pulse_range)
    
    def set_angle(self, angle, release_after=None):
        """
        Move servo to specified angle (0-180 degrees).
        
        Args:
            angle: Target angle (0-180)
            release_after: Seconds to wait before releasing servo (None = use AUTO_RELEASE_DELAY)
        """
        angle = max(0, min(180, angle))
        pulse_width = self.angle_to_pulse(angle)
        
        # Set servo position using hardware PWM
        self.pi.set_servo_pulsewidth(self.gpio, pulse_width)
        self.current_angle = angle
        
        # Auto-release to prevent jitter when holding position
        delay = release_after if release_after is not None else AUTO_RELEASE_DELAY
        if delay > 0:
            time.sleep(delay)
            self.release()
    
    def set_angle_smooth(self, angle, step=2, delay=0.02):
        """Move servo smoothly to angle in small steps."""
        if self.current_angle is None:
            self.current_angle = 90
            
        start = self.current_angle
        end = max(0, min(180, angle))
        
        if start < end:
            angles = range(int(start), int(end) + 1, step)
        else:
            angles = range(int(start), int(end) - 1, -step)
        
        for a in angles:
            pulse_width = self.angle_to_pulse(a)
            self.pi.set_servo_pulsewidth(self.gpio, pulse_width)
            self.current_angle = a
            time.sleep(delay)
        
        # Final position
        self.set_angle(end, release_after=AUTO_RELEASE_DELAY)
    
    def release(self):
        """Stop sending PWM signal (servo will not hold position but won't jitter)."""
        self.pi.set_servo_pulsewidth(self.gpio, 0)
    
    def hold(self):
        """Re-engage servo at current angle (will hold position)."""
        if self.current_angle is not None:
            pulse_width = self.angle_to_pulse(self.current_angle)
            self.pi.set_servo_pulsewidth(self.gpio, pulse_width)


def sweep_test(servo):
    """Perform a full sweep test from 0° to 180° and back."""
    print("\n🔄 Sweep Test: 0° → 180° → 0°")
    print("-" * 30)
    
    # Sweep from 0 to 180
    for angle in range(0, 181, 10):
        pulse = servo.angle_to_pulse(angle)
        servo.pi.set_servo_pulsewidth(servo.gpio, pulse)
        servo.current_angle = angle
        print(f"  → {angle}°")
        time.sleep(0.15)
    
    time.sleep(0.3)
    
    # Sweep from 180 to 0
    for angle in range(180, -1, -10):
        pulse = servo.angle_to_pulse(angle)
        servo.pi.set_servo_pulsewidth(servo.gpio, pulse)
        servo.current_angle = angle
        print(f"  → {angle}°")
        time.sleep(0.15)
    
    servo.release()
    print("✓ Sweep complete! (servo released)")


def position_test(servo):
    """Test specific positions: 0°, 45°, 90°, 135°, 180°."""
    print("\n📍 Position Test")
    print("-" * 30)
    
    positions = [0, 45, 90, 135, 180, 90]
    
    for pos in positions:
        print(f"\nMoving to {pos}°...")
        servo.set_angle(pos, release_after=0)  # Don't auto-release during test
        time.sleep(1)
    
    servo.release()
    print("\n✓ Position test complete! (servo released)")


def interactive_mode(servo):
    """Interactive mode for manual servo control."""
    print("\n🎮 Interactive Mode")
    print("-" * 30)
    print("Commands:")
    print("  0-180   : Move to angle (e.g., '90' for center)")
    print("  smooth X: Smooth move to angle X (e.g., 'smooth 180')")
    print("  sweep   : Perform sweep test")
    print("  center  : Move to 90° (center)")
    print("  min     : Move to 0°")
    print("  max     : Move to 180°")
    print("  hold    : Keep servo engaged (holds position, may jitter)")
    print("  release : Release servo (stops jitter, won't hold position)")
    print("  quit    : Exit program")
    print()
    print(f"💡 Tip: Servo auto-releases after {AUTO_RELEASE_DELAY}s to prevent jitter")
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
            elif cmd == 'min':
                print("  → Moving to 0°...")
                servo.set_angle(0)
            elif cmd == 'max':
                print("  → Moving to 180°...")
                servo.set_angle(180)
            elif cmd == 'hold':
                servo.hold()
                print("  → Servo engaged (holding position)")
            elif cmd == 'release':
                servo.release()
                print("  → Servo released (not holding)")
            elif cmd.startswith('smooth '):
                try:
                    angle = int(cmd.split()[1])
                    if 0 <= angle <= 180:
                        print(f"  → Smooth moving to {angle}°...")
                        servo.set_angle_smooth(angle)
                    else:
                        print("  ⚠ Angle must be 0-180")
                except (ValueError, IndexError):
                    print("  ⚠ Usage: smooth <angle>")
            else:
                try:
                    angle = int(cmd)
                    if 0 <= angle <= 180:
                        print(f"  → Moving to {angle}°...")
                        servo.set_angle(angle)
                    else:
                        print("  ⚠ Angle must be 0-180")
                except ValueError:
                    print("  ⚠ Unknown command. Type 'quit' to exit.")
        
        except KeyboardInterrupt:
            print("\n")
            break


def main():
    print("=" * 50)
    print("🤖 Servo Test for Raspberry Pi 5 (Jitter-Free)")
    print("   HobbyPark 25KG Servo (180°)")
    print("   Using pigpio hardware-timed PWM")
    print("=" * 50)
    print(f"\nUsing GPIO pin: {GPIO_PIN} (Physical pin 12)")
    print("\n⚠️  IMPORTANT: Use external power for the servo!")
    print("   Do NOT power from Pi's 5V pin.\n")
    
    # Connect to pigpio daemon
    print("Connecting to pigpio daemon...")
    pi = pigpio.pi()
    
    if not pi.connected:
        print("\n❌ Error: Could not connect to pigpio daemon!")
        print("\nTo fix this, run:")
        print("  sudo pigpiod")
        print("\nTo start automatically on boot:")
        print("  sudo systemctl enable pigpiod")
        sys.exit(1)
    
    print("✓ Connected to pigpio daemon!\n")
    
    # Create servo controller
    servo = Servo(pi, GPIO_PIN, MIN_PULSE, MAX_PULSE)
    
    try:
        # Center the servo first
        print("Centering servo (90°)...")
        servo.set_angle(90)
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
        servo.release()
        pi.stop()
        print("✓ Done! Servo released, pigpio connection closed.")


if __name__ == "__main__":
    main()
