# Dobbie - Magical Desktop Assistant

Dobbie is a web-based Windows desktop assistant that greets you when your laptop opens, launches apps, searches the web, hunts files with fuzzy name matching, checks your emails, and gets very happy when someone says "socks".

The design is wizard-school inspired: dark green, maroon, gold, and parchment tones with an animated castle background and a beautiful Dobbie portrait.

## Features

- ✨ Beautiful web-based UI with animated background
- 🎙️ Voice commands with speech recognition
- 📱 Text-based commands
- 📧 Gmail integration (check emails from multiple accounts)
- 🖥️ Open apps and applications
- 📁 Find files with fuzzy name matching
- 🌐 Search the web and open websites
- 💻 Direct access to CMD and system commands
- ⚡ Quick action buttons (CHROME, FILES, WEB, HELP)
- 🎭 Wizard-school themed styling

## System Requirements

- Windows 10 or newer
- Python 3.9 or newer
- A modern web browser (Chrome, Edge, Firefox, Safari)

## Installation

1. **Install Python dependencies:**

```powershell
cd c:\Users\mradu\Desktop\dobbie
python -m pip install -r requirements.txt
```

If `pyaudio` fails, try:
```powershell
pip install pipwin
pipwin install pyaudio
```

2. **Setup Gmail Integration (Optional but Recommended):**

To enable email checking, you need to:

1. Enable 2-Factor Authentication on your Gmail account(s)
2. Generate an "App Password" for each Gmail account:
   - Go to https://myaccount.google.com/
   - Click "Security" (or go to https://myaccount.google.com/security)
   - Find "App passwords" (you need 2FA enabled)
   - Select "Mail" and "Windows Computer"
   - Google will generate a 16-character password
   - Copy this password

3. Update `config.json` with your Gmail credentials:

```json
"emails": [
  {
    "email": "mradulraghuwanshi@gmail.com",
    "app_password": "xxxx xxxx xxxx xxxx"
  },
  {
    "email": "aartiraghuwanshi01@gmail.com",
    "app_password": "xxxx xxxx xxxx xxxx"
  }
]
```

## Running Dobbie

```powershell
python app.py
```

This will start the Dobbie server on http://localhost:5000

Open your web browser and visit: **http://localhost:5000**

## Usage Examples

### Voice Commands
- Click the 🎙️ microphone button and speak:
  - "Open Chrome"
  - "Search web weather today"
  - "Find file resume"
  - "Check emails"
  - "What can you do?"

### Text Commands
Type in the command box:
- `open chrome` - Opens Google Chrome
- `open canva` - Opens Canva or other apps
- `search web [query]` - Searches Google for your query
- `find file [name]` - Finds files by name (fuzzy matching)
- `open file [name]` - Opens the best matching file
- `check emails` - Shows your unread emails
- `open cmd` - Opens Command Prompt
- `open file explorer` - Opens Windows File Explorer

### Quick Buttons
- **CHROME** - Opens Chrome
- **FILES** - Opens file browser
- **WEB** - Opens web search
- **HELP** - Shows what Dobbie can do

## Configuration

Edit `config.json` to customize:

- **apps**: Add or modify app shortcuts
- **browser**: Set default browser (chrome, edge)
- **web_search_engine**: Change search engine URL
- **search_dirs**: Add directories to search for files
- **match_threshold**: Adjust file matching sensitivity (0.0 - 1.0)
- **emails**: Configure Gmail accounts

### Example config.json

```json
{
  "apps": {
    "chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "canva": "C:\\Program Files\\Canva\\Canva.exe",
    "cmd": "cmd",
    "explorer": "explorer"
  },
  "browser": "chrome",
  "emails": [
    {
      "email": "your.email@gmail.com",
      "app_password": "xxxx xxxx xxxx xxxx"
    }
  ]
}
```

## Troubleshooting

### Voice input not working
- Make sure you have `SpeechRecognition` and `pyaudio` installed
- Check your microphone permissions in Windows
- Try using text commands instead

### Can't find files
- Make sure the search directories are correct in config.json
- Try searching with shorter names (e.g., "resume" instead of "my_resume_2024")
- Adjust `match_threshold` to be less strict (lower value = more matches)

### Gmail not working
- Verify you've enabled 2-Factor Authentication
- Make sure you generated an "App Password" (not your regular password)
- Check that the email and password are correct in config.json
- Gmail may take a few seconds to fetch emails on first load

### Apps not opening
- Add the app to the "apps" section in config.json
- Use the full path if the app isn't in your PATH environment variable
- Try opening the app manually to make sure it's installed

## Advanced Usage

### Opening specific Chrome profiles
You can modify the Chrome app path to use a specific profile:

```json
"chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe --profile-directory=\"Profile 1\""
```

### Adding custom commands
Edit `app.py` to add custom command handlers in the `handle()` method of the `Dobbie` class.

## Theme Customization

Edit `styles.css` to customize colors:

- `--parchment`: Light background color
- `--gold`: Accent color
- `--dark`: Main background color
- `--green`: Secondary accent color

## Credits

Designed as a wizard-school themed desktop assistant. All artwork is original and inspired by magical school aesthetics.

## License

Feel free to modify and use this for your own magical desktop needs! ✨


Try:

```text
open vs code
find file resume
open file resume
hunt file project report
search web python tkinter tutorial
google weather today
open website youtube.com
socks
```

## Voice Interaction

Dobbie can listen and speak when the voice packages are installed.

1. Open Dobbie.
2. Click `Mic`.
3. Say a command like `open chrome`, `search web weather today`, or
   `find file resume`.
4. Dobbie writes what it heard, runs the command, and speaks the reply.

The status line under the title shows whether Dobbie is listening, working, or
ready for the next command. If the microphone fails, check Windows microphone
permission and your selected input device.

Dobbie speaks every command reply he writes in the chat. Multi-line replies are
spoken as one sentence sequence, so the voice follows the same message you see
on screen.

You can also talk to Dobbie conversationally:

```text
hello
how are you
what can you do
thank you
```

## Make Dobbie Open When Your Laptop Starts

Dobbie is configured to open automatically when you log into Windows through
this shortcut:

```text
C:\Users\mradu\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\Dobbie.lnk
```

That shortcut runs:

```text
C:\Users\mradu\AppData\Local\Programs\Python\Python311\pythonw.exe "C:\Users\mradu\Desktop\dobbie\main.py"
```

Using `pythonw.exe` opens the assistant without a black terminal window.

## Keyboard Shortcut

Press `Ctrl + Alt + D` to open Dobbie whenever you want.

The hotkey is attached to these shortcuts:

```text
C:\Users\mradu\Desktop\Dobbie.lnk
C:\Users\mradu\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Dobbie.lnk
```

If Dobbie is already open, Windows may open another copy when you press the
shortcut. Close extra windows normally.

## Customize

Edit `config.json`.

`apps` maps command names to Windows commands. Example:

```json
"vscode": "code",
"chrome": "chrome",
"calculator": "calc"
```

`search_dirs` controls where Dobbie hunts files. Add folders you use often:

```json
"%USERPROFILE%\\Desktop",
"%USERPROFILE%\\Documents",
"%USERPROFILE%\\Downloads",
"%USERPROFILE%\\Pictures",
"%USERPROFILE%\\Music",
"%USERPROFILE%\\Videos",
"%USERPROFILE%\\OneDrive"
```

`match_threshold` controls fuzzy file matching. `0.7` means about 70%.

`browser` controls what app Dobbie uses for web searches. It defaults to
`chrome`.

`web_search_engine` controls the search URL. The default is Google:

```json
"https://www.google.com/search?q={query}"
```

`always_on_top` can be changed to `true` if you want Dobbie to stay above other
windows:

```json
"always_on_top": true
```

## Command Reference

| Command | What Dobbie does |
| --- | --- |
| `open <app name>` | Opens an app from `config.json` |
| `find file <name>` | Fuzzy-searches known folders |
| `open file <name>` | Opens the best matching file |
| `hunt file <name>` | Same as file search |
| `search web <query>` | Opens Chrome and searches Google |
| `google <query>` | Opens Chrome and searches Google |
| `open website <domain>` | Opens a website directly |
| `socks` | Dobbie becomes very happy |

## Notes

- Voice recognition uses the `SpeechRecognition` package and Google's web API,
  so it needs an internet connection.
- Searching the whole `C:\` drive is possible but slow. Add specific folders to
  `search_dirs` for faster results.
- To turn this into a standalone `.exe`, package it with PyInstaller.
