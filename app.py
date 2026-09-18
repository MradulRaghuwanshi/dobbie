"""
DOBBIE - Your Magical Desktop Assistant
Web-based version using Flask
=======================================

Features:
  - Beautiful web-based UI
  - Text and voice commands
  - File access and management (configured folders + whole-profile fallback)
  - Email integration (Gmail, multiple accounts, ask for one by name)
  - App launching (config.json apps + Start Menu shortcut lookup for anything
    installed, e.g. Canva) and web searching
  - Direct CMD access ("cmd <command>" / "run cmd <command>")
  - Chrome opens with the Gmail account's own Chrome profile

Run: python app.py

SECURITY NOTE: this server can open programs, read your files, and run
CMD commands on your PC. It only accepts connections from your own machine
(127.0.0.1) - see restrict_to_localhost() below. Do not port-forward it or
expose it to your network.
"""

import difflib
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.parse
import webbrowser
import winreg
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory

try:
    import imaplib
    import email
    from email.header import decode_header
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

# Folders that are never worth walking into when searching for files/apps
SKIP_DIR_NAMES = {
    "appdata", "node_modules", ".git", "__pycache__",
    "system volume information", "$recycle.bin", "windows",
}


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    cfg["search_dirs"] = [os.path.expandvars(d) for d in cfg.get("search_dirs", [])]
    return cfg


class Dobbie:
    def __init__(self, cfg):
        self.cfg = cfg
        self.threshold = cfg.get("match_threshold", 0.7)

    # ------------------------------------------------------------------
    # Main dispatch
    # ------------------------------------------------------------------
    def handle(self, text: str) -> dict:
        """Main handler for commands. Returns dict with response and optional action."""
        raw = text.strip()
        low = raw.lower()

        # Easter egg
        if re.search(r"\bsocks?\b", low):
            return {
                "response": "Master gives Dobbie a sock! Dobbie is FREE! Dobbie is a free elf!",
                "status": "Dobbie is happy!"
            }

        # Conversation
        chat = self._conversation_reply(low)
        if chat:
            return {"response": chat, "status": "Ready for your next command."}

        # Direct CMD access
        cmd_text = self._match_cmd_command(raw)
        if cmd_text:
            return self.run_cmd(cmd_text)

        # Detect / list Chrome accounts
        if re.search(r"\b(detect|list|show|find)\s+chrome\s+(accounts?|profiles?)\b", low):
            return self.handle_detect_chrome_profiles()

        # Switch which Gmail/Chrome profile Dobbie uses
        account_name = self._match_switch_account(raw)
        if account_name:
            return self.set_chrome_account(account_name)

        # Email checking (optionally for a specific account: "check aarti emails")
        m = re.search(r"\b(check|read|show|get)\s+(my\s+)?(.*?)\s*emails?\b", low)
        if m:
            who = re.sub(r"'s$", "", m.group(3).strip())
            return self.check_emails(who if who else None)

        # Web search
        query = self._web_query(raw)
        if query:
            return self.search_web(query)

        # Open website
        m = re.match(r"^(open|launch|start)\s+(website|site)\s+(.+)$", raw, re.IGNORECASE)
        if m:
            return self.open_website(m.group(3).strip())

        # Open file
        file_to_open = self._open_file_query(raw)
        if file_to_open:
            return self.open_file(file_to_open)

        # Open app
        m = re.match(r"^(open|launch|start)\s+(.+)$", raw, re.IGNORECASE)
        if m:
            return self.open_app(m.group(2).strip())

        # Find file
        term = self._file_query(raw)
        if term:
            return self.find_file(term)

        return {
            "response": "Dobbie is sorry, master, Dobbie did not understand. Try 'open chrome', 'check emails', 'find file', 'cmd dir', or 'search web'.",
            "status": "Ready to try again."
        }

    def _conversation_reply(self, low: str):
        patterns = {
            r"\b(hello|hi|hey|good morning|good afternoon|good evening)\b":
                "Hello master! Dobbie is here and listening. Tell Dobbie what you need.",
            r"\b(how are you|how r u|are you okay)\b":
                "Dobbie is very happy to help, master. Dobbie is ready for apps, files, websites, and searches.",
            r"\b(thank you|thanks|good job|well done)\b":
                "Dobbie is honored, master. Give Dobbie another task whenever you wish.",
            r"\b(what can you do|help|commands|command list)\b":
                "Dobbie can open apps (even ones not in config.json), search the web, open websites, find files "
                "anywhere on your PC, check your emails, and run CMD commands. Try: open chrome, search web weather, "
                "find file resume, check aarti emails, cmd dir, use mradul chrome.",
            r"\b(who are you|your name)\b":
                "Dobbie is your magical desktop assistant, master. Dobbie helps you find things and open things quickly.",
        }

        for pattern, response in patterns.items():
            if re.search(pattern, low):
                return response
        return None

    def _web_query(self, text: str):
        patterns = [
            r"^(search|google|hunt)\s+(the\s+)?(web|internet)\s+(for\s+)?(.+)$",
            r"^(web\s+search|search\s+web|google)\s+(.+)$",
        ]
        for pattern in patterns:
            m = re.match(pattern, text, re.IGNORECASE)
            if m:
                return m.group(m.lastindex).strip()
        return None

    def _file_query(self, text: str):
        m = re.match(r"^(find|search|hunt)(\s+for)?(\s+the)?\s+file\s+(.+)$", text, re.IGNORECASE)
        if m:
            return m.group(4).strip()
        m = re.match(r"^(find|hunt)\s+(.+)$", text, re.IGNORECASE)
        return m.group(2).strip() if m else None

    def _open_file_query(self, text: str):
        patterns = [
            r"^(open|launch|start)\s+(the\s+)?file\s+(.+)$",
            r"^(open|launch|start)\s+(the\s+)?document\s+(.+)$",
        ]
        for pattern in patterns:
            m = re.match(pattern, text, re.IGNORECASE)
            if m:
                return m.group(m.lastindex).strip()
        return None

    def _match_cmd_command(self, raw: str):
        """Matches explicit CMD-execution phrasing only, so it never collides
        with 'open cmd' (which still just opens an interactive window)."""
        patterns = [
            r"^(?:run|execute)\s+cmd\s*:?\s+(.+)$",
            r"^cmd\s*:\s*(.+)$",
            r"^cmd\s+(.+)$",
            r"^terminal\s*:?\s+(.+)$",
            r"^shell\s*:?\s+(.+)$",
            r"^(?:run|execute)\s+command\s*:?\s+(.+)$",
        ]
        for p in patterns:
            m = re.match(p, raw, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return None

    def _match_switch_account(self, raw: str):
        patterns = [
            r"^open chrome as\s+(.+)$",
            r"^set (?:default )?chrome account (?:to\s+)?(.+)$",
            r"^(?:use|switch to|switch)\s+(.+?)\s+(?:chrome|gmail|account)$",
        ]
        for p in patterns:
            m = re.match(p, raw, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return None

    # ------------------------------------------------------------------
    # CMD access
    # ------------------------------------------------------------------
    def run_cmd(self, command: str) -> dict:
        if not self.cfg.get("cmd_access", True):
            return {
                "response": "CMD access is turned off in config.json ('cmd_access': false), master.",
                "status": "CMD access disabled"
            }
        try:
            result = subprocess.run(
                ["cmd", "/c", command],
                capture_output=True, text=True, timeout=30,
                cwd=os.environ.get("USERPROFILE"),
            )
            output = ((result.stdout or "") + (result.stderr or "")).strip()
            if not output:
                output = "(command finished with no output)"
            if len(output) > 4000:
                output = output[:4000] + "\n... (truncated)"
            return {
                "response": f"Dobbie ran that in CMD, master:\n\n{output}",
                "status": f"Command finished (exit code {result.returncode})"
            }
        except subprocess.TimeoutExpired:
            return {"response": "Dobbie's command took too long and was stopped (30s limit), master.", "status": "Command timed out"}
        except Exception as e:
            return {"response": f"Dobbie could not run that command, master: {e}", "status": "Command error"}

    # ------------------------------------------------------------------
    # Config persistence
    # ------------------------------------------------------------------
    def _save_config(self, updates: dict):
        """Persist a few keys back to config.json without clobbering
        the un-expanded (%USERPROFILE%-style) search_dirs on disk."""
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except Exception:
            raw = {}
        raw.update(updates)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(raw, f, indent=2)
        self.cfg.update(updates)

    # ------------------------------------------------------------------
    # Chrome profile / multi-account support
    # ------------------------------------------------------------------
    def _chrome_user_data_dir(self):
        local = os.environ.get("LOCALAPPDATA")
        if not local:
            return None
        path = os.path.join(local, "Google", "Chrome", "User Data")
        return path if os.path.isdir(path) else None

    def detect_chrome_profiles(self) -> dict:
        """Reads Chrome's own 'Local State' file to map each signed-in
        Gmail/Google account to its Chrome profile folder (e.g. 'Default',
        'Profile 1'). This is how Dobbie knows which Chrome window belongs
        to which of your two emails."""
        user_data = self._chrome_user_data_dir()
        if not user_data:
            return {}
        local_state_path = os.path.join(user_data, "Local State")
        if not os.path.isfile(local_state_path):
            return {}
        try:
            with open(local_state_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return {}
        info_cache = data.get("profile", {}).get("info_cache", {})
        mapping = {}
        for profile_dir, info in info_cache.items():
            acc_email = info.get("user_name") or info.get("gaia_name")
            if acc_email and "@" in acc_email:
                mapping[acc_email.lower()] = profile_dir
        return mapping

    def handle_detect_chrome_profiles(self) -> dict:
        mapping = self.detect_chrome_profiles()
        if not mapping:
            return {
                "response": "Dobbie looked in Chrome's settings but found no signed-in accounts, master. "
                             "Make sure you are signed into Chrome with both Gmail accounts first "
                             "(chrome://settings/people).",
                "status": "No Chrome profiles found"
            }
        lines = ["Dobbie found these Chrome accounts, master:"]
        for acc_email, profile_dir in mapping.items():
            lines.append(f"   - {acc_email}  ->  {profile_dir}")
        self._save_config({"chrome_profiles": mapping})
        lines.append("\nDobbie saved this mapping to config.json. Say 'use mradul chrome' or "
                      "'use aarti chrome' any time to switch which account Chrome opens and searches with.")
        return {"response": "\n".join(lines), "status": "Chrome profiles saved"}

    def _resolve_account_email(self, name: str):
        if not name:
            return None
        name = name.strip().strip('"').strip("'").lower()
        emails_cfg = self.cfg.get("emails", [])
        for acc in emails_cfg:
            if acc.get("email", "").lower() == name:
                return acc.get("email")
        for acc in emails_cfg:
            nick = (acc.get("name") or "").lower()
            local_part = acc.get("email", "").split("@")[0].lower()
            if name == nick or (nick and name in nick) or name == local_part or name in local_part:
                return acc.get("email")
        return None

    def set_chrome_account(self, name: str) -> dict:
        acc_email = self._resolve_account_email(name)
        if not acc_email:
            return {
                "response": f"Dobbie does not know an account called '{name}', master. "
                             "Add it to config.json under 'emails', or say 'detect chrome accounts' first.",
                "status": "Unknown account"
            }
        if acc_email.lower() not in {k.lower() for k in self.cfg.get("chrome_profiles", {})}:
            # try to auto-detect now in case it wasn't done yet
            mapping = self.detect_chrome_profiles()
            if mapping:
                self._save_config({"chrome_profiles": mapping})
        self._save_config({"default_email_account": acc_email})
        return {
            "response": f"Yes master! Dobbie will now open and search Chrome signed in as {acc_email}.",
            "status": f"Chrome account set to {acc_email}"
        }

    def _chrome_launch_args(self, extra_args=None):
        args = list(extra_args or [])
        default_email = self.cfg.get("default_email_account")
        profiles = self.cfg.get("chrome_profiles", {})
        profile_dir = None
        if default_email:
            profile_dir = profiles.get(default_email) or profiles.get(default_email.lower())
        if profile_dir:
            args.insert(0, f"--profile-directory={profile_dir}")
        return args

    # ------------------------------------------------------------------
    # App launching
    # ------------------------------------------------------------------
    def open_app(self, name: str) -> dict:
        apps = self.cfg.get("apps", {})
        app_name = name.lower().strip()
        target = apps.get(app_name)
        matched_key = app_name

        if not target:
            best, score = None, 0.0
            for key in apps:
                ratio = difflib.SequenceMatcher(None, app_name, key).ratio()
                if ratio > score:
                    best, score = key, ratio
            if best and score >= self.threshold:
                target = apps[best]
                matched_key = best

        extra_args = []
        if target and matched_key in ("chrome", "google chrome"):
            extra_args = self._chrome_launch_args()

        if not target:
            # NEW: fall back to a Start Menu / Desktop shortcut search so apps that
            # were never added to config.json (e.g. Canva) can still be opened.
            shortcut = self._find_start_menu_shortcut(app_name)
            if shortcut:
                try:
                    os.startfile(shortcut)
                    return {
                        "response": f"Yes master! Dobbie found {name} in your Start Menu and is opening it now!",
                        "status": f"Opening {name}...",
                        "action": {"type": "open_app", "app": name}
                    }
                except Exception as e:
                    return {
                        "response": f"Dobbie found a shortcut for '{name}', master, but Windows would not open it: {e}",
                        "status": "Failed to open app"
                    }
            return {
                "response": f"Dobbie could not find '{name}' in config.json or your Start Menu, master. "
                             f"Try 'cmd start {name}', or add it to config.json under 'apps'.",
                "status": "Unknown application"
            }

        success, error = self._launch_command(target, extra_args)
        if success:
            return {
                "response": f"Yes master! Dobbie is opening {name} right away!",
                "status": f"Opening {name}...",
                "action": {"type": "open_app", "app": name}
            }
        return {
            "response": f"Dobbie found '{name}', master, but Windows would not open it: {error}",
            "status": "Failed to open app"
        }

    def _find_start_menu_shortcut(self, name: str):
        """Fuzzy-searches Start Menu (all users + current user) and the Desktop
        for a shortcut matching `name`. This is how Dobbie can open apps like
        Canva that were installed normally but never added to config.json."""
        roots = []
        appdata = os.environ.get("APPDATA")
        programdata = os.environ.get("PROGRAMDATA")
        userprofile = os.environ.get("USERPROFILE")
        if appdata:
            roots.append(os.path.join(appdata, "Microsoft", "Windows", "Start Menu", "Programs"))
        if programdata:
            roots.append(os.path.join(programdata, "Microsoft", "Windows", "Start Menu", "Programs"))
        if userprofile:
            roots.append(os.path.join(userprofile, "Desktop"))

        name_low = name.lower()
        best, best_score = None, 0.0
        for root in roots:
            if not os.path.isdir(root):
                continue
            try:
                for dirpath, _dirnames, filenames in os.walk(root):
                    for fname in filenames:
                        if not fname.lower().endswith((".lnk", ".url")):
                            continue
                        stem = os.path.splitext(fname)[0].lower()
                        ratio = difflib.SequenceMatcher(None, name_low, stem).ratio()
                        if name_low in stem:
                            ratio = max(ratio, 0.9)
                        if ratio > best_score:
                            best_score, best = ratio, os.path.join(dirpath, fname)
            except (PermissionError, OSError):
                continue

        if best and best_score >= max(self.threshold, 0.55):
            return best
        return None

    def search_web(self, query: str) -> dict:
        engine = self.cfg.get("web_search_engine", "https://www.google.com/search?q={query}")
        encoded = urllib.parse.quote_plus(query)
        url = engine.format(query=encoded)

        try:
            chrome_target = self.cfg.get("apps", {}).get("chrome", "chrome")
            success, error = self._launch_command(chrome_target, self._chrome_launch_args([url]))
            if success:
                return {
                    "response": f"Dobbie is searching the web for '{query}', master!",
                    "status": "Searching...",
                    "action": {"type": "open_browser", "url": url}
                }
            else:
                return {
                    "response": f"Dobbie tried to search for '{query}' but could not open Chrome. Try 'open chrome' first.",
                    "status": "Failed - Chrome not found"
                }
        except Exception as e:
            return {
                "response": f"Dobbie encountered an error searching: {str(e)}",
                "status": "Search error"
            }

    def open_website(self, target: str) -> dict:
        url = target.strip()
        if not re.match(r"^https?://", url):
            url = "https://" + url

        chrome_target = self.cfg.get("apps", {}).get("chrome", "chrome")
        success, error = self._launch_command(chrome_target, self._chrome_launch_args([url]))
        if success:
            return {
                "response": f"Dobbie is opening {url}, master!",
                "status": "Opening website...",
                "action": {"type": "open_browser", "url": url}
            }
        return {
            "response": f"Dobbie tried to open {url}, master, but Windows would not open the browser.",
            "status": "Failed to open website"
        }

    def _launch_command(self, command: str, args=None):
        args = args or []
        command = (command or "").strip()
        if not command:
            return False, "empty command"

        executable = self._resolve_executable(command)
        if executable:
            try:
                subprocess.Popen([executable, *args])
                return True, None
            except Exception as first_error:
                try:
                    subprocess.Popen(
                        ["cmd", "/c", "start", "", executable, *args],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    return True, None
                except Exception as second_error:
                    return False, f"{first_error}; {second_error}"

        if os.path.sep in command:
            return False, f"path does not exist: {command}"

        try:
            subprocess.Popen(
                ["cmd", "/c", "start", "", command, *args],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True, None
        except Exception as e:
            return False, str(e)

    def _resolve_executable(self, command: str):
        expanded = os.path.expandvars(command).strip().strip('"')
        if not expanded:
            return None

        if os.path.isfile(expanded):
            return expanded

        if os.path.isfile(expanded + ".exe"):
            return expanded + ".exe"

        found = shutil.which(expanded)
        if found:
            return found

        if not expanded.lower().endswith(".exe"):
            found = shutil.which(f"{expanded}.exe")
            if found:
                return found

        registry_path = self._app_path_from_registry(expanded)
        if registry_path:
            return registry_path

        known_locations = [
            os.environ.get("LOCALAPPDATA"),
            os.environ.get("PROGRAMFILES"),
            os.environ.get("PROGRAMFILES(X86)"),
            os.environ.get("USERPROFILE"),
        ]
        for base in filter(None, known_locations):
            for candidate in [
                os.path.join(base, expanded),
                os.path.join(base, expanded + ".exe"),
                os.path.join(base, "Microsoft VS Code", "Code.exe"),
                os.path.join(base, "Google", "Chrome", "Application", "chrome.exe"),
            ]:
                if os.path.isfile(candidate):
                    return candidate

        return None

    def _app_path_from_registry(self, command: str):
        base = os.path.basename(command)
        names = [base] if base.lower().endswith(".exe") else [base, f"{base}.exe"]
        hives = [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]
        roots = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths",
        ]

        for hive in hives:
            for root in roots:
                for name in names:
                    try:
                        with winreg.OpenKey(hive, rf"{root}\{name}") as key:
                            path, _kind = winreg.QueryValueEx(key, "")
                        path = os.path.expandvars(path).strip().strip('"')
                        if os.path.isfile(path):
                            return path
                    except OSError:
                        continue
        return None

    # ------------------------------------------------------------------
    # File search (configured folders, with a whole-profile fallback)
    # ------------------------------------------------------------------
    def find_file(self, term: str) -> dict:
        results = self._find_matches(term)

        if not results:
            return {
                "response": f"Dobbie searched everywhere it knows, master, but found no file matching '{term}'.",
                "status": "Search complete - no files found"
            }

        results.sort(key=lambda x: x[0], reverse=True)
        lines = [f"Dobbie found {len(results)} match(es) for '{term}', master! Top results:"]
        for ratio, path in results[:8]:
            lines.append(f"   - ({int(ratio * 100)}%) {path}")

        return {
            "response": "\n".join(lines),
            "status": f"Found {len(results)} file(s)"
        }

    def open_file(self, term: str) -> dict:
        results = self._find_matches(term)

        if not results:
            return {
                "response": f"Dobbie could not find a file to open for '{term}', master.",
                "status": "File not found"
            }

        score, path = results[0]
        try:
            os.startfile(path)
            return {
                "response": f"Dobbie found the best match and opened it, master: {os.path.basename(path)} ({int(score * 100)}%).",
                "status": "File opened",
                "action": {"type": "open_file", "path": path}
            }
        except Exception as e:
            return {
                "response": f"Dobbie found {os.path.basename(path)}, master, but Windows would not open it: {e}",
                "status": "Failed to open file"
            }

    def _scan_dir_for_matches(self, root_dir: str, term_low: str, time_budget_seconds=None):
        found = []
        if not os.path.isdir(root_dir):
            return found
        deadline = time.time() + time_budget_seconds if time_budget_seconds else None
        try:
            for dirpath, dirnames, filenames in os.walk(root_dir):
                dirnames[:] = [d for d in dirnames if d.lower() not in SKIP_DIR_NAMES]
                for fname in filenames:
                    name_only = os.path.splitext(fname)[0].lower()
                    ratio = difflib.SequenceMatcher(None, term_low, name_only).ratio()
                    if term_low in name_only:
                        ratio = max(ratio, 0.85)
                    if ratio >= self.threshold:
                        found.append((ratio, os.path.join(dirpath, fname)))
                if deadline and time.time() > deadline:
                    break
        except (PermissionError, OSError):
            pass
        return found

    def _find_matches(self, term: str):
        term_low = term.lower()
        results = []
        for root_dir in self.cfg.get("search_dirs", []):
            results.extend(self._scan_dir_for_matches(root_dir, term_low))

        # NEW: if the configured folders didn't have it, widen the search to
        # the whole user profile (Dobbie's "access to my other files" request)
        if not results:
            userprofile = os.environ.get("USERPROFILE")
            if userprofile:
                results.extend(self._scan_dir_for_matches(userprofile, term_low, time_budget_seconds=15))

        results.sort(key=lambda x: x[0], reverse=True)
        return results

    # ------------------------------------------------------------------
    # Email (multiple Gmail accounts)
    # ------------------------------------------------------------------
    def check_emails(self, who: str = None) -> dict:
        """Check emails from configured Gmail accounts. `who` can be a
        nickname ('mradul', 'aarti') or a full email address to check just
        one account; leave it None to check all configured accounts."""
        emails_config = self.cfg.get("emails", [])

        if not emails_config:
            return {
                "response": "Dobbie has no email accounts configured, master. Add them to config.json with your app passwords.",
                "status": "Email not configured"
            }

        if who:
            target_email = self._resolve_account_email(who)
            if not target_email:
                return {
                    "response": f"Dobbie does not know an email account for '{who}', master.",
                    "status": "Unknown account"
                }
            emails_config = [a for a in emails_config if a.get("email", "").lower() == target_email.lower()]

        has_passwords = any(
            email_account.get("app_password") and
            email_account.get("app_password") != "YOUR_APP_PASSWORD_HERE"
            for email_account in emails_config
        )

        if not has_passwords:
            return {
                "response": "Dobbie needs a Gmail app password, master. Please set it in config.json. See SETUP.md for instructions.",
                "status": "Email passwords not configured"
            }

        if not EMAIL_AVAILABLE:
            return {
                "response": "Dobbie's email module is not available on this Python install.",
                "status": "Email module not available"
            }

        all_emails = []
        for email_account in emails_config:
            email_addr = email_account.get("email", "")
            app_password = email_account.get("app_password", "")

            if not email_addr or app_password == "YOUR_APP_PASSWORD_HERE":
                continue

            try:
                emails = self._fetch_gmail(email_addr, app_password)
                for e in emails:
                    e["account"] = email_addr
                all_emails.extend(emails)
            except Exception as e:
                return {
                    "response": f"Dobbie could not access {email_addr}: {str(e)}",
                    "status": "Email error"
                }

        if all_emails:
            response_text = f"Dobbie found {len(all_emails)} email(s), master:\n\n"
            for i, email_data in enumerate(all_emails[:5], 1):
                response_text += f"{i}. [{email_data['account']}] From: {email_data['from']}\n"
                response_text += f"   Subject: {email_data['subject']}\n\n"

            return {
                "response": response_text,
                "status": "Emails retrieved",
                "action": {"type": "check_email", "emails": all_emails[:5]}
            }
        else:
            return {
                "response": "Dobbie found no new emails, master.",
                "status": "No emails"
            }

    def _fetch_gmail(self, email_address: str, app_password: str) -> list:
        """Fetch emails from Gmail using IMAP."""
        try:
            imap = imaplib.IMAP4_SSL("imap.gmail.com", timeout=10)
            imap.login(email_address, app_password)
            imap.select("INBOX")

            status, messages = imap.search(None, "UNSEEN")
            email_ids = messages[0].split()[:5]  # Get latest 5 emails

            emails = []
            for email_id in email_ids:
                status, msg_data = imap.fetch(email_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        subject = decode_header(msg["Subject"])[0][0] if msg["Subject"] else "No Subject"
                        if isinstance(subject, bytes):
                            subject = subject.decode()

                        from_addr = msg.get("From", "Unknown")

                        emails.append({
                            "from": from_addr,
                            "subject": str(subject),
                            "preview": "Email message"
                        })

            imap.close()
            imap.logout()
            return emails
        except Exception as e:
            raise Exception(f"Gmail IMAP error: {str(e)}")


# ==========================================================================
# Flask App
# ==========================================================================
app = Flask(__name__, static_folder=".", template_folder=".")

cfg = load_config()
dobbie = Dobbie(cfg)


@app.before_request
def restrict_to_localhost():
    """Dobbie can run CMD commands and open your files, so it must never
    accept a request from anywhere but your own PC - not even another
    website open in your browser (which is why this app doesn't use
    flask-cors: everything is served same-origin, so no cross-site page
    can call these endpoints)."""
    if request.remote_addr not in ("127.0.0.1", "::1"):
        return jsonify({"error": "Dobbie only accepts connections from this computer."}), 403


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/styles.css")
def styles():
    return send_from_directory(".", "styles.css")


@app.route("/script.js")
def script():
    return send_from_directory(".", "script.js")


@app.route("/assets/<path:filename>")
def assets(filename):
    return send_from_directory("assets", filename)


@app.route("/api/command", methods=["POST"])
def handle_command():
    data = request.json
    command = data.get("command", "").strip()

    if not command:
        return jsonify({"success": False, "error": "Empty command"}), 400

    result = dobbie.handle(command)
    return jsonify({"success": True, **result})


@app.route("/api/open-file", methods=["POST"])
def open_file_endpoint():
    data = request.json
    path = data.get("path", "")
    try:
        os.startfile(path)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/open-app", methods=["POST"])
def open_app_endpoint():
    data = request.json
    app_name = data.get("app", "")
    result = dobbie.open_app(app_name)
    return jsonify({"success": True, **result})


if __name__ == "__main__":
    print("Dobbie is starting, master...")
    print("Opening at http://localhost:5000")

    def open_browser():
        time.sleep(2)  # Wait for server to fully start
        try:
            webbrowser.open("http://localhost:5000", new=1)
            print("Opening Dobbie in your browser...")
        except Exception as e:
            print(f"Could not open browser: {e}")

    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()

    app.run(debug=False, host="127.0.0.1", port=5000)
