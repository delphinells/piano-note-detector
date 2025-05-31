from flask import Flask, request, jsonify, send_from_directory
import numpy as np
import librosa
import os
import soundfile as sf
import io

app = Flask(__name__, static_folder='wwwroot')

# Nota isimlerinin Türkçe karşılıkları
NOTE_NAMES_TR = {
    'C': 'Do',
    'C#': 'Do#',
    'D': 'Re',
    'D#': 'Re#',
    'E': 'Mi',
    'F': 'Fa',
    'F#': 'Fa#',
    'G': 'Sol',
    'G#': 'Sol#',
    'A': 'La',
    'A#': 'La#',
    'B': 'Si'
}

# Akor türleri ve Türkçe isimleri
CHORD_TYPES = {
    'major': 'Majör',
    'minor': 'Minör',
    'diminished': 'Diminiş',
    'augmented': 'Artırılmış',
    'sus4': 'Sus4',
    'sus2': 'Sus2',
    '7': 'Dominant 7'
}

# Akor aralıkları (yarım ton cinsinden)
CHORD_INTERVALS = {
    'major': [0, 4, 7],  # Majör (örn: Do-Mi-Sol)
    'minor': [0, 3, 7],  # Minör (örn: Do-Mib-Sol)
    'diminished': [0, 3, 6],  # Diminiş (örn: Do-Mib-Solb)
    'augmented': [0, 4, 8],  # Artırılmış (örn: Do-Mi-Sol#)
    'sus4': [0, 5, 7],  # Sus4 (örn: Do-Fa-Sol)
    'sus2': [0, 2, 7],  # Sus2 (örn: Do-Re-Sol)
    '7': [0, 4, 7, 10]  # Dominant 7 (örn: Do-Mi-Sol-Sib)
}

# Akor bileşenlerinin açıklamaları
CHORD_COMPONENTS = {
    'major': ['kök', 'majör 3\'lü', 'tam 5\'li'],
    'minor': ['kök', 'minör 3\'lü', 'tam 5\'li'],
    'diminished': ['kök', 'minör 3\'lü', 'azaltılmış 5\'li'],
    'augmented': ['kök', 'majör 3\'lü', 'artırılmış 5\'li'],
    'sus4': ['kök', '4\'lü', 'tam 5\'li'],
    'sus2': ['kök', '2\'li', 'tam 5\'li'],
    '7': ['kök', 'majör 3\'lü', 'tam 5\'li', 'minör 7\'li']
}

# Ana dizin için route
@app.route('/')
def index():
    return send_from_directory('wwwroot', 'index.html')

# Statik dosyalar için route
@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('wwwroot', path)

# Nota tespiti için API endpoint'i
@app.route('/api/detect-note', methods=['POST'])
def detect_note():
    try:
        audio_data = request.get_json().get('audio')
        if not audio_data:
            return jsonify({'error': 'Ses verisi bulunamadı'}), 400

        # Ses verisini numpy dizisine dönüştür
        audio_array = np.array(audio_data, dtype=np.float32)
        
        # Örnekleme hızı
        sr = 44100
        
        # Ses sinyalini normalize et
        audio_array = librosa.util.normalize(audio_array)
        
        # Pitch tespiti için parametreler
        frame_length = 2048
        hop_length = 512
        fmin = librosa.note_to_hz('C2')
        fmax = librosa.note_to_hz('C7')
        
        # Chroma özelliği hesapla (akor tespiti için)
        chroma = librosa.feature.chroma_cqt(y=audio_array, sr=sr,
                                          hop_length=hop_length,
                                          fmin=fmin)
        
        # En güçlü notaları bul
        strongest_notes = []
        chroma_sum = np.sum(chroma, axis=1)
        threshold = np.max(chroma_sum) * 0.3  # Eşik değeri
        
        for i, magnitude in enumerate(chroma_sum):
            if magnitude > threshold:
                note_name = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'][i]
                strongest_notes.append(note_name)
        
        # Pitch tespiti
        pitches, magnitudes = librosa.piptrack(
            y=audio_array,
            sr=sr,
            n_fft=frame_length,
            hop_length=hop_length,
            fmin=fmin,
            fmax=fmax
        )
        
        if pitches.size == 0 or magnitudes.size == 0:
            return jsonify({'error': 'Ses sinyali çok zayıf'}), 400
        
        # En güçlü pitch'i bul
        magnitudes_sum = np.sum(magnitudes, axis=1)
        strongest_bin = magnitudes_sum.argmax()
        frequency = pitches[strongest_bin][0]
        
        if frequency < 20 or frequency > 4000:  # İnsan kulağının duyabileceği aralık
            return jsonify({'error': 'Geçersiz frekans aralığı'}), 400
            
        # Frekansı notaya dönüştür
        note_en, octave = frequency_to_note(frequency)
        if not note_en:
            return jsonify({'error': 'Nota tespit edilemedi'}), 400
            
        # Akor tespiti
        chord_name = None
        chord_type = None
        chord_notes = None
        note_roles = None
        if len(strongest_notes) >= 3:
            chord_name, chord_type, chord_notes, note_roles = detect_chord(strongest_notes)
        
        # İngilizce nota ismini Türkçeye çevir
        note_tr = NOTE_NAMES_TR[note_en]
        note_full = f"{note_tr}{octave}"
        
        response_data = {
            'note': note_full,
            'note_en': f"{note_en}{octave}",
            'frequency': float(frequency),
            'detected_notes': [NOTE_NAMES_TR[n] for n in strongest_notes]
        }
        
        if chord_name and chord_type:
            response_data['chord'] = {
                'root': NOTE_NAMES_TR[chord_name],
                'type': CHORD_TYPES[chord_type],
                'full_name': f"{NOTE_NAMES_TR[chord_name]} {CHORD_TYPES[chord_type]}",
                'notes': chord_notes,
                'note_roles': note_roles
            }
            
        print(f"Tespit edilen nota: {note_full}, Frekans: {frequency:.2f} Hz")
        if chord_name:
            print(f"Tespit edilen akor: {response_data['chord']['full_name']}")
            print(f"Akor notaları: {', '.join(chord_notes)}")
            print(f"Nota rolleri: {', '.join(note_roles)}")
            
        return jsonify(response_data)
    
    except Exception as e:
        print(f"Hata: {str(e)}")
        return jsonify({'error': str(e)}), 500

def frequency_to_note(frequency):
    """Frekansı nota ismine dönüştürür."""
    if frequency <= 0:
        return None, None
    
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    # A4 = 440 Hz referans alınarak MIDI nota numarası hesapla
    midi_number = 69 + 12 * np.log2(frequency / 440.0)
    
    if midi_number < 21 or midi_number > 108:  # Piyano nota aralığı
        return None, None
        
    note_index = int(round(midi_number)) % 12
    octave = int((int(round(midi_number)) - 12) / 12)
    
    return note_names[note_index], octave

def detect_chord(notes):
    """Notalardan akor tespiti yapar."""
    if len(notes) < 3:
        return None, None, None, None
        
    # Notaları sayılara dönüştür (C=0, C#=1, ...)
    note_values = []
    for note in notes:
        note_values.append(['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'].index(note))
    
    # Her notayı kök nota kabul ederek akor tiplerini kontrol et
    best_match = None
    best_match_score = 0
    
    for root in note_values:
        intervals = [(((n - root) % 12) + 12) % 12 for n in note_values]
        intervals = sorted(list(set(intervals)))  # Tekrar eden notaları kaldır
        
        # Akor tiplerini kontrol et
        for chord_type, chord_intervals in CHORD_INTERVALS.items():
            # Akor aralıklarının ne kadarı mevcut
            matches = sum(1 for i in chord_intervals if i in intervals)
            # Fazladan nota var mı?
            extra_notes = sum(1 for i in intervals if i not in chord_intervals)
            
            # Eşleşme skoru hesapla
            score = matches - (extra_notes * 0.5)
            
            # Minimum 3 nota eşleşmesi gerekiyor
            if matches >= 3 and score > best_match_score:
                best_match = (root, chord_type)
                best_match_score = score
    
    if best_match:
        root, chord_type = best_match
        root_note = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'][root]
        
        # Akor bileşenlerini hesapla
        chord_notes = []
        note_roles = []
        for interval in CHORD_INTERVALS[chord_type]:
            note_idx = (root + interval) % 12
            note_name = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'][note_idx]
            chord_notes.append(NOTE_NAMES_TR[note_name])
            note_roles.append(CHORD_COMPONENTS[chord_type][CHORD_INTERVALS[chord_type].index(interval)])
        
        return root_note, chord_type, chord_notes, note_roles
                
    return None, None, None, None

if __name__ == '__main__':
    app.run(debug=True, port=5000) 