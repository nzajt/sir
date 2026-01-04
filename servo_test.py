#!/usr/bin/env python3
"""
Servo Test Script for Raspberry Pi 5
=====================================
For: HobbyPark 25KG Servo (180° control angle)

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
# Install required packages on Raspberry Pi 5:
sudo apt update
sudo apt install python3-gpiozero python3-lgpio

# Run this script:
python3 servo_test.py
"""

import sys
import time

try:
    from gpiozero import Servo
    from gpiozero.pins.lgpio import LGPIOFactory
except ImportError:
    print("Error: gpiozero not installed!")
    print("Run: sudo apt install python3-gpiozero python3-lgpio")
    sys.exit(1)

# Use lgpio backend for Raspberry Pi 5 compatibility
try:
    from gpiozero import Device
    Device.pin_factory = LGPIOFactory()
except Exception as e:
    print(f"Warning: Could not set lgpio factory: {e}")
    print("Continuing with default pin factory...")

# Configuration
GPIO_PIN = 18  # GPIO 18 = Physical Pin 12

# Servo pulse width calibration (adjust if servo doesn't reach full range)
# Standard servo: min=1ms, max=2ms for 180°
# These values are in the range -1 to 1 for gpiozero
MIN_PULSE_WIDTH = 0.0005  # 0.5ms - adjust if servo doesn't go to 0°
MAX_PULSE_WIDTH = 0.0025  # 2.5ms - adjust if servo doesn't go to 180°


def create_servo():
    """Create and return a servo object."""
    try:
        servo = Servo(
            GPIO_PIN,
            min_pulse_width=MIN_PULSE_WIDTH,
            max_pulse_width=MAX_PULSE_WIDTH
        )
        return servo
    except Exception as e:
        print(f"Error creating servo: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you're running on a Raspberry Pi")
        print("2. Check that lgpio is installed: sudo apt install python3-lgpio")
        print("3. Verify GPIO pin is not in use by another process")
        sys.exit(1)


def angle_to_value(angle):
    """Convert angle (0-180) to gpiozero servo value (-1 to 1)."""
    # 0° = -1, 90° = 0, 180° = 1
    return (angle / 90) - 1


def set_angle(servo, angle):
    """Move servo to specified angle (0-180 degrees)."""
    angle = max(0, min(180, angle))  # Clamp to valid range
    servo.value = angle_to_value(angle)
    print(f"  → Moved to {angle}°")


def sweep_test(servo):
    """Perform a full sweep test from 0° to 180° and back."""
    print("\n🔄 Sweep Test: 0° → 180° → 0°")
    print("-" * 30)
    
    # Sweep from 0 to 180
    for angle in range(0, 181, 10):
        set_angle(servo, angle)
        time.sleep(0.1)
    
    time.sleep(0.5)
    
    # Sweep from 180 to 0
    for angle in range(180, -1, -10):
        set_angle(servo, angle)
        time.sleep(0.1)
    
    print("✓ Sweep complete!")


def position_test(servo):
    """Test specific positions: 0°, 45°, 90°, 135°, 180°."""
    print("\n📍 Position Test")
    print("-" * 30)
    
    positions = [0, 45, 90, 135, 180, 90]
    
    for pos in positions:
        print(f"\nMoving to {pos}°...")
        set_angle(servo, pos)
        time.sleep(1)
    
    print("\n✓ Position test complete!")


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
    print("  off    : Disable servo (stop holding position)")
    print("  quit   : Exit program")
    print()
    
    while True:
        try:
            cmd = input("Enter command: ").strip().lower()
            
            if cmd == 'quit' or cmd == 'q':
                break
            elif cmd == 'sweep':
                sweep_test(servo)
            elif cmd == 'center':
                set_angle(servo, 90)
            elif cmd == 'min':
                set_angle(servo, 0)
            elif cmd == 'max':
                set_angle(servo, 180)
            elif cmd == 'off':
                servo.detach()
                print("  → Servo disabled (not holding position)")
            else:
                try:
                    angle = int(cmd)
                    if 0 <= angle <= 180:
                        set_angle(servo, angle)
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
    print("=" * 50)
    print(f"\nUsing GPIO pin: {GPIO_PIN} (Physical pin 12)")
    print("\n⚠️  IMPORTANT: Use external power for the servo!")
    print("   Do NOT power from Pi's 5V pin.\n")
    
    # Create servo
    print("Initializing servo...")
    servo = create_servo()
    print("✓ Servo initialized!\n")
    
    try:
        # Center the servo first
        print("Centering servo (90°)...")
        set_angle(servo, 90)
        time.sleep(1)
        
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
        servo.detach()  # Stop sending PWM signal
        print("✓ Done! Servo released.")


if __name__ == "__main__":
    main()

