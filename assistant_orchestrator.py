"""Orchestrator to handle natural-language commands and open local apps.

Usage:
  python assistant_orchestrator.py "Open calculator"

Behavior:
- If `OPENAI_API_KEY` is set in the environment, the script will call the OpenAI API
  to extract the intended application name from the user's natural language.
- If no API key is present, the script uses a simple rule-based fallback to extract
  the app name.
- The script attempts to locate an executable matching the app name using `shutil.which`
  and by scanning common installation folders on Windows.
"""
import os
import sys
import argparse
import shutil
import subprocess
from pathlib import Path
import time
try:
    import winreg
except Exception:
    winreg = None


def parse_intent_llm(query: str) -> str:
    """Use OpenAI (if configured) to extract the app name to open.

    Returns a short app name string, or empty string on failure.
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return ''
    try:
        import openai
        openai.api_key = api_key
        model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        prompt = (
            "Extract a short, single-line application name from the user's instruction."
            " Only return the app name (no extra text). Examples: 'calculator', 'notepad', 'chrome'."
        )
        resp = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": query},
            ],
            max_tokens=32,
            temperature=0,
        )
        app_name = resp['choices'][0]['message']['content'].strip().strip('"').strip("'")
        return app_name
    except Exception:
        return ''


def parse_intent_fallback(query: str) -> str:
    """Simple rule-based extractor for app names.

    Looks for verbs like open/launch/start followed by the app name.
    """
    q = query.lower()
    for token in ('open', 'launch', 'start', 'run'):
        if token + ' ' in q:
            part = q.split(token + ' ', 1)[1]
            # take first few words
            app = part.strip().split(' for ')[0].split(' with ')[0].split()[0:3]
            return ' '.join(app).strip()
    # if no verb present, assume whole query is app name
    return q.strip()


def find_executable_by_name(name: str):
    """Try several strategies to locate an executable by name on Windows.

    Returns path to executable or None.
    """
    if not name:
        return None

    # 1) try shutil.which (search PATH)
    maybe = shutil.which(name)
    if maybe:
        return maybe

    # 2) common executable suffixes to try
    exts = ['.exe', '.bat', '.cmd', '.lnk']
    candidates = []

    # normalize name tokens
    name_tokens = [t for t in name.replace('-', ' ').split() if t]

    # 3) search common installation directories (Windows-focused)
    base_dirs = [
        os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files')),
        os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)')),
        os.path.expanduser('~\\AppData\\Local\\Programs'),
        os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32'),
    ]

    lowered = ' '.join(name_tokens).lower()
    for base in base_dirs:
        if not os.path.isdir(base):
            continue
        # walk shallowly: only top 2 levels to limit time
        try:
            for entry in os.scandir(base):
                if entry.is_file():
                    nm = entry.name.lower()
                    if lowered in nm:
                        candidates.append(entry.path)
                elif entry.is_dir():
                    # check for exe in this dir
                    try:
                        for sub in os.scandir(entry.path):
                            if sub.is_file():
                                nm = sub.name.lower()
                                if lowered in nm and os.path.splitext(nm)[1] in exts:
                                    candidates.append(sub.path)
                    except PermissionError:
                        continue
        except PermissionError:
            continue

    # 4) last-resort: try appending common exts and searching PATH
    for ext in exts:
        maybe = shutil.which(name + ext)
        if maybe:
            return maybe

    # return the first candidate if any
    if candidates:
        return candidates[0]

    return None


def scan_start_menu(name: str):
    """Scan Start Menu shortcuts for a matching name. Return path to shortcut or exe.

    Returns: path or None
    """
    if not sys.platform.startswith('win'):
        return None
    lowered = name.lower()
    candidates = []
    start_paths = []
    program_data = os.environ.get('ProgramData')
    appdata = os.environ.get('APPDATA')
    if program_data:
        start_paths.append(os.path.join(program_data, 'Microsoft', 'Windows', 'Start Menu', 'Programs'))
    if appdata:
        start_paths.append(os.path.join(appdata, 'Microsoft', 'Windows', 'Start Menu', 'Programs'))

    exts = ('.lnk', '.url', '.exe', '.bat', '.cmd')
    for sp in start_paths:
        if not os.path.isdir(sp):
            continue
        for root, dirs, files in os.walk(sp):
            # shallow walk: skip deep recursion
            for f in files:
                fn = f.lower()
                if lowered in fn:
                    full = os.path.join(root, f)
                    candidates.append(full)
            # don't go deeper than 3 levels
            if root.count(os.sep) - sp.count(os.sep) > 3:
                del dirs[:]

    return candidates[0] if candidates else None


def find_in_registry(name: str):
    """Search uninstall registry keys for an app matching `name` and return an executable path if found."""
    if not winreg:
        return None
    name_l = name.lower()
    roots = [(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
             (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
             (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall")]

    for root, sub in roots:
        try:
            with winreg.OpenKey(root, sub) as k:
                for i in range(0, winreg.QueryInfoKey(k)[0]):
                    try:
                        sk = winreg.EnumKey(k, i)
                        with winreg.OpenKey(k, sk) as skey:
                            try:
                                display = winreg.QueryValueEx(skey, 'DisplayName')[0]
                            except Exception:
                                display = ''
                            if not display:
                                continue
                            if name_l in display.lower():
                                # try to read DisplayIcon or InstallLocation
                                try:
                                    icon = winreg.QueryValueEx(skey, 'DisplayIcon')[0]
                                    if icon and os.path.exists(icon):
                                        return icon
                                except Exception:
                                    pass
                                try:
                                    inst = winreg.QueryValueEx(skey, 'InstallLocation')[0]
                                    if inst:
                                        # try to find exe inside install location
                                        for fname in os.listdir(inst):
                                            if fname.lower().endswith(('.exe', '.bat', '.cmd')) and name_l in fname.lower():
                                                return os.path.join(inst, fname)
                                except Exception:
                                    pass
                    except OSError:
                        break
        except FileNotFoundError:
            continue
    return None


def open_path(path: str):
    """Open the given path using the OS default mechanism.

    On Windows, `os.startfile` is used.
    """
    if not path:
        return False
    try:
        if sys.platform.startswith('win'):
            os.startfile(path)
            return True
        else:
            subprocess.Popen([path])
            return True
    except Exception:
        try:
            # fallback to using shell start on Windows
            if sys.platform.startswith('win'):
                subprocess.Popen(['cmd', '/c', 'start', '""', path], shell=False)
                return True
        except Exception:
            return False


def main():
    parser = argparse.ArgumentParser(description='Assistant orchestrator to open local applications')
    parser.add_argument('command', nargs='+', help='Natural-language command, e.g. "Open calculator"')
    parser.add_argument('--no-llm', action='store_true', help='Disable OpenAI LLM parsing even if API key present')
    args = parser.parse_args()

    query = ' '.join(args.command).strip()
    app_name = ''
    if not args.no_llm and os.getenv('OPENAI_API_KEY'):
        app_name = parse_intent_llm(query)

    if not app_name:
        app_name = parse_intent_fallback(query)

    print(f'Interpreted app name: "{app_name}"')

    # Try direct PATH/ProgramFiles scan
    path = find_executable_by_name(app_name)
    # Try Start Menu shortcuts
    if not path and sys.platform.startswith('win'):
        sm = scan_start_menu(app_name)
        if sm:
            path = sm
    # Try registry lookup
    if not path and sys.platform.startswith('win'):
        reg = find_in_registry(app_name)
        if reg:
            path = reg
    if path:
        print(f'Found: {path}\nAttempting to open...')
        ok = open_path(path)
        if ok:
            print('Opened successfully.')
        else:
            print('Failed to open the application programmatically.')
    else:
        print('Application not found on this machine.')


if __name__ == '__main__':
    main()
