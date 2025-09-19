# BhashaSetu - Real-Time Multilingual Speech & Text Translator

BhashaSetu is a modern, real-time multilingual translation application that bridges language barriers through speech-to-text, text translation, and text-to-speech capabilities.

## 🌟 Features

### Core Functionality
- **Multi-Input Support**: Text input, file upload, and real-time microphone recording
- **Real-Time Translation**: Instant translation between multiple Indian languages
- **Speech-to-Text**: Convert spoken words to text in real-time
- **Text-to-Speech**: Hear translations spoken aloud
- **Auto-Play**: Real-time audio playback for microphone translations

### Supported Languages
- English (en-IN)
- Telugu (te-IN)
- Hindi (hi-IN)
- Tamil (ta-IN)
- Kannada (kn-IN)
- Malayalam (ml-IN)
- Bengali (bn-IN)
- Gujarati (gu-IN)
- Marathi (mr-IN)
- Punjabi (pa-IN)

### User Interface
- **Modern Design**: Clean, responsive interface with dark/light theme support
- **Real-Time Feedback**: Live display of current speech and translation
- **Intuitive Controls**: Easy-to-use microphone, file upload, and text input
- **Visual Indicators**: Recording status, translation progress, and audio playback

## 🚀 Getting Started

### Prerequisites
- Node.js (v14 or higher)
- npm or yarn
- Backend API server running on `http://localhost:8000`

### Installation

1. **Install dependencies**
   ```bash
   npm install
   ```

2. **Start the development server**
   ```bash
   npm start
   ```

3. **Open your browser**
   Navigate to `http://localhost:3000`

### Building for Production

```bash
npm run build
```

## 🏗️ Architecture

### Frontend Structure
```
src/
├── App.js              # Main application component
├── index.js            # Application entry point
├── index.css           # Global styles
```

### Key Components

#### App.js
The main React component that handles:
- **State Management**: All application state and refs
- **API Integration**: Speech-to-text, translation, and TTS calls
- **Audio Processing**: Real-time microphone streaming and processing
- **UI Rendering**: Complete application interface

#### State Organization
```javascript
// Input/Output Configuration
const [inputSource, setInputSource] = useState('text');
const [inputLang, setInputLang] = useState('en-IN');
const [outputLang, setOutputLang] = useState('te-IN');

// Text Content
const [originalText, setOriginalText] = useState('');
const [translatedText, setTranslatedText] = useState('');

// UI State
const [isTranslating, setIsTranslating] = useState(false);
const [theme, setTheme] = useState('light');

// Microphone State
const [micStatus, setMicStatus] = useState('idle');
const [isRecording, setIsRecording] = useState(false);

// Auto-Play State
const [autoPlayEnabled, setAutoPlayEnabled] = useState(false);
```

## 🔧 API Integration

### Backend Endpoints
- `POST /api/speech-to-text` - Convert audio to text
- `POST /api/translate` - Translate text between languages
- `POST /api/text-to-speech` - Convert text to speech

### API Configuration
All API calls are configured to use `http://localhost:8000` as the base URL.

## 🎤 Microphone Functionality

### Real-Time Audio Processing
1. **Audio Capture**: Uses Web Audio API for real-time microphone access
2. **Chunk Processing**: Audio is processed in 3-second chunks
3. **WAV Encoding**: PCM data is converted to WAV format
4. **API Integration**: Encoded audio is sent to speech-to-text API
5. **Translation Pipeline**: Transcribed text is immediately translated

### Auto-Play Queue System
- **Sequential Playback**: Audio chunks are queued and played in order
- **No Interruption**: New translations wait for current audio to finish
- **Resource Management**: Automatic cleanup of audio URLs and resources

## 🎨 Styling

### CSS Architecture
- **Inline Styles**: Component-specific styles in JSX
- **CSS-in-JS**: Styles embedded in the main component
- **Responsive Design**: Mobile-friendly layout with CSS Grid
- **Theme Support**: Dark and light theme implementation

### Key Style Features
- Modern card-based layout
- Smooth animations and transitions
- Custom scrollbars
- Responsive grid system
- Theme-aware color schemes

## 🔍 Code Quality

### Documentation
- **Comprehensive Comments**: All functions and complex logic are documented
- **JSDoc Format**: Standard documentation format for functions
- **Section Organization**: Code is organized into logical sections
- **Inline Comments**: Complex operations have step-by-step explanations

### Code Organization
```javascript
// ===== STATE MANAGEMENT =====
// ===== UTILITY FUNCTIONS =====
// ===== AUTO-PLAY QUEUE MANAGEMENT =====
// ===== EFFECTS =====
// ===== TEXT HANDLING FUNCTIONS =====
// ===== SPEECH-TO-TEXT FUNCTIONS =====
// ===== TEXT-TO-SPEECH FUNCTIONS =====
// ===== FILE HANDLING FUNCTIONS =====
// ===== MICROPHONE HANDLING FUNCTIONS =====
// ===== UI HANDLERS =====
// ===== MAIN RENDER =====
```

## 📈 Performance & Latency Results

| Scenario              | Input Method      | Chunk/File Size   | Total Latency (s) | Cost (₹) | Notes                                    |
|----------------------|------------------|-------------------|-------------------|----------|-------------------------------------------|
| Text translation     | Text input       | 100 words         | 3.16              | ₹1.00    | 500 characters @ ₹20/10K chars           |
| Real-time speech     | Microphone       | 3 sec chunks      | 0.95              | ₹0.10    | STT+Translate: ₹0.025 + TTS: ₹0.075      |
| **Real-time speech-to-speech** | **Microphone + Auto-play** | **3 sec chunks** | **2.73** | **₹0.10** | **STT: ~0.96s + Translation: ~0.55s + TTS: ~1.23s** |
| File upload          | Video/audio file | 30 sec file       | 2.03              | ₹0.55    | STT+Translate: ₹0.25 + TTS: ₹0.30        |
| **Text-to-Speech**   | **Speaker button**| **250 characters**| **1.32**          | **₹0.38** | **Per 250-character chunk**               |

- **Real-time speech (microphone):** ~0.95s per 3s chunk (STT + Translation only)
- **Real-time speech-to-speech:** ~2.73s per 3s chunk (complete pipeline with auto-playback)
- **File upload (video/audio):** ~2.03s for 30s file (batch processing)
- **Text translation (100 words):** ~3.16s
- **Text-to-Speech (manual):** ~1.32s per 250-character chunk

*Real-time processing provides results every 3 seconds. Speech-to-speech includes automatic TTS playback. File upload latency is for the entire file. TTS chunks text by sentences (max 250 chars) for faster initial playback.*

**Cost Analysis:** Based on Sarvam.AI pricing - Speech-to-Text & Translate: ₹30/hour, Translate Mayura V1: ₹20/10K characters, Text-to-Speech: ₹15/10K characters.

## 🐛 Troubleshooting

### Common Issues

1. **Microphone Not Working**
   - Ensure browser permissions are granted
   - Check if HTTPS is required for microphone access
   - Verify audio input devices are connected

2. **Translation Not Working**
   - Verify backend server is running on port 8000
   - Check network connectivity
   - Ensure API endpoints are accessible

3. **Audio Playback Issues**
   - Check browser audio permissions
   - Verify audio output devices are connected
   - Clear browser cache if needed

### Debug Information
The application includes comprehensive console logging for debugging:
- Microphone recording status
- API request/response details
- Audio processing steps
- Error handling and recovery

## 🤝 Contributing

### Development Guidelines
1. **Code Style**: Follow existing comment and organization patterns
2. **Testing**: Test all input methods (text, file, microphone)
3. **Documentation**: Update comments when modifying functionality
4. **Error Handling**: Implement proper error handling for new features

### Adding New Features
1. **Language Support**: Add new languages to `LANGUAGE_OPTIONS`
2. **UI Components**: Create reusable components in `components/` directory
3. **API Integration**: Follow existing API call patterns
4. **State Management**: Add new state variables in appropriate sections

## 📄 License

This project is part of the BhashaSetu initiative for bridging language barriers in India.

## 🙏 Acknowledgments

- **Backend API**: Powered by Sarvam AI for speech and translation services
- **UI Framework**: Built with React and modern web technologies
- **Audio Processing**: Web Audio API for real-time audio handling
- **Design**: Modern, accessible interface design

---

**BhashaSetu** - Bridging languages, connecting people. 🌉
