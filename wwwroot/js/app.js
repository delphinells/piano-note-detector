document.addEventListener('DOMContentLoaded', function() {
    const pianoKeys = document.getElementById('piano-keys');
    const recordButton = document.getElementById('recordButton');
    const detectNoteButton = document.getElementById('detectNoteButton');
    const detectChordButton = document.getElementById('detectChordButton');
    const resultText = document.getElementById('result-text');
    const resultDetails = document.getElementById('result-details');
    const statusDisplay = document.getElementById('status');
    
    let isRecording = false;
    let audioContext = null;
    let analyser = null;
    let microphone = null;
    let processor = null;
    let recordedChunks = [];
    
    // Nota isimleri ve karşılıkları
    const NOTE_NAMES_TR = {
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
    };

    // Akor renkleri
    const CHORD_COLORS = {
        root: { bg: '#FF6B6B', text: '#fff' },      // Kırmızı
        third: { bg: '#4ECDC4', text: '#fff' },     // Turkuaz
        fifth: { bg: '#45B7D1', text: '#fff' },     // Mavi
        seventh: { bg: '#96CEB4', text: '#fff' }    // Yeşil
    };
    
    // Piyano tuşlarını oluştur
    const notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
    const octaves = [4, 5]; // 2 oktav göster

    octaves.forEach(octave => {
        notes.forEach((note, index) => {
            const key = document.createElement('div');
            const isSharp = note.includes('#');
            key.className = `piano-key ${isSharp ? 'black-key' : 'white-key'}`;
            key.dataset.note = `${note}${octave}`;
            key.dataset.noteTr = `${NOTE_NAMES_TR[note]}${octave}`;
            
            // Nota etiketi
            const noteLabel = document.createElement('span');
            noteLabel.className = 'note-label';
            noteLabel.textContent = NOTE_NAMES_TR[note];
            key.appendChild(noteLabel);

            // Aktif nota gösterimi için element
            const activeNote = document.createElement('div');
            activeNote.className = 'active-note-display';
            key.appendChild(activeNote);
            
            pianoKeys.appendChild(key);

            key.addEventListener('click', () => {
                highlightKey(key, null, key.dataset.noteTr);
            });
        });
    });

    recordButton.addEventListener('click', async () => {
        if (!isRecording) {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    audio: { 
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: false
                    } 
                });
                startRecording(stream);
            } catch (err) {
                console.error('Mikrofon erişimi hatası:', err);
                statusDisplay.textContent = 'Mikrofon erişimi reddedildi';
            }
        } else {
            stopRecording();
        }
    });

    detectNoteButton.addEventListener('click', async () => {
        await detectSound('note');
    });

    detectChordButton.addEventListener('click', async () => {
        await detectSound('chord');
    });

    async function detectSound(type) {
        if (recordedChunks.length === 0) {
            statusDisplay.textContent = 'Önce ses kaydı yapın';
            return;
        }

        detectNoteButton.disabled = true;
        detectChordButton.disabled = true;
        statusDisplay.textContent = `${type === 'note' ? 'Nota' : 'Akor'} tespit ediliyor...`;

        try {
            const audioData = averageAudioChunks(recordedChunks);
            const response = await sendAudioToServer(audioData);
            
            if (response) {
                clearKeyHighlights();
                
                if (type === 'note' && response.note) {
                    resultText.textContent = response.note;
                    resultDetails.textContent = `${response.frequency.toFixed(1)} Hz`;
                    const key = document.querySelector(`[data-note="${response.note_en}"]`);
                    if (key) highlightKey(key, CHORD_COLORS.root, response.note);
                } else if (type === 'chord' && response.chord) {
                    resultText.textContent = response.chord.full_name;
                    
                    // Akor bileşenlerini detaylı göster
                    const noteDetails = response.chord.notes.map((note, index) => {
                        const role = response.chord.note_roles[index];
                        const roleClass = getRoleClass(index);
                        return `<span class="chord-component ${roleClass}">${note} (${role})</span>`;
                    });
                    resultDetails.innerHTML = noteDetails.join(' - ');
                    
                    // Akor notalarını piyano üzerinde göster
                    response.chord.notes.forEach((note, index) => {
                        const key = document.querySelector(`[data-noteTr^="${note}"]`);
                        if (key) {
                            const role = response.chord.note_roles[index];
                            const color = getChordNoteColor(index);
                            highlightKey(key, color, `${note} (${role})`);
                        }
                    });
                } else {
                    resultText.textContent = '-';
                    resultDetails.textContent = `${type === 'note' ? 'Nota' : 'Akor'} tespit edilemedi`;
                }
            }
        } catch (error) {
            console.error('Tespit hatası:', error);
            statusDisplay.textContent = `${type === 'note' ? 'Nota' : 'Akor'} tespit edilemedi`;
        } finally {
            detectNoteButton.disabled = false;
            detectChordButton.disabled = false;
        }
    }

    function averageAudioChunks(chunks) {
        const totalSamples = chunks.reduce((acc, chunk) => acc + chunk.length, 0);
        const averagedData = new Float32Array(Math.floor(totalSamples / chunks.length));
        
        for (let i = 0; i < averagedData.length; i++) {
            let sum = 0;
            for (const chunk of chunks) {
                if (i < chunk.length) {
                    sum += chunk[i];
                }
            }
            averagedData[i] = sum / chunks.length;
        }
        
        return Array.from(averagedData);
    }

    async function startRecording(stream) {
        isRecording = true;
        recordedChunks = [];
        recordButton.classList.add('recording');
        recordButton.textContent = 'Kaydı Durdur';
        detectNoteButton.disabled = true;
        detectChordButton.disabled = true;
        statusDisplay.textContent = 'Kayıt yapılıyor...';
        resultText.textContent = '-';
        resultDetails.textContent = '-';

        try {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            analyser = audioContext.createAnalyser();
            microphone = audioContext.createMediaStreamSource(stream);
            processor = audioContext.createScriptProcessor(4096, 1, 1);

            microphone.connect(analyser);
            analyser.connect(processor);
            processor.connect(audioContext.destination);

            processor.onaudioprocess = function(e) {
                const inputData = e.inputBuffer.getChannelData(0);
                if (inputData.some(sample => Math.abs(sample) > 0.01)) {
                    recordedChunks.push(Array.from(inputData));
                }
            };

        } catch (error) {
            console.error('AudioContext hatası:', error);
            stopRecording();
        }
    }

    function stopRecording() {
        isRecording = false;
        recordButton.classList.remove('recording');
        recordButton.textContent = 'Kayda Başla';
        detectNoteButton.disabled = false;
        detectChordButton.disabled = false;
        statusDisplay.textContent = 'Kayıt tamamlandı. Nota veya akor tespiti için butona tıklayın.';

        if (processor) {
            processor.disconnect();
            processor = null;
        }
        if (microphone) {
            microphone.disconnect();
            microphone = null;
        }
        if (analyser) {
            analyser.disconnect();
            analyser = null;
        }
        if (audioContext) {
            audioContext.close();
            audioContext = null;
        }
    }

    function getRoleClass(index) {
        const classes = ['chord-root', 'chord-third', 'chord-fifth', 'chord-seventh'];
        return classes[index] || '';
    }

    function clearKeyHighlights() {
        document.querySelectorAll('.piano-key').forEach(key => {
            key.classList.remove('active');
            key.style.backgroundColor = '';
            key.style.opacity = '';
            const activeNote = key.querySelector('.active-note-display');
            if (activeNote) {
                activeNote.textContent = '';
                activeNote.style.opacity = '0';
                activeNote.style.backgroundColor = '';
                activeNote.style.color = '';
            }
        });
    }

    function getChordNoteColor(index) {
        const colors = [
            CHORD_COLORS.root,    // Kök nota
            CHORD_COLORS.third,   // 3'lü
            CHORD_COLORS.fifth,   // 5'li
            CHORD_COLORS.seventh  // 7'li
        ];
        return colors[index] || colors[0];
    }

    function highlightKey(key, color = null, noteText = null) {
        key.classList.add('active');
        
        // Aktif nota gösterimini güncelle
        const activeNote = key.querySelector('.active-note-display');
        if (activeNote && noteText) {
            activeNote.textContent = noteText;
            activeNote.style.opacity = '1';
            if (color) {
                activeNote.style.backgroundColor = color.bg;
                activeNote.style.color = color.text;
            }
        }

        if (color) {
            const isBlackKey = key.classList.contains('black-key');
            key.style.backgroundColor = color.bg;
            key.style.opacity = isBlackKey ? '0.9' : '0.7';
        }
    }

    async function sendAudioToServer(audioData) {
        try {
            const response = await fetch('/api/detect-note', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ audio: audioData })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            if (data.error) {
                console.error('Sunucu hatası:', data.error);
                statusDisplay.textContent = 'Tespit edilemedi';
                return null;
            }
            return data;
        } catch (error) {
            console.error('API hatası:', error);
            statusDisplay.textContent = 'Sunucu bağlantı hatası';
            return null;
        }
    }
}); 