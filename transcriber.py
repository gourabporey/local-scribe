# transcriber.py
import json
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer
from PySide6.QtCore import QThread, Signal

class TranscriberThread(QThread):
    """
    A QThread that runs the VOSK transcription in the background.
    """
    # Signal to emit the transcribed text
    transcription_ready = Signal(str)
    # Signal to emit partial (in-progress) results
    partial_result_ready = Signal(str)

    def __init__(self, model_path, parent=None):
        super().__init__(parent)
        self.model_path = model_path
        self.running = False
        self.audio_queue = queue.Queue()

    def _audio_callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status)
        self.audio_queue.put(bytes(indata))

    def run(self):
        """The main loop of the transcription thread."""
        try:
            model = Model(self.model_path)
            # Get the default input device information
            device_info = sd.query_devices(sd.default.device[0], 'input')
            samplerate = int(device_info['default_samplerate'])
            
            recognizer = KaldiRecognizer(model, samplerate)
            recognizer.SetWords(True) # To get partial results

            # Open the microphone stream
            with sd.RawInputStream(samplerate=samplerate, blocksize=8000,
                                   device=None, dtype='int16',
                                   channels=1, callback=self._audio_callback):
                
                self.running = True
                while self.running:
                    data = self.audio_queue.get()
                    if recognizer.AcceptWaveform(data):
                        # Final result after a pause
                        result = json.loads(recognizer.Result())
                        self.transcription_ready.emit(result['text'])
                    else:
                        # Partial, in-progress result
                        partial_result = json.loads(recognizer.PartialResult())
                        self.partial_result_ready.emit(partial_result['partial'])

        except Exception as e:
            print(f"Error in transcription thread: {e}")

    def stop(self):
        """Stops the transcription loop."""
        self.running = False


class HotkeyRecorderThread(QThread):
    """
    A QThread that starts recording on run() and stops when stop() is called.
    It then processes the entire captured audio and emits the result.
    """
    transcription_finished = Signal(str)

    def __init__(self, model_path, parent=None):
        super().__init__(parent)
        self.model_path = model_path
        self._is_running = False

    def run(self):
        """Initializes the recognizer and records audio until stopped."""
        self._is_running = True
        print("Hotkey recording started... Press hotkey again to stop.")
        
        try:
            model = Model(self.model_path)
            device_info = sd.query_devices(sd.default.device[0], 'input')
            samplerate = int(device_info['default_samplerate'])
            recognizer = KaldiRecognizer(model, samplerate)

            with sd.InputStream(samplerate=samplerate, channels=1, dtype='int16') as stream:
                while self._is_running:
                    # Continuously read audio and feed it to the recognizer
                    data, overflowed = stream.read(4000)
                    recognizer.AcceptWaveform(bytes(data))

            # Once the loop is stopped, process the final result
            result = json.loads(recognizer.FinalResult())
            final_text = result.get('text', '')
            print(f"--> Final hotkey result: '{final_text}'")
            self.transcription_finished.emit(final_text)

        except Exception as e:
            print(f"Error in HotkeyRecorderThread: {e}")
        finally:
            print("Hotkey recording finished.")

    def stop(self):
        """Signals the recording loop to stop."""
        self._is_running = False