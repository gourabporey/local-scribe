# main.py
import sys
import json
import sounddevice as sd
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget)
from PySide6.QtGui import QTextCursor
from PySide6.QtCore import QThread, Signal

from playsound import playsound
from pynput.keyboard import Controller

# Our module imports
from transcriber import TranscriberThread, HotkeyRecorderThread 
from hotkey_listener import HotkeyListenerThread

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Local Scribe")
        self.setGeometry(100, 100, 600, 400)

        # --- Model Path ---
        self.model_path = "vosk-model-small-en-in-0.4"

        # --- UI Elements ---
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)
        
        self.transcription_display = QTextEdit()
        self.transcription_display.setReadOnly(True)
        self.transcription_display.setPlaceholderText("Press 'Start' for continuous transcription.\nPress Ctrl+Shift+X to start/stop recording anywhere.")
        
        self.toggle_button = QPushButton("Start Transcription")
        self.toggle_button.setCheckable(True)
        
        layout.addWidget(self.transcription_display)
        layout.addWidget(self.toggle_button)

        # --- Continuous Transcription Thread ---
        self.transcriber_thread = TranscriberThread(model_path=self.model_path)
        
        # --- Hotkey State Management ---
        self.keyboard_controller = Controller()
        self.is_hotkey_recording = False
        self.hotkey_recorder_thread = None
        self._was_continuous_running = False # Flag to remember continuous state
        self.setup_hotkey_listener()

        # --- Connections ---
        self.toggle_button.clicked.connect(self.toggle_transcription)
        self.transcriber_thread.transcription_ready.connect(self.on_transcription_ready)
        self.transcriber_thread.partial_result_ready.connect(self.on_partial_result)

    def setup_hotkey_listener(self):
        self.hotkey_listener = HotkeyListenerThread(self)
        self.hotkey_listener.hotkey_activated.connect(self.toggle_hotkey_transcription)
        self.hotkey_listener.start()

    def toggle_hotkey_transcription(self):
        if not self.is_hotkey_recording:
            # --- START RECORDING ---
            self.is_hotkey_recording = True
            
            # --- NEW: Traffic Controller Logic (Pause continuous transcription) ---
            if self.toggle_button.isChecked():
                self._was_continuous_running = True
                print("Pausing continuous transcription to prioritize hotkey...")
                self.toggle_button.setChecked(False) # This will trigger the stop logic
                self.toggle_transcription(False)
            else:
                self._was_continuous_running = False
            self.toggle_button.setEnabled(False) # Disable button during recording
            # --- End of new logic ---

            try:
                playsound('start.mp3', block=False)
                self.hotkey_recorder_thread = HotkeyRecorderThread(model_path=self.model_path)
                self.hotkey_recorder_thread.transcription_finished.connect(self.on_hotkey_transcription_finished)
                self.hotkey_recorder_thread.finished.connect(self.on_recorder_thread_finished)
                self.hotkey_recorder_thread.start()
            except Exception as e:
                print(f"Error starting hotkey recording: {e}")
                self.is_hotkey_recording = False
                self.toggle_button.setEnabled(True) # Re-enable button on error

        else:
            # --- STOP RECORDING ---
            if self.hotkey_recorder_thread and self.hotkey_recorder_thread.isRunning():
                self.hotkey_recorder_thread.stop()

    def on_hotkey_transcription_finished(self, text):
        try:
            playsound('start.mp3', block=False)
            if text:
                self.keyboard_controller.type(text)
        except Exception as e:
            print(f"Error during typing or playing sound: {e}")

    def on_recorder_thread_finished(self):
        self.is_hotkey_recording = False
        self.hotkey_recorder_thread = None
        
        # --- NEW: Traffic Controller Logic (Resume continuous transcription) ---
        self.toggle_button.setEnabled(True) # Re-enable the button
        if self._was_continuous_running:
            print("Resuming continuous transcription...")
            self.toggle_button.setChecked(True)
            self.toggle_transcription(True)
            self._was_continuous_running = False
        # --- End of new logic ---
            
    def toggle_transcription(self, checked):
        if checked:
            # Prevent starting if hotkey is active
            if self.is_hotkey_recording:
                self.toggle_button.setChecked(False)
                return
            self.toggle_button.setText("Stop Transcription")
            self.transcriber_thread.start()
        else:
            self.toggle_button.setText("Start Transcription")
            if self.transcriber_thread.isRunning():
                self.transcriber_thread.stop()
                self.transcriber_thread.wait() 

    def on_transcription_ready(self, text):
        if text:
            self.transcription_display.append(f"-> {text}\n")

    def on_partial_result(self, text):
        cursor = self.transcription_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.select(QTextCursor.SelectionType.LineUnderCursor)
        cursor.removeSelectedText()
        cursor.insertText(text)

    def closeEvent(self, event):
        self.hotkey_listener.stop()
        self.hotkey_listener.wait()
        if self.transcriber_thread.isRunning():
            self.transcriber_thread.stop()
            self.transcriber_thread.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())