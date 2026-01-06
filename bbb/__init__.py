# BBB (Boredom Buster Bot) shared library
from bbb.servo import (
    ServoController,
    SERVO_ENABLED,
    GPIO_PIN,
    MOUTH_CLOSED,
    MOUTH_OPEN,
    MOUTH_HALF,
    init_servo,
    move_mouth,
    mouth_talking_animation,
    laugh_animation,
)

from bbb.tts import (
    check_tts_available,
    speak_with_pico,
    speak_text_sync,
    speak_text_async,
)

