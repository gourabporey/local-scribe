# hotkey_listener.py
from pynput import keyboard
from PySide6.QtCore import QThread, Signal

# Define your desired hotkey combination
# <ctrl>+<shift>+x
HOTKEY_COMBINATION = {
    keyboard.Key.ctrl, 
    keyboard.Key.shift, 
    keyboard.KeyCode.from_char('x')
}

class HotkeyListenerThread(QThread):
    """
    A QThread that listens for a global hotkey combination.
    """
    hotkey_activated = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_keys = set()
        self.listener = None

    def on_press(self, key):
        """Callback for when a key is pressed."""
        if key in HOTKEY_COMBINATION:
            self.current_keys.add(key)
            if self.current_keys == HOTKEY_COMBINATION:
                print("Hotkey activated!")
                self.hotkey_activated.emit()

    def on_release(self, key):
        """Callback for when a key is released."""
        try:
            self.current_keys.remove(key)
        except KeyError:
            pass

    def run(self):
        """Starts the key listener loop."""
        print(f"Hotkey listener started. Press Ctrl+Shift+X to transcribe.")
        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as self.listener:
            self.listener.join()

    def stop(self):
        """Stops the key listener."""
        if self.listener:
            self.listener.stop()