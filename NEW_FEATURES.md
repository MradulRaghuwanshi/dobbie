# What's new in this version

## 1. Theme now matches your mockup exactly
`index.html` / `styles.css` now use the actual castle banner and Dobby
portrait from your reference image (saved under `assets/`) instead of the
CSS-drawn castle and hand-drawn SVG elf. Everything else (layout, colors,
buttons, message box) was already matching your mockup, so nothing else
changed visually.

## 2. Real CMD access
Say any of these and Dobbie runs it in CMD and shows you the output:

```
cmd dir
cmd ipconfig
run cmd tasklist
execute command echo hello
terminal dir /b
```

This is on by default. Turn it off by setting `"cmd_access": false` in
`config.json`. Commands time out after 30 seconds and output is capped so
the chat doesn't get flooded.

## 3. Opening apps that aren't in config.json (e.g. Canva)
If an app isn't in `config.json`'s `"apps"` list, Dobbie now searches your
Start Menu and Desktop shortcuts for a match before giving up. This is how
`open canva` works even though Canva was never added to the config -
Windows already made a shortcut for it when it was installed, and Dobbie
now finds it. If it still can't find it, you can always fall back to
`cmd start canva`.

## 4. File search now covers your whole user folder
`find file` / `open file` first checks the folders listed in
`search_dirs`. If nothing turns up there, Dobbie now widens the search to
your entire user profile (`C:\Users\mradu`) for up to 15 seconds, so files
outside Desktop/Documents/Downloads/etc. are still reachable.

## 5. Two Gmail accounts, and asking for one by name
```
check emails            -> both accounts
check mradul emails     -> just mradulraghuwanshi@gmail.com
check aarti emails      -> just aartiraghuwanshi01@gmail.com
```
You still need to give each account a Gmail **App Password** in
`config.json` under `"emails"` - that part hasn't changed, see SETUP.md.
Google account passwords can't be generated for you automatically; you
have to create them once in your Google Account security settings.

## 6. "Open Chrome logged into my account" + search in that Chrome
This is the part that needed real detective work. Chrome doesn't expose a
simple "open as this email" switch - it opens whichever **profile folder**
(`Default`, `Profile 1`, etc.) you tell it to, and each profile folder
happens to be signed into one of your Google accounts.

So Dobbie now:
1. Reads Chrome's own settings file to see which profile folder belongs to
   which signed-in Google account.
2. Remembers that mapping in `config.json` under `"chrome_profiles"`.
3. Passes `--profile-directory=...` whenever it opens Chrome, searches the
   web, or opens a website - so it's always the right account's Chrome
   window.

**One-time setup on your PC** (you must run this once, Claude can't do it
for you since it needs your actual Chrome data):
1. Make sure you're signed into Chrome with both Gmail accounts at least
   once (`chrome://settings/people`).
2. Start Dobbie and type: `detect chrome accounts`
   Dobbie will find both profiles and save them automatically.
3. From then on, switch which account Chrome/search uses with:
   ```
   use mradul chrome
   use aarti chrome
   ```
   Whichever one you picked stays the default until you switch again -
   including for `open chrome` and `search web ...`.

## 7. Security fix (please read)
The old version used `Flask-CORS` with no restrictions, which meant **any
website open in your browser could have sent commands to Dobbie** (open
apps, read files) without your knowledge, because Dobbie's server accepted
requests from any origin. Since Dobbie can now also run raw CMD commands,
this was tightened:

- `flask-cors` was removed entirely (not needed - the page and the API are
  served from the same origin).
- The server now rejects any request that isn't coming from your own PC
  (`127.0.0.1`).

Keep running Dobbie only on `localhost` (don't port-forward it or expose
port 5000 to your network) and this stays safe.
