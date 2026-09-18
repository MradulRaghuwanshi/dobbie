# Dobbie Setup Guide

## Quick Start

1. **Install Python 3.9+** from https://www.python.org/
2. **Open PowerShell in the Dobbie folder**
3. **Run:** `python -m pip install -r requirements.txt`
4. **Run:** `python app.py`
5. **Open:** http://localhost:5000 in your browser

## Email Setup (Gmail Integration)

### Enable Gmail for Dobbie

To allow Dobbie to check your emails, follow these steps:

#### Step 1: Enable 2-Factor Authentication
1. Go to https://myaccount.google.com/
2. Click **"Security"** on the left sidebar
3. Scroll down to **"2-Step Verification"**
4. Click **"Get Started"** (if not already enabled)
5. Follow the prompts to set up 2-Factor Authentication

#### Step 2: Create App Password
1. After 2FA is enabled, go back to https://myaccount.google.com/security
2. Scroll down to **"App passwords"** (it appears after enabling 2FA)
3. If you don't see "App passwords":
   - Make sure 2-Factor Authentication is enabled
   - You're using a Gmail account (not a work account)
4. Select **"Mail"** and **"Windows Computer"** from the dropdowns
5. Google will generate a 16-character password
6. **Copy this password exactly** (including spaces)

#### Step 3: Add to config.json
1. Open `config.json` in a text editor
2. Find the `"emails"` section
3. Replace `YOUR_APP_PASSWORD_HERE` with the generated password:

```json
"emails": [
  {
    "email": "mradulraghuwanshi@gmail.com",
    "app_password": "xxxx xxxx xxxx xxxx"
  },
  {
    "email": "aartiraghuwanshi01@gmail.com",
    "app_password": "yyyy yyyy yyyy yyyy"
  }
]
```

4. **Save the file**

### Test Email Setup
1. Start Dobbie: `python app.py`
2. Open http://localhost:5000
3. Type or say: **"check emails"**
4. Dobbie should show your unread emails

## Voice Commands Setup

### Check Microphone
1. Make sure your microphone is connected and working
2. Windows should have microphone permissions enabled for your browser
3. When you click the 🎙️ microphone button, your browser should ask for permission

### If Voice Doesn't Work
- Install/reinstall `SpeechRecognition` and `pyaudio`:
  ```powershell
  pip uninstall SpeechRecognition pyaudio
  pip install SpeechRecognition pyaudio
  ```
- Try using text commands instead (click "Send" button or press Enter)
- Check Windows privacy settings: Settings → Privacy & Security → Microphone

## Adding Custom Applications

### Add Apps to config.json
Open `config.json` and add your apps to the `"apps"` section:

```json
"apps": {
  "chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  "canva": "C:\\Users\\mradu\\AppData\\Local\\Canva\\Canva.exe",
  "photoshop": "C:\\Program Files\\Adobe\\Adobe Photoshop 2024\\Photoshop.exe",
  "vs code": "code",
  "excel": "excel",
  "word": "winword"
}
```

### How to Find App Paths
1. Right-click the application shortcut on your desktop or Start menu
2. Select **"Open file location"**
3. Right-click the application executable (.exe)
4. Select **"Properties"**
5. Copy the **"Location"** field
6. The full path is: `Location\Executable Name.exe`

## File Search Configuration

### Add Directories to Search
Edit the `"search_dirs"` in config.json:

```json
"search_dirs": [
  "%USERPROFILE%\\Desktop",
  "%USERPROFILE%\\Documents",
  "%USERPROFILE%\\Downloads",
  "%USERPROFILE%\\OneDrive",
  "C:\\Users\\mradu\\Projects"
]
```

### Adjust Search Sensitivity
- **Lower `match_threshold`** (0.5-0.6) = More results, lower accuracy
- **Higher `match_threshold`** (0.8-0.9) = Fewer results, higher accuracy
- Default: 0.7

```json
"match_threshold": 0.7
```

## Keyboard Shortcuts & Tips

| Action | How |
|--------|-----|
| Send command | Click "Send" or press **Enter** |
| Voice command | Click 🎙️ microphone and speak |
| Clear input | Type command and press **Enter** |
| Quick actions | Click CHROME, FILES, WEB, or HELP |
| Scroll messages | Use mouse wheel or arrow keys |

## Common Commands

```
Voice & Text Commands:
- open chrome
- open cmd (opens Command Prompt)
- open file explorer
- open canva
- open [app name]

Search:
- search web [query]
- find file [name]
- open file [name]

Email:
- check emails
- check my emails

Help:
- what can you do
- help
- commands
```

## Troubleshooting

### Problem: Can't open apps
**Solution:**
- Add the app to `config.json` under `"apps"`
- Use the full path: `"C:\\Program Files\\...\\app.exe"`
- Make sure the app is installed on your computer

### Problem: Can't find files
**Solution:**
- Make sure the search directories are correct in config.json
- Try shorter search terms (e.g., "resume" not "my_detailed_resume_2024")
- Lower the `match_threshold` to get more results
- Add the directory containing your files to `search_dirs`

### Problem: Gmail not working
**Solution:**
- Verify 2-Factor Authentication is enabled
- Make sure you used an **App Password** (not your regular Gmail password)
- Check that the email address is correct in config.json
- Try copying/pasting the password again (make sure no extra spaces)

### Problem: Voice input not working
**Solution:**
- Allow microphone access when prompted by your browser
- Check Windows Settings → Privacy & Security → Microphone
- Try using text commands instead
- Re-run: `pip install --upgrade SpeechRecognition pyaudio`

### Problem: Website won't open in Chrome
**Solution:**
- Make sure Chrome is installed
- Check the Chrome path in config.json
- Try: `"open website https://google.com"`
- Test by clicking the CHROME button first

### Problem: Server won't start
**Solution:**
- Make sure port 5000 is not in use
- Try: `python app.py` from the correct folder
- Check that all dependencies are installed: `pip install -r requirements.txt`

## Advanced Configuration

### Change Web Search Engine
```json
"web_search_engine": "https://www.bing.com/search?q={query}"
```

### Change Default Browser
```json
"browser": "edge"  // or "chrome"
```

### Disable Always-on-Top (for window)
```json
"always_on_top": false
```

### Adjust Window Size
```json
"window_width": 900,
"window_height": 820
```

## Running on Startup

### Option 1: Create a Batch File
Create `run_dobbie.bat`:
```batch
@echo off
python app.py
```

### Option 2: Add to Windows Startup Folder
1. Press **Win + R**
2. Type: `shell:startup`
3. Copy your batch file here

### Option 3: Task Scheduler
1. Open Task Scheduler (search in Windows)
2. Create Basic Task
3. Set trigger: "At log on"
4. Set action: Start program → Choose `python.exe` with arguments `app.py`

## Support & Tips

- **Browser**: Works best in Chrome, Edge, or Firefox
- **Port**: Dobbie runs on localhost:5000 (can be changed in app.py)
- **Local only**: Dobbie can only be accessed from your computer
- **Security**: Don't share your config.json (contains email passwords)

## File Structure

```
dobbie/
├── index.html          # Web interface
├── styles.css          # Styling
├── script.js           # Frontend logic
├── app.py              # Flask backend
├── config.json         # Configuration
├── requirements.txt    # Python dependencies
├── README.md           # Quick reference
└── SETUP.md            # This file
```

---

**Enjoy your magical desktop assistant! ✨**
