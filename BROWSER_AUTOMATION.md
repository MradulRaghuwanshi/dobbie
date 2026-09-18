Browser automation for ChatGPT
=============================

This repository includes a small Selenium script to open https://chat.openai.com/ and send a query from your local machine.

Files added:
- `open_chatgpt.py`: Selenium script that opens ChatGPT and types/sends a query.

Install
-------
Add the new dependencies and install them in your virtual environment:

```powershell
python -m pip install -r requirements.txt
```

Usage
-----
1. Recommended: use your Chrome profile so the script can reuse an existing logged-in session. Find your Chrome user data directory. Example on Windows:

   `C:\Users\<you>\AppData\Local\Google\Chrome\User Data`

2. Run the script with your query:

```powershell
python open_chatgpt.py "Give me a short summary of photosynthesis." --profile "C:\Users\<you>\AppData\Local\Google\Chrome\User Data"
```

Notes & caveats
---------------
- If you don't pass `--profile`, the browser will open a fresh profile; you'll need to sign in manually.
- This automation is brittle: site UI changes can break selectors. Use this as a convenience tool only.
- Respect the site's terms of service. This script does not bypass authentication or access controls.

Troubleshooting
---------------
- If the script cannot find the input field, try logging in manually in the opened browser and re-run.
- If Chrome/driver versions mismatch, run `python -m pip install -U webdriver-manager selenium` and retry.
