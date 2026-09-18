# ⚡ Dobbie Auto-Start Setup

## 🎯 Quick Setup (2 Minutes)

### Option 1: Auto-Start on PC Boot (Recommended)

1. **Open File Explorer** and go to:
   ```
   c:\Users\mradu\Desktop\dobbie
   ```

2. **Double-click `add_to_startup.bat`**
   - A command window will appear
   - You'll see a confirmation message ✓
   - Press any key to close

3. **Restart your PC**
   - Dobbie will automatically start
   - Your browser will open http://localhost:5000

### Option 2: Manual Startup Folder

1. **Press `Win + R`** and type:
   ```
   shell:startup
   ```

2. **Create a shortcut:**
   - Right-click → New → Shortcut
   - Location: `c:\Users\mradu\Desktop\dobbie\run_dobbie.bat`
   - Name: `Dobbie`

3. **Double-click the shortcut to start Dobbie anytime**

### Option 3: Manual - Run Anytime

Simply **double-click:**
```
c:\Users\mradu\Desktop\dobbie\run_dobbie.bat
```

## 🔍 How It Works

- **run_dobbie.bat** → Starts Dobbie in background and opens browser
- **app.py** → Now auto-opens the browser window automatically
- **add_to_startup.bat** → Adds Dobbie to Windows startup

## ✅ After Setup

Your PC will:
1. Automatically start Dobbie when it boots
2. Open your default browser to http://localhost:5000
3. Show Dobbie interface ready to use
4. Keep running in the background

## 🛑 Stop Dobbie

To stop Dobbie:
- **Close the browser** OR
- **Press Ctrl+C** in the command window OR
- **Restart your PC**

## ❌ Remove from Startup

1. **Press `Win + R`** and type:
   ```
   shell:startup
   ```

2. **Delete the "Dobbie.lnk" shortcut**

3. **Done!** Dobbie will no longer auto-start

## 🔧 Troubleshooting

### Browser doesn't open
- Make sure you have a default browser set (Chrome, Edge, Firefox)
- Try double-clicking `run_dobbie.bat` instead

### Dobbie won't start
- Make sure Python is installed and in PATH
- Run from a normal command prompt (not admin)
- Check that the path `c:\Users\mradu\Desktop\dobbie` is correct

### Can't remove from startup
- Go to `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup`
- Find and delete "Dobbie.lnk" manually

## 📝 Files

- **run_dobbie.bat** - Start Dobbie (double-click anytime)
- **add_to_startup.bat** - Add to automatic startup
- **app.py** - Main Dobbie application (modified to auto-open browser)

---

**Your Dobbie is now ready to greet you every time you start your PC! ✨**
