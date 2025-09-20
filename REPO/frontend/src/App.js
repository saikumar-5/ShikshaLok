import React, { useState, useRef, useEffect } from 'react';
import Recorder from 'recorder-js';
import WavEncoder from 'wav-encoder';

// Language options - Sarvam API supported languages
const LANGUAGE_OPTIONS = [
  { code: 'en-IN', label: 'English' },
  { code: 'hi-IN', label: 'Hindi (हिन्दी)' },
  { code: 'bn-IN', label: 'Bengali (বাংলা)' },
  { code: 'te-IN', label: 'Telugu (తెలుగు)' },
  { code: 'mr-IN', label: 'Marathi (मराठी)' },
  { code: 'ta-IN', label: 'Tamil (தமிழ்)' },
  { code: 'gu-IN', label: 'Gujarati (ગુજરાતી)' },
  { code: 'kn-IN', label: 'Kannada (ಕನ್ನಡ)' },
  { code: 'ml-IN', label: 'Malayalam (മലയാളം)' },
  { code: 'or-IN', label: 'Odia (ଓଡ଼ିଆ)' },
  { code: 'pa-IN', label: 'Punjabi (ਪੰਜਾਬੀ)' }
];

const INPUT_SOURCES = [
  { value: 'microphone', label: 'Microphone' },
  { value: 'file', label: 'Upload File' },
  { value: 'document', label: 'Upload Document' },
  { value: 'text', label: 'Text Input' },
];

function Header() {
  return (
    <div className="header">
      <div className="header-content">
        <div className="logo-section">
          <div className="app-logo">
            <img src="./siksha logo.jpg" alt="Shiksha Logo" />
          </div>
          <div className="app-info">
            <h1>Shiksha Lok</h1>
            <span className="tagline">AI-Powered Multilingual Content Localization Engine</span>
          </div>
        </div>
        <div className="header-logo">
          <img src="./WhatsApp_msde.jpg" alt="MSDE Logo" />
        </div>
      </div>
    </div>
  );
}

function LanguageSelector({ label, value, onChange, options }) {
  return (
    <div className="lang-selector">
      <label>{label}</label>
      <select value={value} onChange={onChange}>
        {options.map(opt => (
          <option key={opt.code} value={opt.code}>{opt.label}</option>
        ))}
      </select>
    </div>
  );
}

function InputPanel({
  inputSource, setInputSource,
  inputLang, setInputLang,
  outputLang, setOutputLang,
  languageOptions,
  file, handleFileChange,
  documentFile, handleDocumentChange,
  micStatus, handleMicRecord,
  onClear,
  isRecording,
  autoPlayEnabled,
  setAutoPlayEnabled,
  stopAutoPlay,
  videoUrl,
  setVideoUrl,
  isProcessingVideo,
  handleProcessVideoUrl,
  useLocalization,
  setUseLocalization,
}) {
  return (
    <div className="input-panel">
      <div className="input-source-section">
        <h3>Select Input Source</h3>
        <div className="radio-group">
          {INPUT_SOURCES.map(opt => (
            <label key={opt.value} className="radio-option">
              <input
                type="radio"
                name="inputSource"
                value={opt.value}
                checked={inputSource === opt.value}
                onChange={e => setInputSource(e.target.value)}
              />
              <span>{opt.label}</span>
            </label>
          ))}
        </div>
      </div>

      {inputSource === 'file' && (
        <div className="file-upload-section">
          <label className="upload-area">
            <div className="upload-icon">🎵</div>
            <div className="upload-text">
              <strong>Drop Audio/Video File</strong>
              <span>- or -</span>
              <span>Click to Browse</span>
            </div>
            <input type="file" accept="audio/*,video/*" onChange={handleFileChange} />
            {file && <div className="file-selected">✅ {file.name}</div>}
          </label>

          <div style={{ marginTop: 12, display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
            <input
              type="text"
              placeholder="Paste video URL (YouTube, etc.)"
              value={videoUrl}
              onChange={e => setVideoUrl(e.target.value)}
              style={{ flex: 1, minWidth: 240, padding: '10px 12px', border: '1.5px solid #d1d5db', borderRadius: 8 }}
            />
            <button
              onClick={handleProcessVideoUrl}
              disabled={!videoUrl || isProcessingVideo}
              className="clear-btn"
              style={{ width: 'auto', padding: '10px 16px' }}
              title="Download and translate video audio"
            >
              {isProcessingVideo ? 'Processing…' : 'Translate Video URL'}
            </button>
          </div>
          <div style={{ marginTop: 6, color: '#6b7280', fontSize: 12 }}>
            Paste a YouTube or public video link (max 5 minutes). The audio will be transcribed, translated, and muxed back into the video.
            <br /><strong>Note:</strong> Processing may take 2-5 minutes depending on video length.
          </div>
        </div>
      )}

      {inputSource === 'document' && (
        <div className="document-upload-section">
          <label className="upload-area">
            <div className="upload-icon">📄</div>
            <div className="upload-text">
              <strong>Drop Document File</strong>
              <span>- or -</span>
              <span>Click to Browse</span>
            </div>
            <input 
              type="file" 
              accept=".pdf,.docx,.txt,.png,.jpg,.jpeg,.gif,.bmp,.tiff" 
              onChange={handleDocumentChange} 
            />
            {documentFile && <div className="file-selected">✅ {documentFile.name}</div>}
          </label>
          <div className="supported-formats">
            <small>Supported: PDF, DOCX, TXT, Images (PNG, JPG, JPEG)</small>
          </div>
        </div>
      )}

      {inputSource === 'microphone' && (
        <div className="microphone-section">
          <div className="mic-controls" style={{ justifyContent: 'center', gap: 16 }}>
            <button
              className={`record-btn ${micStatus === 'recording' ? 'recording' : ''}`}
              onClick={() => {
                if (!isRecording) {
                  console.log('Microphone Start');
                } else {
                  console.log('Microphone Stop');
                }
                handleMicRecord();
              }}
              style={{ margin: '0', display: 'inline-block' }}
            >
              <span className="record-dot"></span>
              {micStatus === 'recording' ? 'Stop' : 'Start'}
            </button>
          </div>
          {micStatus === 'recording' && (
            <div className="waveform-visualization">
              <div className="wave-bar"></div>
              <div className="wave-bar"></div>
              <div className="wave-bar"></div>
              <div className="wave-bar"></div>
              <div className="wave-bar"></div>
            </div>
          )}
        </div>
      )}

      <div className="language-selectors">
        <LanguageSelector
          label="Input Language"
          value={inputLang}
          onChange={e => setInputLang(e.target.value)}
          options={languageOptions}
        />
        <LanguageSelector
          label="Output Language"
          value={outputLang}
          onChange={e => setOutputLang(e.target.value)}
          options={languageOptions}
        />
      </div>

      <div className="localization-section">
        <label className="localization-toggle">
          <input 
            type="checkbox" 
            checked={useLocalization} 
            onChange={(e) => {
              const newValue = e.target.checked;
              console.log('🔄 Localization toggle changed:', newValue);
              setUseLocalization(newValue);
            }}
          />
          <span className="toggle-slider"></span>
          <span className="toggle-label">
            Best Localization
          </span>
        </label>

      </div>

      {inputSource === 'microphone' && (
        <div className="auto-play-section">
          <label className="auto-play-toggle">
            <input
              type="checkbox"
              checked={autoPlayEnabled}
              onChange={e => {
                const enabled = e.target.checked;
                setAutoPlayEnabled(enabled);
                if (!enabled) {
                  stopAutoPlay();
                }
              }}
            />
            <span className="toggle-slider"></span>
            <span className="toggle-label">Auto-Play Translated Speech</span>
          </label>
          {autoPlayEnabled && (
            <div className="auto-play-info">
              <span>🎵 Real-time audio playback enabled</span>
            </div>
          )}
        </div>
      )}

      <button className="clear-btn" onClick={onClear}>
        🗑️ Clear All
      </button>
    </div>
  );
}

function Footer() {
  return (
    <div className="footer">
      <div className="footer-content">
        <span className="footer-text">🚀 Smart India Hackathon 2024 | Problem Statement #1525</span>
        <div className="tech-stack">
          <span>⚡ React</span>
          <span>🤖 AI/ML</span>
          <span>🎤 Speech API</span>
        </div>
      </div>
    </div>
  );
}

function App() {
  const [inputSource, setInputSource] = useState('text');
  const [inputLang, setInputLang] = useState('en-IN');
  const [outputLang, setOutputLang] = useState('te-IN');
  const [useLocalization, setUseLocalization] = useState(false);
  const [originalText, setOriginalText] = useState('');
  const [translatedText, setTranslatedText] = useState('');
  const [history, setHistory] = useState([]);
  const [isTranslating, setIsTranslating] = useState(false);
  const [isPlayingOriginal, setIsPlayingOriginal] = useState(false);
  const [isPlayingTranslated, setIsPlayingTranslated] = useState(false);
  const [file, setFile] = useState(null);
  const [documentFile, setDocumentFile] = useState(null);
  const [isProcessingDocument, setIsProcessingDocument] = useState(false);
  const [translatedDocumentUrl, setTranslatedDocumentUrl] = useState(null);
  const [videoUrl, setVideoUrl] = useState('');
  const [isProcessingVideo, setIsProcessingVideo] = useState(false);
  const [dubbedVideoUrl, setDubbedVideoUrl] = useState(null);
  const [micStatus, setMicStatus] = useState('idle');
  const debounceRef = useRef(null);
  const [isRecording, setIsRecording] = useState(false);
  const sampleRate = 16000;
  const audioContextRef = useRef(null);
  const processorRef = useRef(null);
  const sourceRef = useRef(null);
  const bufferRef = useRef([]);
  const originalTextRef = useRef('');
  const translatedTextRef = useRef('');
  const audioRef = useRef(null);
  const lastAudioKeyRef = useRef(null);
  const [currentChunkText, setCurrentChunkText] = useState('');
  const [currentChunkTranslation, setCurrentChunkTranslation] = useState('');
  const [theme, setTheme] = useState('light');
  const isRecordingRef = useRef(false);
  // Add auto-play state and audio queue
  const [autoPlayEnabled, setAutoPlayEnabled] = useState(false);
  const audioQueueRef = useRef([]);
  const isPlayingQueueRef = useRef(false);
  const currentAudioRef = useRef(null);
  const [queueStatus, setQueueStatus] = useState({ count: 0, isPlaying: false });
  // Dynamic labels for left and right columns
  const getLeftLabel = () => {
    switch (inputSource) {
      case 'file': return 'File Input';
      case 'document': return 'Document Input';
      case 'microphone': return 'Speech Input';
      case 'text': return 'Text Input';
      default: return 'Original Text';
    }
  };

  const getRightLabel = () => {
    switch (inputSource) {
      case 'file': return 'File Translation';
      case 'document': return 'Document Translation';
      case 'microphone': return 'Speech Translation';
      case 'text': return 'Text Translation';
      default: return 'Translated Text';
    }
  };

  // Auto-play queue management functions
  const addToAudioQueue = async (text, lang) => {
    if (!text || !text.trim()) return;
    
    try {
      const response = await fetch('http://localhost:8000/api/text-to-speech', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: text,
          language_code: lang,
          gender: 'male',
          sampling_rate: 22050
        })
      });
      
      if (!response.ok) {
        console.error('TTS API error:', response.status);
        return;
      }
      
      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      
      audioQueueRef.current.push({
        url: audioUrl,
        text: text,
        lang: lang
      });
      
      // Update queue status
      setQueueStatus({
        count: audioQueueRef.current.length,
        isPlaying: isPlayingQueueRef.current
      });
      
      // Start playing if not already playing
      if (!isPlayingQueueRef.current) {
        playNextInQueue();
      }
    } catch (error) {
      console.error('Error adding to audio queue:', error);
    }
  };

  const playNextInQueue = async () => {
    if (audioQueueRef.current.length === 0) {
      isPlayingQueueRef.current = false;
      setQueueStatus({ count: 0, isPlaying: false });
      return;
    }
    
    isPlayingQueueRef.current = true;
    setQueueStatus({
      count: audioQueueRef.current.length,
      isPlaying: true
    });
    const audioItem = audioQueueRef.current.shift();
    
    try {
      const audio = new Audio(audioItem.url);
      currentAudioRef.current = audio;
      
      audio.onended = () => {
        // Clean up the URL
        URL.revokeObjectURL(audioItem.url);
        currentAudioRef.current = null;
        // Update status before playing next
        setQueueStatus(prev => ({
          count: audioQueueRef.current.length,
          isPlaying: false
        }));
        // Play next item in queue
        playNextInQueue();
      };
      
      audio.onerror = (error) => {
        console.error('Audio playback error:', error);
        URL.revokeObjectURL(audioItem.url);
        currentAudioRef.current = null;
        // Continue with next item
        playNextInQueue();
      };
      
      await audio.play();
    } catch (error) {
      console.error('Error playing audio from queue:', error);
      URL.revokeObjectURL(audioItem.url);
      currentAudioRef.current = null;
      // Continue with next item
      playNextInQueue();
    }
  };

  const stopAutoPlay = () => {
    // Stop current audio
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current.currentTime = 0;
      currentAudioRef.current = null;
    }
    
    // Clear queue and revoke URLs
    audioQueueRef.current.forEach(item => {
      URL.revokeObjectURL(item.url);
    });
    audioQueueRef.current = [];
    isPlayingQueueRef.current = false;
    setQueueStatus({ count: 0, isPlaying: false });
  };

  // Add useEffect to reset refs and state on inputSource change
  useEffect(() => {
    setOriginalText('');
    setTranslatedText('');
    originalTextRef.current = '';
    translatedTextRef.current = '';
    setTranslatedDocumentUrl(null);
    
    // Video URL related cleanup
    if (dubbedVideoUrl) { 
      try { URL.revokeObjectURL(dubbedVideoUrl); } catch (e) {} 
    }
    setDubbedVideoUrl(null);
    setVideoUrl('');
    setIsProcessingVideo(false);
    
    // Disable auto-play when switching away from microphone
    if (inputSource !== 'microphone' && autoPlayEnabled) {
      setAutoPlayEnabled(false);
      stopAutoPlay();
    }
  }, [inputSource, autoPlayEnabled]);

  useEffect(() => {
    isRecordingRef.current = isRecording;
}, [isRecording]);

  const handleOriginalTextChange = (e) => {
    const value = e.target.value;
    setOriginalText(value);
    setIsTranslating(true);
    setTranslatedText('');
    
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      if (value.trim() !== '') {
        // For text input, do not use refs, just update state
        translateText(value, inputLang, outputLang);
      } else {
        setTranslatedText('');
        setIsTranslating(false);
      }
    }, 1500);
  };

  // Replace translateText with real API call
  const translateText = async (text, sourceLang, targetLang, append = false, returnOnly = false) => {
    console.log('Calling /api/translate', { text, sourceLang, targetLang, append, returnOnly });
    setIsTranslating(true);
    if (!append) setTranslatedText('');

    // Start timing
    const start = performance.now();

    try {
      const response = await fetch('http://localhost:8000/api/translate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          input: text,
          source_language_code: sourceLang,
          target_language_code: targetLang,
          speaker_gender: 'Male',
          mode: 'formal',
          model: 'mayura:v1',
          enable_preprocessing: true,
          use_localization: useLocalization,
          use_text_preprocessing: true
        })
      });
      const data = await response.json();
      setIsTranslating(false);

      // End timing
      const end = performance.now();
      console.log('Text translation latency:', (end - start).toFixed(2), 'ms');

      if (returnOnly) return data.translated_text || '';
      if (append) {
        setTranslatedText(prev => (prev ? prev + ' ' + (data.translated_text || '') : (data.translated_text || '')));
      } else {
        setTranslatedText(data.translated_text || '');
      }
      setHistory(prev => [
        {
          original: text,
          translated: data.translated_text,
          inputLang: sourceLang,
          outputLang: targetLang,
          timestamp: new Date().toLocaleTimeString()
        },
        ...prev.slice(0, 9)
      ]);
    } catch (err) {
      setTranslatedText('Translation failed');
      setIsTranslating(false);
      if (returnOnly) return '';
    }
  };


class AudioBuffer {
  constructor(minDurationSec = 2.0, sampleRate = 16000) {
    this.minDurationSec = minDurationSec;
    this.sampleRate = sampleRate;
    this.buffer = [];
    this.lastSentTime = null;
  }

  addChunk(audioData) {
    this.buffer.push(audioData);
  }

  shouldSend() {
    const totalSamples = this.buffer.reduce((sum, chunk) => sum + chunk.length, 0);
    const duration = totalSamples / this.sampleRate;
    return duration >= this.minDurationSec;
  }

  getAudioData() {
    if (this.buffer.length === 0) return null;
    
    // Concatenate all buffered audio
    const totalLength = this.buffer.reduce((sum, chunk) => sum + chunk.length, 0);
    const combined = new Float32Array(totalLength);
    let offset = 0;
    
    for (const chunk of this.buffer) {
      combined.set(chunk, offset);
      offset += chunk.length;
    }
    
    return combined;
  }

  clear() {
    this.buffer = [];
  }
}

  // Add speechToText for microphone/file
const speechToText = async (audioBlob, languageCode) => {
  console.log('=== SPEECH TO TEXT DEBUG START ===');
  console.log('Function called with:', {
    audioBlob: audioBlob,
    audioBlobType: audioBlob?.type,
    audioBlobSize: audioBlob?.size,
    languageCode: languageCode
  });
  
  // Validate inputs
  if (!audioBlob) {
    console.error('No audio blob provided');
    return '';
  }
  
  if (!languageCode) {
    console.error('No language code provided');
    return '';
  }
  
  try {
    // Create FormData
    const formData = new FormData();
    
    // Create a proper audio file with correct MIME type
    const audioFile = new File([audioBlob], 'audio.wav', { 
      type: 'audio/wav',
      lastModified: Date.now()
    });
    
    formData.append('file', audioFile);
    formData.append('language_code', languageCode === 'auto' ? '' : languageCode);
    
    // Log FormData contents
    console.log('FormData created with:');
    for (let [key, value] of formData.entries()) {
      console.log(`${key}:`, value);
    }
    
    const url = 'http://localhost:8000/api/speech-to-text';
    console.log('Making request to:', url);
    console.log('Request method: POST');
    
    // Make the fetch request with explicit configuration
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
      // DO NOT set Content-Type header - let browser handle it for FormData
      mode: 'cors',
      credentials: 'same-origin'
    });
    
    console.log('Response received:');
    console.log('Status:', response.status);
    console.log('Status Text:', response.statusText);
    console.log('OK:', response.ok);
    console.log('Headers:', Object.fromEntries(response.headers.entries()));
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Error response body:', errorText);
      console.log('=== SPEECH TO TEXT DEBUG END (ERROR) ===');
      throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`);
    }
    
    const data = await response.json();
    console.log('Success response data:', data);
    console.log('=== SPEECH TO TEXT DEBUG END (SUCCESS) ===');
    
    return data.transcript || '';
    
  } catch (error) {
    console.error('=== SPEECH TO TEXT ERROR ===');
    console.error('Error type:', error.constructor.name);
    console.error('Error message:', error.message);
    console.error('Error stack:', error.stack);
    console.log('=== SPEECH TO TEXT DEBUG END (CATCH) ===');
    return '';
  }
};


  // Replace playAudio with real TTS API call
  const playAudio = async (text, lang, setPlaying) => {
    const audioKey = text + '|' + lang;
    console.log('Calling /api/text-to-speech', { text, lang });

    // If the same audio is already playing, stop it and return (toggle behavior)
    if (audioRef.current && lastAudioKeyRef.current === audioKey && !audioRef.current.paused) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
      setPlaying(false);
      lastAudioKeyRef.current = null;
      return;
    }

    setPlaying(true);

    // Stop any currently playing audio
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
      setPlaying(false);
    }

    // Helper: Split text into sentences or 250-char chunks
    function splitText(text) {
      // Try to split by sentence first
      let sentences = text.match(/[^.!?\n]+[.!?\n]+|[^.!?\n]+$/g);
      if (!sentences) return [text];
      let chunks = [];
      let current = '';
      for (let s of sentences) {
        if ((current + s).length > 250) {
          if (current) chunks.push(current.trim());
          current = s;
        } else {
          current += s;
        }
      }
      if (current) chunks.push(current.trim());
      return chunks;
    }

    const chunks = splitText(text);
    let stopped = false;

    for (let i = 0; i < chunks.length; i++) {
      if (stopped) break;
      const chunk = chunks[i];
      try {
        const response = await fetch('http://localhost:8000/api/text-to-speech', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text: chunk,
            language_code: lang,
            gender: 'male',
            sampling_rate: 22050
          })
        });
        const contentType = response.headers.get('content-type') || '';
        if (!response.ok || !contentType.includes('audio')) {
          const errorText = await response.text();
          console.error('TTS error:', errorText);
          setPlaying(false);
          lastAudioKeyRef.current = null;
          return;
        }
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new window.Audio(audioUrl);
        audioRef.current = audio;
        lastAudioKeyRef.current = audioKey;
        await new Promise((resolve, reject) => {
          audio.onended = resolve;
          audio.onerror = reject;
          audio.play();
        });
      } catch (err) {
        setPlaying(false);
        audioRef.current = null;
        lastAudioKeyRef.current = null;
        console.error('TTS play error:', err);
        return;
      }
    }
    setPlaying(false);
    audioRef.current = null;
    lastAudioKeyRef.current = null;
  };

  // Update handleFileChange to use speechToText then translateText
  const handleFileChange = async (e) => {
    const selectedFile = e.target.files[0];
    setFile(selectedFile);
    if (selectedFile) {
      setOriginalText(`File selected: ${selectedFile.name}`);
      // Convert file to audio blob and send to backend
      const transcript = await speechToText(selectedFile, inputLang);
      setOriginalText(transcript);
      // For file input, do not use refs, just update state
      translateText(transcript, inputLang, outputLang);
    }
  };

  // Handle document upload and processing
  const handleDocumentChange = async (e) => {
    const selectedFile = e.target.files[0];
    setDocumentFile(selectedFile);
    
    if (selectedFile) {
      setIsProcessingDocument(true);
      setOriginalText(`Processing document: ${selectedFile.name}...`);
      setTranslatedText('');
      setTranslatedDocumentUrl(null);
      
      try {
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('source_language_code', inputLang);
        formData.append('target_language_code', outputLang);
        formData.append('use_localization', useLocalization);
        
        const response = await fetch('http://localhost:8000/api/document-translate', {
          method: 'POST',
          body: formData,
        });
        
        if (response.ok) {
          // Get the translated document
          const blob = await response.blob();
          
          // Extract filename from response headers or create one
          const contentDisposition = response.headers.get('content-disposition');
          let filename = 'translated_document.txt';
          if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="(.+)"/);
            if (filenameMatch) {
              filename = filenameMatch[1];
            }
          } else {
            // Create filename based on original file and format
            const originalExt = selectedFile.name.split('.').pop().toLowerCase();
            const baseName = selectedFile.name.replace(/\.[^/.]+$/, "");
            if (originalExt === 'pdf' || originalExt === 'docx') {
              filename = `translated_${baseName}.${originalExt}`;
            } else {
              filename = `translated_${baseName}.txt`;
            }
          }
          
          // Remove automatic download - just store for manual download
          
          // Store document for download button and get text content
          const docUrl = URL.createObjectURL(blob);
          setTranslatedDocumentUrl({ url: docUrl, filename });
          
          // Get actual text content for display
          try {
            const extractFormData = new FormData();
            extractFormData.append('file', selectedFile);
            extractFormData.append('source_language_code', inputLang);
            extractFormData.append('target_language_code', outputLang);
            extractFormData.append('use_localization', useLocalization);
            
            const textResponse = await fetch('http://localhost:8000/api/document-extract', {
              method: 'POST',
              body: extractFormData,
            });
            
            if (textResponse.ok) {
              const textData = await textResponse.json();
              setOriginalText(textData.extracted_text || `Document processed: ${selectedFile.name}`);
              setTranslatedText(textData.translated_text || `Translation completed! Click download button below.`);
            } else {
              setOriginalText(`Document processed successfully: ${selectedFile.name}`);
              setTranslatedText(`Translation completed! Click download button below.`);
            }
          } catch (error) {
            console.error('Error getting text content:', error);
            setOriginalText(`Document processed successfully: ${selectedFile.name}`);
            setTranslatedText(`Translation completed! Click download button below.`);
          }
          
          // Add to history
          setHistory(prev => [
            {
              original: `Document: ${selectedFile.name}`,
              translated: `Translated document: ${filename}`,
              inputLang: inputLang,
              outputLang: outputLang,
              timestamp: new Date().toLocaleTimeString()
            },
            ...prev.slice(0, 9)
          ]);
        } else {
          const errorData = await response.json();
          setOriginalText(`Error processing document: ${errorData.error || 'Unknown error'}`);
          setTranslatedText('');
        }
      } catch (error) {
        console.error('Document processing error:', error);
        setOriginalText(`Error processing document: ${error.message}`);
        setTranslatedText('');
      } finally {
        setIsProcessingDocument(false);
      }
    }
  };

  // Real-time mic streaming logic
const handleMicRecord = async () => {
 console.log('=== MICROPHONE HANDLER START ===');
 console.log('Current recording state (before toggle):', isRecording); // Log before changing
 // Toggle the recording state immediately
 const willBeRecording = !isRecording;
 setIsRecording(willBeRecording);
 setMicStatus(willBeRecording ? 'recording' : 'idle');
 
  if (willBeRecording) { // Logic for starting recording
    console.log('Starting recording...');
    
    try {
      // Reset states when starting a new recording
      originalTextRef.current = '';
      translatedTextRef.current = '';
      setOriginalText('');
      setTranslatedText('');
      setCurrentChunkText('');
      setCurrentChunkTranslation('');
      bufferRef.current = [];
      
      console.log('Requesting microphone access...');
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          sampleRate: sampleRate,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true
        }
      });
      
      console.log('Microphone access granted');
      console.log('Creating audio context...');
      
      const audioContext = new (window.AudioContext || window.webkitAudioContext)({ 
        sampleRate: sampleRate 
      });
      audioContextRef.current = audioContext;
      
      console.log('Audio context created, sample rate:', audioContext.sampleRate);
      
      const source = audioContext.createMediaStreamSource(stream);
      sourceRef.current = source;
      
      const processor = audioContext.createScriptProcessor(8192, 1, 1);
      processorRef.current = processor;
      
      console.log('Audio processor created');
      
      processor.onaudioprocess = (e) => {
        // Use the ref here, as its value is always current
        if (!isRecordingRef.current) { // <-- Use a ref for isRecording here
          console.log('Recording stopped (via ref), ignoring audio data');
          return;
        }
        
        const input = e.inputBuffer.getChannelData(0);
        bufferRef.current.push(...input);
        
        const targetSamples = sampleRate * 3; // 3 seconds
        
        if (bufferRef.current.length >= targetSamples) {
          console.log('Buffer full, processing chunk...');
          const chunk = bufferRef.current.slice(0, targetSamples);
          bufferRef.current = bufferRef.current.slice(targetSamples);
          
          setTimeout(() => {
            encodeAndSendChunk(chunk);
          }, 0);
        }
      };
      
      source.connect(processor);
      processor.connect(audioContext.destination);
      
      console.log('Audio pipeline connected, recording started');
      
    } catch (error) {
      console.error('Error starting recording:', error);
      setIsRecording(false); // Ensure state is reset on error
      setMicStatus('idle');
    }
    
    } else { // Logic for stopping recording
    console.log('Stopping recording...');
    // No need to setMicStatus or setIsRecording here, as it's set at the top
    
    // Stop auto-play when stopping recording
    stopAutoPlay();
    
    // Clean up
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
      console.log('Processor disconnected');
    }
    
    if (sourceRef.current) {
      sourceRef.current.disconnect();
      // Also stop the media stream tracks
      sourceRef.current.mediaStream.getTracks().forEach(track => track.stop());
      sourceRef.current = null;
      console.log('Source disconnected and tracks stopped');
    }
    
    if (audioContextRef.current) {
      // Process any remaining audio
      if (bufferRef.current && bufferRef.current.length > 0) {
        console.log('Processing remaining buffer:', bufferRef.current.length, 'samples');
        encodeAndSendChunk(bufferRef.current); // Process final chunk
        bufferRef.current = [];
      }
      
      audioContextRef.current.close();
      audioContextRef.current = null;
      console.log('Audio context closed');
    }
  }
  
  console.log('=== MICROPHONE HANDLER END ===');
};

const testEndpoint = async () => {
  console.log('=== TESTING ENDPOINT ===');
  
  try {
    const response = await fetch('http://localhost:8000/api/speech-to-text', {
      method: 'OPTIONS' // Test if the endpoint exists
    });
    
    console.log('OPTIONS response:', response.status, response.statusText);
    console.log('Allowed methods:', response.headers.get('Allow'));
    
  } catch (error) {
    console.error('Endpoint test failed:', error);
  }
};

const processAudioChunk = async (audioData) => {
  try {
    console.log('processAudioChunk called with', audioData.length, 'samples');
    
    // Convert Float32Array to WAV format
    const wavBuffer = await WavEncoder.encode({
      sampleRate: sampleRate,
      channelData: [audioData],
    });
    
    const blob = new Blob([wavBuffer], { type: 'audio/wav' });
    console.log('Created WAV blob:', {
      size: blob.size,
      type: blob.type
    });
    
    // Call speech-to-text
    const transcript = await speechToText(blob, inputLang);
    console.log('Transcript received:', transcript);
    
    setCurrentChunkText(transcript || '');
    
    if (transcript && transcript.trim()) {
      // Append to original text
      const newOriginalText = originalTextRef.current ? 
        originalTextRef.current + ' ' + transcript : transcript;
      originalTextRef.current = newOriginalText;
      setOriginalText(newOriginalText);
      
      // Translate the chunk
      try {
        const translation = await translateText(transcript, inputLang, outputLang, false, true);
        console.log('Translation received:', translation);
        
        setCurrentChunkTranslation(translation || '');
        
        if (translation && translation.trim()) {
          // Append to translated text
          const newTranslatedText = translatedTextRef.current ? 
            translatedTextRef.current + ' ' + translation : translation;
          translatedTextRef.current = newTranslatedText;
          setTranslatedText(newTranslatedText);

          // Auto play TTS if enabled
          if (false) { // Removed autoPlay
            try {
              const ttsResponse = await fetch('http://localhost:8000/api/text-to-speech', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  text: translation,
                  lang: outputLang,
                }),
              });
              console.log('TTS response status:', ttsResponse.status);
              console.log('TTS response content-type:', ttsResponse.headers.get('content-type'));
              if (ttsResponse.ok) {
                // Try to preview the response as text (for debugging)
                const contentType = ttsResponse.headers.get('content-type');
                if (contentType && contentType.includes('audio')) {
                  const audioBlob = await ttsResponse.blob();
                  const audioUrl = URL.createObjectURL(audioBlob);
                  const audio = new Audio(audioUrl);
                  audio.play();
                  console.log('Playing audio from TTS response.');
                } else {
                  const text = await ttsResponse.text();
                  console.warn('TTS response is not audio. Response text:', text);
                }
              } else {
                const text = await ttsResponse.text();
                console.error('TTS response error:', text);
              }
            } catch (e) {
              console.error('Auto play TTS error:', e);
            }
          }
        }
      } catch (translateError) {
        console.error('Translation error:', translateError);
        setCurrentChunkTranslation('Translation failed');
      }
    } else {
      setCurrentChunkTranslation('');
    }
    
  } catch (error) {
    console.error('Error in processAudioChunk:', error);
    setCurrentChunkText('Processing error');
    setCurrentChunkTranslation('');
  }
};

  // In encodeAndSendChunk, only use refs for mic streaming
  const encodeAndSendChunk = async (pcm) => {
  console.log('=== ENCODE AND SEND CHUNK START ===');
  console.log('PCM data length:', pcm.length);
  
  // Start timing
  const start = performance.now();

  try {
    // Validate PCM data
    if (!pcm || pcm.length === 0) {
      console.warn('Empty PCM data, skipping...');
      return;
    }
    
    console.log('Encoding WAV...');
    const wavBuffer = await WavEncoder.encode({
      sampleRate: sampleRate,
      channelData: [new Float32Array(pcm)],
    });

    // Create a Blob and wrap as File for FormData
    const blob = new Blob([wavBuffer], { type: 'audio/wav' });
    const audioFile = new File([blob], 'audio.wav', { type: 'audio/wav' });

    // Debug: Download the WAV file being sent
    // const url = URL.createObjectURL(blob);
    // const a = document.createElement('a');
    // a.style.display = 'none';
    // a.href = url;
    // a.download = 'debug_chunk.wav';
    // document.body.appendChild(a);
    // a.click();
    // setTimeout(() => {
    //   document.body.removeChild(a);
    //   URL.revokeObjectURL(url);
    // }, 100);

    // Send as multipart/form-data POST (like file upload)
    const formData = new FormData();
    formData.append('file', audioFile);
    formData.append('language_code', inputLang);

    console.log('Calling speechToText (as file upload)...');
    const response = await fetch('http://localhost:8000/api/speech-to-text', {
      method: 'POST',
      body: formData,
    });
    const data = await response.json();
    const transcript = data.transcript || '';
    console.log('Transcript received:', transcript);

    setCurrentChunkText(transcript || '');

    if (transcript && transcript.trim()) {
      // Update original text
      const newOriginalText = originalTextRef.current ? 
        originalTextRef.current + ' ' + transcript : transcript;
      originalTextRef.current = newOriginalText;
      setOriginalText(newOriginalText);

      console.log('Calling translateText...');
      // Translate the transcript
      const translation = await translateText(transcript, inputLang, outputLang, true, true);
      console.log('Translation received:', translation);

      setCurrentChunkTranslation(translation || '');

      if (translation && translation.trim()) {
        const newTranslatedText = translatedTextRef.current ? 
          translatedTextRef.current + ' ' + translation : translation;
        translatedTextRef.current = newTranslatedText;
        setTranslatedText(newTranslatedText);

        // Add to auto-play queue if enabled and using microphone
        if (autoPlayEnabled && inputSource === 'microphone') {
          addToAudioQueue(translation, outputLang);
        }
      }
    } else {
      setCurrentChunkTranslation('');
      console.log('No transcript received');
    }

    // End timing
    const end = performance.now();
    console.log('Speech-to-translation latency:', (end - start).toFixed(2), 'ms');

    console.log('=== ENCODE AND SEND CHUNK END (SUCCESS) ===');
    
  } catch (err) {
    console.error('=== ENCODE AND SEND CHUNK ERROR ===');
    console.error('Error:', err);
    setCurrentChunkText('Processing error: ' + err.message);
    setCurrentChunkTranslation('');
    console.log('=== ENCODE AND SEND CHUNK END (ERROR) ===');
  }
};

  // Function to decode HTML entities
  const decodeHtmlEntities = (text) => {
    const textarea = document.createElement('textarea');
    textarea.innerHTML = text;
    return textarea.value;
  };

  // Download translated text function
  const downloadTranslatedText = (text, sourceLang, targetLang) => {
    if (!text || !text.trim()) return;
    
    // Decode HTML entities in the text
    const decodedText = decodeHtmlEntities(text);
    const decodedOriginalText = decodeHtmlEntities(originalText);
    
    const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
    const sourceLabel = LANGUAGE_OPTIONS.find(lang => lang.code === sourceLang)?.label || sourceLang;
    const targetLabel = LANGUAGE_OPTIONS.find(lang => lang.code === targetLang)?.label || targetLang;
    const filename = `translation_${sourceLabel}_to_${targetLabel}_${timestamp}.txt`;
    
    const content = `Translation Report
==================

Source Language: ${sourceLabel} (${sourceLang})
Target Language: ${targetLabel} (${targetLang})
Timestamp: ${new Date().toLocaleString()}

--- Original Text ---
${decodedOriginalText}

--- Translated Text ---
${decodedText}

--- Generated by Shiksha Lok ---
AI-Powered Multilingual Content Localization Engine`;
    
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    
    const downloadLink = document.createElement('a');
    downloadLink.href = url;
    downloadLink.download = filename;
    downloadLink.style.display = 'none';
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
    
    // Clean up the URL after a short delay
    setTimeout(() => {
      URL.revokeObjectURL(url);
    }, 1000);
  };

  // Format document text with proper styling
  const formatDocumentText = (text) => {
    if (!text) return 'Document content will appear here...';
    
    // Decode HTML entities first
    const decodedText = decodeHtmlEntities(text);
    
    // Clean up the text - remove extra spaces and fix formatting
    const cleanedText = decodedText
      .replace(/&amp;/g, '&')
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'")
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/\s+/g, ' ')
      .trim();
    
    // Split into paragraphs and format
    const paragraphs = cleanedText.split(/\n\s*\n/);
    const formattedParagraphs = [];
    
    for (let paragraph of paragraphs) {
      paragraph = paragraph.trim();
      if (!paragraph) continue;
      
      // Check if it's a heading (marked with **)
      if (paragraph.startsWith('**') && paragraph.endsWith('**')) {
        const headingText = paragraph.slice(2, -2);
        formattedParagraphs.push(`<h3 class="doc-subheading">${headingText}</h3>`);
      }
      // Check if it contains bullet points or numbered lists
      else if (/^[•\-\*]|^\d+\./m.test(paragraph)) {
        const lines = paragraph.split('\n');
        const listItems = lines.map(line => {
          line = line.trim();
          if (/^[•\-\*]/.test(line) || /^\d+\./.test(line)) {
            return `<div class="doc-bullet">${line}</div>`;
          }
          return line ? `<p class="doc-paragraph">${line}</p>` : '';
        }).filter(item => item);
        formattedParagraphs.push(listItems.join(''));
      }
      // Regular paragraph
      else {
        formattedParagraphs.push(`<p class="doc-paragraph">${paragraph}</p>`);
      }
    }
    
    return formattedParagraphs.join('');
  };

  // Optimized video processing with progress tracking
  const handleProcessVideoUrl = async () => {
    if (!videoUrl) return;
    
    try {
      setIsProcessingVideo(true);
      setOriginalText('🔄 Processing video... This may take a few minutes.');
      setTranslatedText('');
      
      // Revoke previous preview URL if any
      if (dubbedVideoUrl) {
        try { URL.revokeObjectURL(dubbedVideoUrl); } catch (e) {}
        setDubbedVideoUrl(null);
      }
      
      // Add timeout for long videos
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minute timeout
      
      const response = await fetch('http://localhost:8000/api/translate-video-url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          video_url: videoUrl,
          source_language_code: inputLang,
          target_language_code: outputLang,
          gender: 'male',
          sampling_rate: 22050,
          max_duration: 300 // Limit to 5 minutes
        }),
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      const contentType = response.headers.get('content-type') || '';
      
      if (!response.ok) {
        const errText = await response.text();
        let errorMsg = 'Video processing failed';
        
        try {
          const errorJson = JSON.parse(errText);
          errorMsg = errorJson.error || errorMsg;
        } catch (e) {
          // Use default error message
        }
        
        setOriginalText(`❌ Error: ${errorMsg}`);
        setTranslatedText('Please try with a shorter video or check the URL.');
        return;
      }
      
      if (!contentType.includes('video')) {
        setOriginalText('❌ Invalid response from server');
        setTranslatedText('Please try again or contact support.');
        return;
      }
      
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      setDubbedVideoUrl(url);
      setOriginalText('✅ Video processing completed successfully!');
      setTranslatedText('Your dubbed video is ready for download.');
      
    } catch (error) {
      if (error.name === 'AbortError') {
        setOriginalText('⏰ Processing timeout - Video too long');
        setTranslatedText('Please try with a shorter video (under 5 minutes).');
      } else {
        console.error('Failed processing video URL:', error);
        setOriginalText('❌ Network error occurred');
        setTranslatedText('Please check your connection and try again.');
      }
    } finally {
      setIsProcessingVideo(false);
    }
  };

  const handleClear = () => {
    setOriginalText('');
    setTranslatedText('');
    setCurrentChunkText('');
    setCurrentChunkTranslation('');
    setIsTranslating(false);
    setFile(null);
    setDocumentFile(null);
    setIsProcessingDocument(false);
    setTranslatedDocumentUrl(null);
    // Video URL related cleanup
    if (dubbedVideoUrl) { try { URL.revokeObjectURL(dubbedVideoUrl); } catch (e) {} }
    setDubbedVideoUrl(null);
    setVideoUrl('');
    setIsProcessingVideo(false);
    setMicStatus('idle');
    originalTextRef.current = '';
    translatedTextRef.current = '';
    // Stop auto-play when clearing
    stopAutoPlay();
  };

  // Cleanup function for auto-play
  useEffect(() => {
    return () => {
      stopAutoPlay();
    };
  }, []);

  // Auto-translate when output language or localization changes
  useEffect(() => {
    if (inputSource !== 'microphone' && originalText.trim() !== '') {
      translateText(originalText, inputLang, outputLang);
    }
    // eslint-disable-next-line
  }, [outputLang]);

  // Auto-translate when localization toggle changes
  useEffect(() => {
    if (inputSource !== 'microphone' && originalText.trim() !== '') {
      console.log('🔄 Localization changed, re-translating...', useLocalization);
      translateText(originalText, inputLang, outputLang);
    }
    // eslint-disable-next-line
  }, [useLocalization]);

  return (
    <div className={`app-container${theme === 'dark' ? ' dark-theme' : ''}`}>
      <button
        className="theme-toggle-btn"
        onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
        title={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
        style={{ position: 'absolute', top: 18, left: 18, fontSize: '2rem', background: 'none', border: 'none', cursor: 'pointer', zIndex: 1001 }}
      >
        {theme === 'light' ? '🌙' : '☀️'}
      </button>
      <Header />
      
      <div className="main-content">
        {/* Left Column - Input */}
        <div className="text-column">
          <div className="column-header">
            <span className="column-title">{getLeftLabel()}</span>
            <button
              className={`speaker-button ${isPlayingOriginal ? 'playing' : ''}`}
              onClick={() => playAudio(originalText, inputLang, setIsPlayingOriginal)}
              disabled={!originalText}
              title="Play input text"
            >
              🔊
            </button>
          </div>
          {inputSource === 'microphone' && micStatus === 'recording' && (
            <div className="live-chunk">
              <div><strong>Current Speech:</strong> {currentChunkText}</div>
            </div>
          )}
          {inputSource === 'document' ? (
            <div className="document-preview">
              <div className="document-content" dangerouslySetInnerHTML={{ __html: formatDocumentText(originalText) }} />
            </div>
          ) : (
            <textarea
              className="text-area"
              value={originalText}
              onChange={handleOriginalTextChange}
              placeholder={
                inputSource === 'text' 
                  ? "Enter text to translate..." 
                  : inputSource === 'microphone'
                  ? "Recorded speech will appear here..."
                  : "File content will appear here..."
              }
              readOnly={inputSource !== 'text'}
            />
          )}
        </div>

        {/* Center Column - Controls */}
        <div className="center-column">
          <InputPanel
            inputSource={inputSource}
            setInputSource={setInputSource}
            inputLang={inputLang}
            setInputLang={setInputLang}
            outputLang={outputLang}
            setOutputLang={setOutputLang}
            languageOptions={LANGUAGE_OPTIONS}
            file={file}
            handleFileChange={handleFileChange}
            documentFile={documentFile}
            handleDocumentChange={handleDocumentChange}
            micStatus={micStatus}
            handleMicRecord={handleMicRecord}
            onClear={handleClear}
            isRecording={isRecording}
            autoPlayEnabled={autoPlayEnabled}
            setAutoPlayEnabled={setAutoPlayEnabled}
            stopAutoPlay={stopAutoPlay}
            videoUrl={videoUrl}
            setVideoUrl={setVideoUrl}
            isProcessingVideo={isProcessingVideo}
            handleProcessVideoUrl={handleProcessVideoUrl}
            useLocalization={useLocalization}
            setUseLocalization={setUseLocalization}
          />
        </div>

        {/* Right Column - Output */}
        <div className="text-column">
          <div className="column-header">
            <div className="column-title-section">
              <span className="column-title">{getRightLabel()}</span>
            </div>
            <div className="header-buttons">
              <button
                className="download-text-btn"
                onClick={() => {
                  if (inputSource === 'document' && translatedDocumentUrl) {
                    // Download the actual document
                    const downloadLink = document.createElement('a');
                    downloadLink.href = translatedDocumentUrl.url;
                    downloadLink.download = translatedDocumentUrl.filename;
                    downloadLink.style.display = 'none';
                    document.body.appendChild(downloadLink);
                    downloadLink.click();
                    document.body.removeChild(downloadLink);
                  } else {
                    // Download as text file
                    downloadTranslatedText(translatedText, inputLang, outputLang);
                  }
                }}
                disabled={!translatedText && !(inputSource === 'document' && translatedDocumentUrl)}
                title={inputSource === 'document' ? 'Download translated document' : 'Download translated text'}
              >
                📥
              </button>
              <button
                className={`speaker-button ${isPlayingTranslated ? 'playing' : ''}`}
                onClick={() => playAudio(translatedText, outputLang, setIsPlayingTranslated)}
                disabled={!translatedText}
                title="Play translated text"
              >
                🔊
              </button>
            </div>
          </div>
          {inputSource === 'microphone' && micStatus === 'recording' && (
            <div className="live-chunk">
              <div><strong>Current Translation:</strong> {currentChunkTranslation}</div>
            </div>
          )}

          {dubbedVideoUrl && (
            <div className="video-preview" style={{ padding: 16, borderBottom: '1px solid #e2e8f0', background: '#fafbfc' }}>
              <div style={{ fontWeight: 600, marginBottom: 8 }}>Dubbed Video Preview</div>
              <video controls src={dubbedVideoUrl} style={{ width: '100%', borderRadius: 8, background: '#000' }} />
              <div style={{ marginTop: 10, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                <a className="clear-btn" style={{ width: 'auto', textDecoration: 'none', display: 'inline-block', padding: '8px 12px' }} href={dubbedVideoUrl} download="dubbed.mp4">Download Dubbed Video</a>
                <button className="clear-btn" style={{ width: 'auto', padding: '8px 12px' }} onClick={() => { try { URL.revokeObjectURL(dubbedVideoUrl); } catch (e) {} setDubbedVideoUrl(null); }}>Remove Preview</button>
              </div>
              {translatedText && (
                <div className="video-transcript" style={{ marginTop: 12, padding: 12, background: '#f8fafc', borderRadius: 8, border: '1px solid #e2e8f0' }}>
                  <div style={{ fontWeight: 600, marginBottom: 8, color: '#374151', fontSize: '0.9rem' }}>Translated Text:</div>
                  <div className="transcript-text" style={{ maxHeight: '120px', overflowY: 'auto', fontSize: '0.95rem', lineHeight: '1.5', color: '#4b5563' }}>
                    {translatedText}
                  </div>
                </div>
              )}
            </div>
          )}

          <div className="text-area output-area">
            {isTranslating || isProcessingDocument ? (
              <div className="translating-indicator">
                <div className="loading-dots">
                  <span>.</span><span>.</span><span>.</span>
                </div>
                {isProcessingDocument ? 'Processing document...' : 'Translating...'}
              </div>
            ) : (
              inputSource === 'document' ? (
                <div className="document-preview">
                  <div className="document-content" dangerouslySetInnerHTML={{ __html: formatDocumentText(translatedText) }} />
                </div>
              ) : (
                <div className={`output-text ${!translatedText ? 'placeholder' : ''}`}>
                  {translatedText ? decodeHtmlEntities(translatedText) : 'Translation will appear here...'}
                </div>
              )
            )}

          </div>
        </div>
      </div>



      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');

        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }

        body {
          font-family: 'Poppins', sans-serif;
          background: #f8fafc;
          height: 100vh;
          overflow: hidden;
        }

        .app-container {
          height: 100vh;
          display: flex;
          flex-direction: column;
          background: #f8fafc;
          overflow: hidden;
        }

        .app-container.dark-theme {
          background: #181a1b;
        }
        .dark-theme, .dark-theme body {
          background: #181a1b !important;
          color: #f3f4f6 !important;
        }
        .dark-theme .text-column, .dark-theme .center-column, .dark-theme .input-panel {
          background: #23272a !important;
          color: #f3f4f6 !important;
          border-color: #23272a !important;
        }
        .dark-theme .column-header, .dark-theme .output-area, .dark-theme .upload-area, .dark-theme .live-chunk {
          background: #23272a !important;
          color: #f3f4f6 !important;
        }
        .dark-theme .text-area, .dark-theme .output-area {
          background: #23272a !important;
          color: #f3f4f6 !important;
        }
        .dark-theme .text-area::placeholder, .dark-theme .output-text.placeholder {
          color: #8b949e !important;
        }
        .dark-theme .column-title {
          color: #f3f4f6 !important;
        }
        .dark-theme .record-btn {
          background: #374151 !important;
          color: #f3f4f6 !important;
          border-color: #4b5563 !important;
        }
        .dark-theme .record-btn.recording {
          background: #dc2626 !important;
        }
        .dark-theme .clear-btn, .dark-theme .prominent-clear {
          background: #23272a !important;
          color: #f3f4f6 !important;
          border-color: #4b5563 !important;
        }
        .dark-theme select,
        .dark-theme .lang-selector select,
        .dark-theme .input-panel label,
        .dark-theme .input-panel h3 {
          color: #f3f4f6 !important;
          background: #23272a !important;
        }
        .dark-theme .upload-area {
          border-color: #4b5563 !important;
        }
        .dark-theme .wave-bar {
          background: #60a5fa !important;
        }
        /* Keep header always white in dark theme */
        .dark-theme .header {
          background: white !important;
          color: #1e293b !important;
          border-bottom-color: #e2e8f0 !important;
        }
        .dark-theme .app-info h1 {
          color: #1e293b !important;
        }
        .dark-theme .tagline {
          color: #64748b !important;
        }
        .dark-theme .app-logo {
          background: #f8fafc !important;
          border-color: #e2e8f0 !important;
        }
        .dark-theme .lang-selector label,
        .dark-theme .input-source-section h3,
        .dark-theme .radio-option,
        .dark-theme .column-header,
        .dark-theme .footer,
        .dark-theme .file-selected,
        .dark-theme .mic-status {
          color: #f3f4f6 !important;
        }
        .dark-theme .radio-option input[type="radio"] {
          accent-color: #60a5fa !important;
        }

        .header {
          background: white;
          color: #1e293b;
          padding: 20px 32px;
          box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
          border-bottom: 1px solid #e2e8f0;
        }

        .header-content {
          position: relative;
          display: flex;
          align-items: center;
          max-width: 1600px;
          margin: 0 auto;
          padding: 0 20px;
        }

        .logo-section {
          position: absolute;
          left: 50%;
          transform: translateX(-50%);
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .header-logo {
          margin-left: auto;
        }

        .header-logo {
          height: 60px;
        }

        .header-logo img {
          height: 100%;
          width: auto;
          object-fit: contain;
        }



        .app-logo {
          height: 60px;
          width: 60px;
          background: #f8fafc;
          border-radius: 12px;
          padding: 8px;
          border: 2px solid #e2e8f0;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .app-logo img {
          height: 100%;
          width: 100%;
          object-fit: contain;
        }

        .app-info h1 {
          font-size: 2.5rem;
          font-weight: 700;
          margin: 0;
          color: #1e293b;
        }

        .tagline {
          font-size: 1rem;
          color: #64748b;
          font-weight: 500;
        }



        .main-content {
          flex: 1;
          display: grid;
          grid-template-columns: 1fr 1.2fr 1fr;
          gap: 24px;
          padding: 24px;
          max-width: 1600px;
          margin: 0 auto;
          width: 100%;
          min-height: 0;
          overflow: hidden;
        }

        .text-column {
          display: flex;
          flex-direction: column;
          background: white;
          border-radius: 16px;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
          overflow: hidden;
          min-height: 0;
        }

        .column-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 20px 24px;
          background: #f1f5f9;
          border-bottom: 1px solid #e2e8f0;
        }

        .column-title-section {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .auto-play-indicator {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 0.8rem;
          color: #059669;
          font-weight: 500;
        }

        .queue-count {
          color: #6b7280;
          font-size: 0.75rem;
        }

        .dark-theme .queue-count {
          color: #9ca3af;
        }

        .auto-play-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #10b981;
          animation: pulse-green 1.5s infinite;
        }

        @keyframes pulse-green {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }

        .dark-theme .auto-play-indicator {
          color: #10b981;
        }

        .dark-theme .auto-play-dot {
          background: #10b981;
        }

        .column-title {
          font-size: 1.25rem;
          font-weight: 600;
          color: #1e293b;
        }

        .speaker-button {
          width: 44px;
          height: 44px;
          border-radius: 50%;
          border: 2px solid #3b82f6;
          background: white;
          color: #3b82f6;
          font-size: 1.2rem;
          cursor: pointer;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .speaker-button:hover:not(:disabled) {
          background: #3b82f6;
          color: white;
          transform: scale(1.05);
        }

        .speaker-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
          border-color: #d1d5db;
          color: #9ca3af;
        }

        .speaker-button.playing {
          background: #3b82f6;
          color: white;
          animation: pulse 0.5s ease-in-out infinite alternate;
        }

        @keyframes pulse {
          from { transform: scale(1); }
          to { transform: scale(1.1); }
        }

        .header-buttons {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .download-text-btn {
          width: 44px;
          height: 44px;
          border-radius: 50%;
          border: 2px solid #10b981;
          background: white;
          color: #10b981;
          font-size: 1.2rem;
          cursor: pointer;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .download-text-btn:hover:not(:disabled) {
          background: #10b981;
          color: white;
          transform: scale(1.05);
        }

        .download-text-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
          border-color: #d1d5db;
          color: #9ca3af;
        }

        .dark-theme .download-text-btn {
          border-color: #10b981;
          background: #23272a;
          color: #10b981;
        }

        .dark-theme .download-text-btn:hover:not(:disabled) {
          background: #10b981;
          color: white;
        }

        .document-preview {
          flex: 1;
          min-height: 0;
          padding: 24px;
          background: white;
          overflow-y: auto;
        }

        .document-content {
          line-height: 1.8;
          font-family: 'Poppins', sans-serif;
          padding: 0;
          white-space: pre-wrap;
          word-wrap: break-word;
        }
        
        .document-content h3:first-child {
          margin-top: 0;
        }
        
        .document-content p:last-child {
          margin-bottom: 0;
        }

        .doc-subheading {
          font-size: 1.2rem;
          font-weight: 700;
          color: #1e293b;
          margin: 20px 0 12px 0;
          line-height: 1.3;
        }

        .doc-paragraph {
          margin: 12px 0;
          color: #4b5563;
          text-align: left;
          line-height: 1.8;
          font-size: 1.1rem;
          white-space: pre-wrap;
        }

        .doc-bullet {
          margin: 6px 0;
          color: #4b5563;
          padding-left: 20px;
          line-height: 1.5;
        }

        .document-content strong {
          font-weight: 700;
          color: #1e293b;
        }

        .dark-theme .document-preview {
          background: #23272a;
        }

        .dark-theme .doc-subheading {
          color: #f3f4f6;
        }

        .dark-theme .document-content strong {
          color: #f3f4f6;
        }

        .dark-theme .doc-paragraph,
        .dark-theme .doc-bullet {
          color: #d1d5db;
        }

        /* Custom scrollbar for document preview */
        .document-preview::-webkit-scrollbar {
          width: 6px;
        }

        .document-preview::-webkit-scrollbar-track {
          background: #f1f5f9;
          border-radius: 3px;
        }

        .document-preview::-webkit-scrollbar-thumb {
          background: #cbd5e1;
          border-radius: 3px;
          transition: background 0.2s ease;
        }

        .document-preview::-webkit-scrollbar-thumb:hover {
          background: #94a3b8;
        }

        .document-preview {
          scrollbar-width: thin;
          scrollbar-color: #cbd5e1 #f1f5f9;
        }

        .text-area {
          flex: 1;
          min-height: 0;
          padding: 24px;
          border: none;
          font-size: 1.1rem;
          line-height: 1.6;
          font-family: 'Poppins', sans-serif;
          resize: none;
          outline: none;
          background: white;
          overflow-y: auto;
        }

        /* Custom thin scrollbar for text areas */
        .text-area::-webkit-scrollbar {
          width: 6px;
        }

        .text-area::-webkit-scrollbar-track {
          background: #f1f5f9;
          border-radius: 3px;
        }

        .text-area::-webkit-scrollbar-thumb {
          background: #cbd5e1;
          border-radius: 3px;
          transition: background 0.2s ease;
        }

        .text-area::-webkit-scrollbar-thumb:hover {
          background: #94a3b8;
        }

        /* Firefox scrollbar */
        .text-area {
          scrollbar-width: thin;
          scrollbar-color: #cbd5e1 #f1f5f9;
        }

        .text-area::placeholder {
          color: #9ca3af;
        }

        .output-area {
          background: #fafbfc;
          position: relative;
          display: flex;
          align-items: flex-start;
          padding: 24px;
          overflow-y: auto;
        }

        /* Custom thin scrollbar for output area */
        .output-area::-webkit-scrollbar {
          width: 6px;
        }

        .output-area::-webkit-scrollbar-track {
          background: #f1f5f9;
          border-radius: 3px;
        }

        .output-area::-webkit-scrollbar-thumb {
          background: #cbd5e1;
          border-radius: 3px;
          transition: background 0.2s ease;
        }

        .output-area::-webkit-scrollbar-thumb:hover {
          background: #94a3b8;
        }

        /* Firefox scrollbar */
        .output-area {
          scrollbar-width: thin;
          scrollbar-color: #cbd5e1 #f1f5f9;
        }

        /* Custom scrollbar for video transcript */
        .transcript-text::-webkit-scrollbar {
          width: 6px;
        }

        .transcript-text::-webkit-scrollbar-track {
          background: #f1f5f9;
          border-radius: 3px;
        }

        .transcript-text::-webkit-scrollbar-thumb {
          background: #cbd5e1;
          border-radius: 3px;
          transition: background 0.2s ease;
        }

        .transcript-text::-webkit-scrollbar-thumb:hover {
          background: #94a3b8;
        }

        /* Firefox scrollbar for transcript */
        .transcript-text {
          scrollbar-width: thin;
          scrollbar-color: #cbd5e1 #f1f5f9;
        }

        .output-text {
          width: 100%;
          word-wrap: break-word;
          line-height: 1.6;
        }

        .output-text.placeholder {
          color: #9ca3af;
        }

        .translating-indicator {
          display: flex;
          align-items: center;
          gap: 12px;
          color: #6366f1;
          font-weight: 500;
        }

        .loading-dots {
          display: flex;
          gap: 2px;
        }

        .loading-dots span {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: #6366f1;
          animation: bounce 1.4s infinite both;
        }

        .loading-dots span:nth-child(1) { animation-delay: -0.32s; }
        .loading-dots span:nth-child(2) { animation-delay: -0.16s; }

        @keyframes bounce {
          0%, 80%, 100% { transform: scale(0); }
          40% { transform: scale(1); }
        }

        .center-column {
          display: flex;
          flex-direction: column;
          gap: 24px;
          background: #f0f9ff;
          border-radius: 16px;
          padding: 24px;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
          min-height: 0;
          overflow: hidden;
        }

        .input-panel {
          background: white;
          border-radius: 12px;
          padding: 12px 12px 8px 12px;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }

        .input-source-section h3 {
          font-size: 1.1rem;
          font-weight: 600;
          color: #1e293b;
          margin-bottom: 16px;
        }

        .radio-group {
          display: flex;
          gap: 20px;
          margin-bottom: 20px;
        }

        .radio-option {
          display: flex;
          align-items: center;
          gap: 8px;
          cursor: pointer;
          font-weight: 500;
          color: #374151;
        }

        .radio-option input[type="radio"] {
          width: 18px;
          height: 18px;
          accent-color: #3b82f6;
        }

        .file-upload-section, .document-upload-section, .microphone-section {
          margin-bottom: 20px;
          min-height: 120px;
        }

        .upload-area {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 10px 8px;
          border: 2px dashed #d1d5db;
          border-radius: 12px;
          background: #f9fafb;
          cursor: pointer;
          transition: all 0.2s ease;
          text-align: center;
        }

        .upload-area:hover {
          border-color: #3b82f6;
          background: #eff6ff;
        }

        .upload-area input[type="file"] {
          display: none;
        }

        .upload-icon {
          font-size: 3rem;
          margin-bottom: 12px;
          filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
        }

        .upload-text {
          display: flex;
          flex-direction: column;
          gap: 4px;
          color: #6b7280;
          font-weight: 500;
        }

        .upload-text strong {
          color: #374151;
          font-size: 1.1rem;
        }

        .file-selected {
          margin-top: 12px;
          padding: 8px 16px;
          background: #dcfce7;
          color: #16a34a;
          border-radius: 6px;
          font-size: 0.9rem;
          font-weight: 500;
        }

        .supported-formats {
          margin-top: 8px;
          text-align: center;
        }

        .supported-formats small {
          color: #6b7280;
          font-size: 0.8rem;
          font-style: italic;
        }

        .document-download-section {
          margin-top: 16px;
          padding: 12px;
          background: #f0f9ff;
          border-radius: 8px;
          text-align: center;
        }

        .download-btn {
          display: inline-block;
          padding: 10px 20px;
          background: #3b82f6;
          color: white;
          text-decoration: none;
          border-radius: 8px;
          font-weight: 600;
          transition: all 0.2s ease;
          border: none;
          cursor: pointer;
        }

        .download-btn:hover {
          background: #2563eb;
          transform: translateY(-1px);
          text-decoration: none;
          color: white;
        }

        .dark-theme .document-download-section {
          background: #1e293b;
        }

        .dark-theme .download-btn {
          background: #60a5fa;
        }

        .dark-theme .download-btn:hover {
          background: #3b82f6;
        }

        .mic-controls {
          display: flex;
          align-items: center;
          gap: 16px;
          margin-bottom: 16px;
        }

        .record-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          padding: 12px 20px;
          background: #3b82f6;
          color: white;
          border: none;
          border-radius: 25px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
          font-family: 'Poppins', sans-serif;
          width: 120px;
          min-width: 120px;
        }

        .record-btn:hover:not(:disabled) {
          background: #2563eb;
          transform: translateY(-1px);
        }

        .record-btn:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }

        .record-btn.recording {
          background: #dc2626;
          animation: pulse-red 1s infinite;
        }

        @keyframes pulse-red {
          0% { background: #dc2626; }
          50% { background: #ef4444; }
          100% { background: #dc2626; }
        }

        .record-dot {
          width: 10px;
          height: 10px;
          border-radius: 50%;
          background: white;
        }

        .mic-status {
          color: #6b7280;
          font-weight: 500;
          width: 120px;
          min-width: 120px;
        }

        .waveform-visualization {
          display: flex;
          align-items: flex-end;
          justify-content: center;
          gap: 4px;
          padding: 20px;
          background: #eff6ff;
          border-radius: 8px;
          height: 80px; /* Increased height */
          min-height: 80px;
          max-height: 80px;
        }

        .wave-bar {
          width: 4px;
          background: #3b82f6;
          border-radius: 2px;
          animation: wave 1s infinite ease-in-out;
        }
        .wave-bar:nth-child(1) { animation-delay: 0s; }
        .wave-bar:nth-child(2) { animation-delay: 0.1s; }
        .wave-bar:nth-child(3) { animation-delay: 0.2s; }
        .wave-bar:nth-child(4) { animation-delay: 0.3s; }
        .wave-bar:nth-child(5) { animation-delay: 0.4s; }

        @keyframes wave {
          0%, 100% { height: 10px; }
          50% { height: 40px; }
        }

        .language-selectors {
          display: flex;
          gap: 20px;
          margin-bottom: 20px;
        }

        .lang-selector {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .lang-selector label {
          font-weight: 500;
          color: #374151;
          font-size: 0.95rem;
        }

        .lang-selector select {
          padding: 10px 12px;
          border: 1.5px solid #d1d5db;
          border-radius: 8px;
          background: white;
          font-family: 'Poppins', sans-serif;
          font-size: 1rem;
          color: #374151;
          outline: none;
          transition: border-color 0.2s ease;
        }

        .lang-selector select:focus {
          border-color: #3b82f6;
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        .clear-btn {
          width: 100%;
          padding: 12px;
          background: #f3f4f6;
          border: 1.5px solid #d1d5db;
          border-radius: 8px;
          font-weight: 600;
          color: #374151;
          cursor: pointer;
          transition: all 0.2s ease;
          font-family: 'Poppins', sans-serif;
          font-size: 1rem;
        }

        .clear-btn:hover {
          background: #e5e7eb;
          border-color: #9ca3af;
        }

        .auto-play-section {
          margin-bottom: 20px;
        }

        .auto-play-toggle {
          display: flex;
          align-items: center;
          gap: 12px;
          cursor: pointer;
          font-weight: 500;
          color: #374151;
          margin-bottom: 8px;
        }

        .auto-play-toggle input[type="checkbox"] {
          display: none;
        }

        .toggle-slider {
          position: relative;
          width: 50px;
          height: 24px;
          background: #d1d5db;
          border-radius: 12px;
          transition: background 0.3s ease;
        }

        .toggle-slider:before {
          content: '';
          position: absolute;
          top: 2px;
          left: 2px;
          width: 20px;
          height: 20px;
          background: white;
          border-radius: 50%;
          transition: transform 0.3s ease;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }

        .auto-play-toggle input[type="checkbox"]:checked + .toggle-slider {
          background: #3b82f6;
        }

        .auto-play-toggle input[type="checkbox"]:checked + .toggle-slider:before {
          transform: translateX(26px);
        }

        .toggle-label {
          font-size: 0.95rem;
        }

        .auto-play-info {
          padding: 8px 12px;
          background: #dcfce7;
          color: #16a34a;
          border-radius: 6px;
          font-size: 0.9rem;
          font-weight: 500;
          text-align: center;
        }

        .dark-theme .auto-play-toggle {
          color: #f3f4f6;
        }

        .dark-theme .toggle-slider {
          background: #4b5563;
        }

        .dark-theme .auto-play-toggle input[type="checkbox"]:checked + .toggle-slider {
          background: #60a5fa;
        }

        .dark-theme .auto-play-info {
          background: #1f2937;
          color: #10b981;
        }

        .localization-section {
          margin-bottom: 20px;
        }

        .localization-toggle {
          display: flex;
          align-items: center;
          gap: 12px;
          cursor: pointer;
          font-weight: 500;
          color: #374151;
          margin-bottom: 8px;
        }

        .localization-toggle input[type="checkbox"] {
          display: none;
        }

        .localization-info {
          padding: 8px 12px;
          background: #fef3c7;
          color: #d97706;
          border-radius: 6px;
          font-size: 0.9rem;
          font-weight: 500;
          text-align: center;
        }

        .dark-theme .localization-toggle {
          color: #f3f4f6;
        }

        .dark-theme .localization-info {
          background: #1f2937;
          color: #fbbf24;
        }

        .localization-toggle input[type="checkbox"]:checked + .toggle-slider {
          background: #10b981 !important;
        }

        .localization-toggle input[type="checkbox"]:checked + .toggle-slider:before {
          transform: translateX(26px) !important;
        }

        .dark-theme .localization-toggle input[type="checkbox"]:checked + .toggle-slider {
          background: #10b981 !important;
        }



        .live-chunk {
          background: #f0f9ff;
          padding: 10px 18px;
          font-size: 1.05rem;
          color: #0a2540;
          border-bottom: 1px solid #e2e8f0;
        }

        @media (max-width: 1200px) {
          .main-content {
            grid-template-columns: 1fr;
            gap: 16px;
            padding: 16px;
          }
          
          .header {
            padding: 16px 20px;
          }
          
          .header h1 {
            font-size: 1.8rem;
          }
          

        }

        @media (max-width: 768px) {
          .radio-group {
            flex-direction: column;
            gap: 12px;
          }
          
          .language-selectors {
            flex-direction: column;
            gap: 16px;
          }
          
          .mic-controls {
            flex-direction: column;
            align-items: stretch;
            gap: 12px;
          }
          
          .header-content {
            flex-direction: column;
            gap: 16px;
          }
          
          .logo-section {
            flex-direction: column;
            text-align: center;
            gap: 8px;
          }
          
          .app-info h1 {
            font-size: 2rem;
          }
          

        }
      `}</style>
    </div>
  );
}

export default App;