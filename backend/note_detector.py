import librosa
import numpy as np
import sounddevice as sd

class NoteDetector:
    def __init__(self):
        self.sample_rate = 44100
        self.notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
    def frequency_to_note(self, frequency):
        if frequency == 0:
            return None
        
        # A4 = 440Hz
        note_number = 12 * np.log2(frequency / 440) + 49
        note_number = round(note_number)
        
        # Get note name and octave
        note_name = self.notes[note_number % 12]
        octave = (note_number - 12) // 12
        return f"{note_name}{octave}"
    
    def record_audio(self, duration=3):
        print("Recording...")
        audio = sd.rec(int(duration * self.sample_rate),
                      samplerate=self.sample_rate,
                      channels=1)
        sd.wait()
        return audio.flatten()
    
    def detect_notes(self, audio):
        # Compute pitch using librosa
        pitches, magnitudes = librosa.piptrack(y=audio,
                                             sr=self.sample_rate)
        
        detected_notes = []
        
        # Process each frame
        for i in range(pitches.shape[1]):
            index = magnitudes[:, i].argmax()
            pitch = pitches[index, i]
            
            if pitch > 0:  # If pitch is detected
                note = self.frequency_to_note(pitch)
                if note and note not in detected_notes:
                    detected_notes.append(note)
        
        return detected_notes 