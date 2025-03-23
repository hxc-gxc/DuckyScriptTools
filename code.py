# Ducky Script Interpreter for HackyPi with ST7789 Display
# Place this in code.py and put your Ducky Script in payload.txt
# Supports automatic conversion from Flipper Zero scripts

import time
import os
import usb_hid
import board
import busio
import digitalio
import displayio
import terminalio
from adafruit_display_text import label
from adafruit_st7789 import ST7789
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode

# Debug mode - set to True to print to serial console
DEBUG = True

# Display configuration
BORDER = 10
FONTSCALE = 2
BACKGROUND_COLOR = 0x000000  # Black
SUCCESS_COLOR = 0x00FF00     # Green
ERROR_COLOR = 0xFF0000       # Red
WARNING_COLOR = 0xFFFF00     # Yellow
INFO_COLOR = 0x0000FF        # Blue
LOADING_COLOR = 0xFF8C00     # Orange
TEXT_COLOR = 0xFFFFFF        # White

# Initialize display
try:
    # Release any resources currently in use for the displays
    displayio.release_displays()
    
    # Configure SPI for display
    tft_clk = board.GP10  # must be a SPI CLK
    tft_mosi = board.GP11  # must be a SPI TX
    tft_rst = board.GP12
    tft_dc = board.GP8
    tft_cs = board.GP9
    spi = busio.SPI(clock=tft_clk, MOSI=tft_mosi)
    
    # Make the displayio SPI bus and the ST7789 display
    display_bus = displayio.FourWire(spi, command=tft_dc, chip_select=tft_cs, reset=tft_rst)
    display = ST7789(display_bus, rotation=270, width=240, height=135, rowstart=40, colstart=53)
    
    # Set up backlight
    tft_bl = board.GP13  # GPIO pin to control backlight LED
    backlight = digitalio.DigitalInOut(tft_bl)
    backlight.direction = digitalio.Direction.OUTPUT
    backlight.value = True
    
    HAS_DISPLAY = True
    if DEBUG:
        print("Display initialized successfully")
except Exception as e:
    if DEBUG:
        print(f"Display initialization failed: {e}")
    HAS_DISPLAY = False

# Initialize keyboard
kbd = Keyboard(usb_hid.devices)
layout = KeyboardLayoutUS(kbd)
cc = ConsumerControl(usb_hid.devices)

# Key mapping
KEY_MAPPING = {
    # Regular keys
    "ENTER": Keycode.ENTER,
    "RETURN": Keycode.ENTER,
    "ESCAPE": Keycode.ESCAPE,
    "ESC": Keycode.ESCAPE,
    "BACKSPACE": Keycode.BACKSPACE,
    "TAB": Keycode.TAB,
    "SPACE": Keycode.SPACE,
    "CAPSLOCK": Keycode.CAPS_LOCK,
    "PRINTSCREEN": Keycode.PRINT_SCREEN,
    "SCROLLLOCK": Keycode.SCROLL_LOCK,
    "SCROLLOCK": Keycode.SCROLL_LOCK,  # Common typo in scripts
    "PAUSE": Keycode.PAUSE,
    "INSERT": Keycode.INSERT,
    "HOME": Keycode.HOME,
    "PAGEUP": Keycode.PAGE_UP,
    "DELETE": Keycode.DELETE,
    "END": Keycode.END,
    "PAGEDOWN": Keycode.PAGE_DOWN,
    "RIGHT": Keycode.RIGHT_ARROW,
    "RIGHTARROW": Keycode.RIGHT_ARROW,
    "LEFT": Keycode.LEFT_ARROW,
    "LEFTARROW": Keycode.LEFT_ARROW,
    "DOWN": Keycode.DOWN_ARROW,
    "DOWNARROW": Keycode.DOWN_ARROW,
    "UP": Keycode.UP_ARROW,
    "UPARROW": Keycode.UP_ARROW,
    "NUMLOCK": Keycode.KEYPAD_NUMLOCK,
    "BREAK": Keycode.PAUSE,
    
    # Function keys
    "F1": Keycode.F1,
    "F2": Keycode.F2,
    "F3": Keycode.F3,
    "F4": Keycode.F4,
    "F5": Keycode.F5,
    "F6": Keycode.F6,
    "F7": Keycode.F7,
    "F8": Keycode.F8,
    "F9": Keycode.F9,
    "F10": Keycode.F10,
    "F11": Keycode.F11,
    "F12": Keycode.F12,
    
    # Modifiers
    "CTRL": Keycode.CONTROL,
    "CONTROL": Keycode.CONTROL,
    "SHIFT": Keycode.SHIFT,
    "ALT": Keycode.ALT,
    "GUI": Keycode.GUI,
    "WINDOWS": Keycode.GUI,
    "COMMAND": Keycode.GUI,
    "OPTION": Keycode.ALT,
    "MENU": Keycode.APPLICATION,
    "APP": Keycode.APPLICATION,
    
    # Media keys
    "MUTE": ConsumerControlCode.MUTE,
    "VOLUMEUP": ConsumerControlCode.VOLUME_INCREMENT,
    "VOLUMEDOWN": ConsumerControlCode.VOLUME_DECREMENT,
    "PLAYPAUSE": ConsumerControlCode.PLAY_PAUSE,
    "STOP": ConsumerControlCode.STOP,
    "NEXT": ConsumerControlCode.SCAN_NEXT_TRACK,
    "PREVIOUS": ConsumerControlCode.SCAN_PREVIOUS_TRACK,
}

def create_screen(bg_color):
    """Create a fresh screen with background color"""
    if not HAS_DISPLAY:
        return None
        
    # Make a display group
    splash = displayio.Group()
    display.show(splash)
    
    # Create the background
    color_bitmap = displayio.Bitmap(display.width, display.height, 1)
    color_palette = displayio.Palette(1)
    color_palette[0] = bg_color
    
    bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
    splash.append(bg_sprite)
    
    return splash

def show_status(message, bg_color=BACKGROUND_COLOR, text_color=TEXT_COLOR):
    """Display a status message on the screen"""
    log(message)  # Always log message to console
    
    if not HAS_DISPLAY:
        return
        
    # Create new screen with specified background color
    splash = create_screen(bg_color)
    
    # Display main message text in center
    text_area = label.Label(terminalio.FONT, text=message, color=text_color)
    text_group = displayio.Group(
        scale=FONTSCALE,
        x=display.width//2 - (len(message) * FONTSCALE * 3),
        y=display.height//2
    )
    text_group.append(text_area)
    splash.append(text_group)
    
    # Add "HackyPi" text at the top
    title = label.Label(terminalio.FONT, text="HackyPi", color=text_color)
    title_group = displayio.Group(scale=1, x=5, y=10)
    title_group.append(title)
    splash.append(title_group)
    
    # Blink the backlight briefly to indicate status change
    if bg_color != BACKGROUND_COLOR:
        backlight.value = False
        time.sleep(0.1)
        backlight.value = True

def log(message):
    """Print debug messages if DEBUG is enabled"""
    if DEBUG:
        print(message)

def press_keys(keys):
    """Press a combination of keys"""
    is_consumer_key = False
    consumer_key = None
    
    # Check if this is a consumer key (media control)
    for key in keys:
        if isinstance(KEY_MAPPING.get(key), int) and KEY_MAPPING.get(key) >= 0xE8:
            is_consumer_key = True
            consumer_key = KEY_MAPPING.get(key)
            break
    
    if is_consumer_key and consumer_key:
        cc.send(consumer_key)
    else:
        for key in keys:
            if key in KEY_MAPPING:
                kbd.press(KEY_MAPPING[key])
        time.sleep(0.01)  # Small delay to register key presses
        kbd.release_all()

def press_modifier_and_key(modifier, key):
    """Press a modifier key and another key together"""
    if modifier in KEY_MAPPING and key in KEY_MAPPING:
        kbd.press(KEY_MAPPING[modifier])
        time.sleep(0.05)  # Small delay between pressing modifier and key
        kbd.press(KEY_MAPPING[key])
        time.sleep(0.05)  # Hold both keys briefly
        kbd.release_all()
    else:
        log(f"Unknown modifier or key: {modifier} + {key}")

def convert_flipper_to_standard_ducky(lines):
    """Convert Flipper Zero Ducky script to standard format"""
    converted_lines = []
    is_flipper_script = False
    
    # Check if it looks like a Flipper Zero script
    for line in lines:
        if line.startswith("ID ") or "USB Keyboard" in line:
            is_flipper_script = True
            break
    
    if not is_flipper_script:
        log("Script appears to be in standard Ducky format, no conversion needed")
        return lines
    
    log("Detected Flipper Zero script format, converting...")
    show_status("CONVERTING", bg_color=INFO_COLOR)
    
    # Process the lines for conversion
    for line in lines:
        line = line.strip()
        
        # Skip Flipper Zero specific headers
        if line.startswith("ID ") or "USB Keyboard" in line:
            continue
            
        # Convert ESC to ESCAPE for better compatibility
        if line == "ESC":
            converted_lines.append("ESCAPE")
        # LED ON/OFF commands (not directly supported but keep them)
        elif line == "LED ON" or line == "LED OFF":
            converted_lines.append(line)
        else:
            converted_lines.append(line)
    
    log(f"Conversion complete. Converted {len(lines)} lines to {len(converted_lines)} lines.")
    return converted_lines

def execute_ducky_script(filename):
    """Execute commands from a Ducky Script file"""
    try:
        show_status("LOADING", bg_color=ERROR_COLOR)
        
        with open(filename, 'r') as f:
            lines = f.readlines()
        
        # Convert the script if needed
        lines = convert_flipper_to_standard_ducky(lines)
        
        default_delay = 0
        current_line = 0
        
        # Initial wait for device recognition
        time.sleep(1)
        
        show_status("RUNNING", bg_color=LOADING_COLOR)
        
        while current_line < len(lines):
            line = lines[current_line].strip()
            current_line += 1
            
            # Skip empty lines and comments
            if not line or line.startswith("//") or line.startswith("REM") or line.startswith("#"):
                continue
            
            log(f"Executing: {line}")
            
            # Apply default delay from prior commands
            if default_delay > 0:
                time.sleep(default_delay / 1000)
            
            # Process commands
            parts = line.split(" ", 1)
            command = parts[0].upper()
            
            # Specific handling for "ALT F2" and similar patterns (for run dialog)
            if command == "ALT" and len(parts) > 1:
                key = parts[1].upper()
                log(f"Executing ALT+{key} combination")
                press_modifier_and_key("ALT", key)
                continue  # Skip the rest of the loop for this iteration
                
            # Also handle GUI and CTRL combinations with similar syntax
            elif command == "GUI" and len(parts) > 1:
                key = parts[1].upper()
                log(f"Executing GUI+{key} combination")
                press_modifier_and_key("GUI", key)
                continue
                
            elif command == "CTRL" and len(parts) > 1:
                key = parts[1].upper()
                log(f"Executing CTRL+{key} combination")
                press_modifier_and_key("CTRL", key)
                continue
                
            elif command == "SHIFT" and len(parts) > 1:
                key = parts[1].upper()
                log(f"Executing SHIFT+{key} combination")
                press_modifier_and_key("SHIFT", key)
                continue
                
            elif command == "DELAY":
                # Delay specified number of milliseconds
                if len(parts) > 1:
                    delay_time = int(parts[1]) / 1000
                    time.sleep(delay_time)
            
            elif command == "DEFAULT_DELAY" or command == "DEFAULTDELAY":
                # Set default delay between commands
                if len(parts) > 1:
                    default_delay = int(parts[1])
            
            elif command == "STRING":
                # Type a string of characters
                if len(parts) > 1:
                    layout.write(parts[1])
            
            elif command == "TYPSPEED":
                # TypeSpeed isn't directly supported in CircuitPython, so we log it
                log("TYPSPEED command is not supported in this implementation")
            
            elif command == "LED":
                # Use display backlight for LED commands
                if len(parts) > 1 and parts[1].upper() == "ON":
                    log("LED ON command received")
                    backlight.value = True
                elif len(parts) > 1 and parts[1].upper() == "OFF":
                    log("LED OFF command received")
                    backlight.value = False
            
            elif command == "WAIT_FOR_BUTTON_PRESS":
                log("WAIT_FOR_BUTTON_PRESS not applicable, continuing")
            
            elif command == "PRESS":
                # Special handling for PRESS command
                if len(parts) > 1:
                    key = parts[1].upper()
                    if key in KEY_MAPPING:
                        kbd.send(KEY_MAPPING[key])
            
            elif "-" in command:
                # Handle combined keys like CTRL-ALT-DELETE
                combo = command.split("-")
                press_keys(combo)
            
            else:
                # Single key commands
                if command in KEY_MAPPING:
                    # Special case for media keys
                    if isinstance(KEY_MAPPING[command], int) and KEY_MAPPING[command] >= 0xE8:
                        cc.send(KEY_MAPPING[command])
                    else:
                        kbd.send(KEY_MAPPING[command])
                
                # Handle key combinations with a simple character
                elif len(parts) > 1 and parts[0] in KEY_MAPPING:
                    modifier = KEY_MAPPING[parts[0]]
                    key = parts[1].upper()
                    if len(key) == 1:  # It's a single character
                        kbd.press(modifier)
                        layout.write(key)
                        kbd.release_all()
                    elif key in KEY_MAPPING:  # It's a named key
                        kbd.press(modifier)
                        kbd.press(KEY_MAPPING[key])
                        kbd.release_all()
                
                else:
                    log(f"Unknown command: {command}")
        
        log("Script execution completed")
        show_status("EXECUTED", bg_color=SUCCESS_COLOR)
        
        # Blink the backlight 3 times to signal completion
        for _ in range(3):
            backlight.value = False
            time.sleep(0.2)
            backlight.value = True
            time.sleep(0.2)
        
    except Exception as e:
        log(f"Error: {e}")
        show_status("ERROR", bg_color=ERROR_COLOR)
        
        # Error indicator pattern - blink backlight rapidly 5 times
        for _ in range(5):
            backlight.value = False
            time.sleep(0.1)
            backlight.value = True
            time.sleep(0.1)

# Main program
try:
    # Welcome screen
    splash = create_screen(BACKGROUND_COLOR)
    
    # Title
    title = label.Label(terminalio.FONT, text="HackyPi", color=TEXT_COLOR)
    title_group = displayio.Group(scale=3, x=60, y=30)
    title_group.append(title)
    splash.append(title_group)
    
    # Subtitle
    subtitle = label.Label(terminalio.FONT, text="Ducky Script Interpreter", color=TEXT_COLOR)
    subtitle_group = displayio.Group(scale=1, x=50, y=60)
    subtitle_group.append(subtitle)
    splash.append(subtitle_group)
    
    # Version
    version = label.Label(terminalio.FONT, text="v1.0", color=TEXT_COLOR)
    version_group = displayio.Group(scale=1, x=105, y=80)
    version_group.append(version)
    splash.append(version_group)
    
    # Visual startup effect - pulse the backlight
    for _ in range(3):
        backlight.value = False
        time.sleep(0.1)
        backlight.value = True
        time.sleep(0.2)
    
    time.sleep(1)  # Show welcome screen for 1 second
    
    log("HackyPi Ducky Script Interpreter starting...")
    
    if "payload.txt" in os.listdir("/"):
        log("Found payload.txt, executing...")
        show_status("FOUND SCRIPT", bg_color=INFO_COLOR)
        time.sleep(0.5)
        execute_ducky_script("/payload.txt")
    else:
        log("No payload.txt found! Please create a payload.txt file.")
        show_status("NO SCRIPT", bg_color=WARNING_COLOR)
        
        # Look for other potential script files
        potential_scripts = []
        for file in os.listdir("/"):
            if file.endswith(".txt") and file != "code.py":
                potential_scripts.append(file)
                log(f"Found potential script file: {file}")
        
        # Show alternative scripts if found
        if potential_scripts:
            # Create warning screen
            splash = create_screen(WARNING_COLOR)
            
            # Add title
            title = label.Label(terminalio.FONT, text="Missing payload.txt", color=TEXT_COLOR)
            title_group = displayio.Group(scale=1, x=60, y=20)
            title_group.append(title)
            splash.append(title_group)
            
            # List alternative files
            y_pos = 40
            subtitle = label.Label(terminalio.FONT, text="Found these files:", color=TEXT_COLOR)
            subtitle_group = displayio.Group(scale=1, x=60, y=y_pos)
            subtitle_group.append(subtitle)
            splash.append(subtitle_group)
            
            for i, script in enumerate(potential_scripts[:3]):  # Show up to 3 alternative files
                y_pos += 20
                file_text = label.Label(terminalio.FONT, text=f"- {script}", color=TEXT_COLOR)
                file_group = displayio.Group(scale=1, x=40, y=y_pos)
                file_group.append(file_text)
                splash.append(file_group)
            
            # Blink the backlight to get attention
            for _ in range(5):
                backlight.value = False
                time.sleep(0.2)
                backlight.value = True
                time.sleep(0.2)
except Exception as e:
    log(f"Error in main: {e}")
    if HAS_DISPLAY:
        show_status("FATAL ERROR", bg_color=ERROR_COLOR)
    
    # Fatal error - rapid blink pattern
    for _ in range(10):
        if HAS_DISPLAY:
            backlight.value = False
            time.sleep(0.1)
            backlight.value = True
            time.sleep(0.1)