# BBB (Boredom Buster Bot) shared library
# Servo imports
from bbb.servo import (
    ServoController,
    SERVO_ENABLED,
    GPIO_PIN,
    HAND_DOWN,
    HAND_UP,
    HAND_MIDDLE,
    MOUTH_CLOSED,
    MOUTH_OPEN,
    MOUTH_HALF,
    init_servo,
    get_servo,
    get_servo_lock,
    get_servo_error,
    move_hand,
    hand_talking_animation,
    joke_setup_animation,
    punchline_animation,
    hand_slap_animation,
)

# TTS imports
from bbb.tts import (
    check_tts_available,
    init_tts,
    get_tts_command,
    speak_with_pico,
    speak_with_espeak,
    speak_text_sync,
    speak_text_async,
)

