"""
DOBBIE - Your Magical Desktop Assistant
=======================================
A wizard-school-inspired desktop assistant for Windows.

Features:
  - Greets you when it opens
  - Text and optional voice commands
  - "open <app>" -> launches an application
  - "find file <name>" -> fuzzy-searches your files
  - "search web <query>" -> opens Chrome and searches Google
  - Say/type "socks" -> Dobbie's happy easter egg

Run: python main.py
"""

import difflib
import json
import math
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import tkinter as tk
import urllib.parse
import webbrowser
import winreg
from argparse import ArgumentParser
from datetime import datetime
from tkinter import scrolledtext

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

try:
    import speech_recognition as sr
    STT_AVAILABLE = True
except ImportError:
    STT_AVAILABLE = False

try:
    import imaplib
    import email
    from email.header import decode_header
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False


CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    cfg["search_dirs"] = [os.path.expandvars(d) for d in cfg.get("search_dirs", [])]
    return cfg


BG_DARK = "#0b1a14"
PANEL_BG = "#12281d"
PARCHMENT = "#f4ebd1"
GOLD = "#d9b75b"
MAROON = "#6d0f13"
SLYTHERIN_GREEN = "#1f3d2c"
INK = "#2b1c12"
BRONZE = "#8a5a2a"
STONE = "#24382d"
MIST = "#7e8b7a"
MOON = "#f0e4ba"
FIRE = "#a7571d"
FONT_TITLE = ("Papyrus", 30, "bold") if sys.platform == "win32" else ("Georgia", 30, "bold")
FONT_BODY = ("Georgia", 11)
FONT_INPUT = ("Georgia", 12)


class Dobbie:
    def __init__(self, cfg):
        self.cfg = cfg
        self.threshold = cfg.get("match_threshold", 0.7)

    def handle(self, text: str) -> str:
        raw = text.strip()
        low = raw.lower()

        if re.search(r"\bsocks?\b", low):
            return "Master gives Dobbie a sock! Dobbie is FREE! Dobbie is a free elf!"

        chat = self._conversation_reply(low)
        if chat:
            return chat

        # Email checking
        if re.search(r"\b(check|read|show|get)\s+(my\s+)?emails?\b", low):
            return self.check_emails()

        query = self._web_query(raw)
        if query:
            return self.search_web(query)

        m = re.match(r"^(open|launch|start)\s+(website|site)\s+(.+)$", raw, re.IGNORECASE)
        if m:
            return self.open_website(m.group(3).strip())

        file_to_open = self._open_file_query(raw)
        if file_to_open:
            return self.open_file(file_to_open)

        m = re.match(r"^(open|launch|start)\s+(.+)$", raw, re.IGNORECASE)
        if m:
            return self.open_app(m.group(2).strip())

        term = self._file_query(raw)
        if term:
            return self.find_file(term)

        return (
            "Dobbie is sorry, master, Dobbie did not understand. "
            "Try 'open <app>', 'find file <name>', 'check emails', or 'search web <query>'."
        )

    def _conversation_reply(self, low: str):
        if re.search(r"\b(hello|hi|hey|good morning|good afternoon|good evening)\b", low):
            return "Hello master! Dobbie is here and listening. Tell Dobbie what you need."
        if re.search(r"\b(how are you|how r u|are you okay)\b", low):
            return "Dobbie is very happy to help, master. Dobbie is ready for apps, files, websites, and searches."
        if re.search(r"\b(thank you|thanks|good job|well done)\b", low):
            return "Dobbie is honored, master. Give Dobbie another task whenever you wish."
        if re.search(r"\b(what can you do|help|commands|command list)\b", low):
            return (
                "Dobbie can open apps, search the web, open websites, find files, and open the best matching file. "
                "You can say open chrome, search web weather today, find file resume, or open file resume."
            )
        if re.search(r"\b(who are you|your name)\b", low):
            return "Dobbie is your magical desktop assistant, master. Dobbie helps you find things and open things quickly."
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

    def open_app(self, name: str) -> str:
        apps = self.cfg.get("apps", {})
        app_name = name.lower()
        target = apps.get(app_name)
        if not target:
            best, score = None, 0.0
            for key in apps:
                ratio = difflib.SequenceMatcher(None, app_name, key).ratio()
                if ratio > score:
                    best, score = key, ratio
            if best and score >= self.threshold:
                target = apps[best]
                name = best
        if not target:
            return (
                f"Dobbie does not know an application called '{name}', master. "
                'Add it to config.json under "apps".'
            )
        success, error = self._launch_command(target)
        if success:
            return f"Yes master! Dobbie is opening {name} right away!"
        return f"Dobbie found '{name}', master, but Windows would not open it: {error}"

    def search_web(self, query: str) -> str:
        engine = self.cfg.get("web_search_engine", "https://www.google.com/search?q={query}")
        encoded = urllib.parse.quote_plus(query)
        if self._open_url(engine.format(query=encoded)):
            return f"Dobbie is searching the web for '{query}', master!"
        return "Dobbie tried to search the web, master, but Windows would not open the browser."

    def open_website(self, target: str) -> str:
        url = target.strip()
        if not re.match(r"^https?://", url):
            url = "https://" + url
        if self._open_url(url):
            return f"Dobbie is opening {url}, master!"
        return f"Dobbie tried to open {url}, master, but Windows would not open the browser."

    def _open_url(self, url: str):
        browser = self.cfg.get("browser", "").strip().lower()
        apps = self.cfg.get("apps", {})
        browser_cmd = apps.get(browser, browser)
        if browser_cmd:
            success, _error = self._launch_command(browser_cmd, [url])
            if success:
                return True
        return webbrowser.open(url)

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
                os.path.join(base, "Google", "Chrome", "Application", "chrome.exe"),
                os.path.join(base, "Microsoft", "Edge", "Application", "msedge.exe"),
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

    def find_file(self, term: str):
        results = self._find_matches(term)

        if not results:
            return f"Dobbie searched the known folders, master, but found no file matching '{term}'."

        results.sort(key=lambda x: x[0], reverse=True)
        lines = [f"Dobbie found {len(results)} match(es) for '{term}', master! Top results:"]
        for ratio, path in results[:8]:
            lines.append(f"   - ({int(ratio * 100)}%) {path}")
        return "\n".join(lines)

    def open_file(self, term: str):
        results = self._find_matches(term)
        if not results:
            return f"Dobbie could not find a file to open for '{term}', master."

        score, path = results[0]
        try:
            os.startfile(path)
            return f"Dobbie found the best match and opened it, master: {os.path.basename(path)} ({int(score * 100)}%)."
        except Exception as e:
            return f"Dobbie found {os.path.basename(path)}, master, but Windows would not open it: {e}"

    def _find_matches(self, term: str):
        results = []
        term_low = term.lower()
        for root_dir in self.cfg.get("search_dirs", []):
            if not os.path.isdir(root_dir):
                continue
            for dirpath, dirnames, filenames in os.walk(root_dir):
                dirnames[:] = [
                    d for d in dirnames
                    if d.lower() not in {"appdata", "node_modules", ".git", "__pycache__"}
                ]
                for fname in filenames:
                    name_only = os.path.splitext(fname)[0].lower()
                    ratio = difflib.SequenceMatcher(None, term_low, name_only).ratio()
                    if term_low in name_only:
                        ratio = max(ratio, 0.85)
                    if ratio >= self.threshold:
                        results.append((ratio, os.path.join(dirpath, fname)))
        results.sort(key=lambda x: x[0], reverse=True)
        return results

    def check_emails(self) -> str:
        """Check emails from configured Gmail accounts."""
        emails_config = self.cfg.get("emails", [])
        
        if not emails_config:
            return "Dobbie has no email accounts configured, master. Add them to config.json with your app passwords."
        
        has_passwords = any(
            email_account.get("app_password") and 
            email_account.get("app_password") != "YOUR_APP_PASSWORD_HERE"
            for email_account in emails_config
        )
        
        if not has_passwords:
            return "Dobbie needs Gmail app passwords, master. Please set them in config.json. See SETUP.md for instructions."

        if not EMAIL_AVAILABLE:
            return "Dobbie's email module is not available."

        all_emails = []
        for email_account in emails_config:
            email_addr = email_account.get("email", "")
            app_password = email_account.get("app_password", "")
            
            if not email_addr or app_password == "YOUR_APP_PASSWORD_HERE":
                continue
                
            try:
                emails = self._fetch_gmail(email_addr, app_password)
                all_emails.extend(emails)
            except Exception as e:
                return f"Dobbie could not access {email_addr}: {str(e)}"

        if all_emails:
            response_text = f"Dobbie found {len(all_emails)} email(s), master:\n\n"
            for i, email_data in enumerate(all_emails[:5], 1):
                response_text += f"{i}. From: {email_data['from']}\n"
                response_text += f"   Subject: {email_data['subject']}\n\n"
            return response_text
        else:
            return "Dobbie found no new emails, master."

    def _fetch_gmail(self, email_address: str, app_password: str) -> list:
        """Fetch emails from Gmail using IMAP."""
        try:
            imap = imaplib.IMAP4_SSL("imap.gmail.com", timeout=10)
            imap.login(email_address, app_password)
            imap.select("INBOX")

            status, messages = imap.search(None, "UNSEEN")
            email_ids = messages[0].split()[:5]

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


class DobbieApp:
    def __init__(self, root):
        self.root = root
        self.cfg = load_config()
        self.brain = Dobbie(self.cfg)
        self.speech_queue = queue.Queue()
        self.recognizer = sr.Recognizer() if STT_AVAILABLE else None
        if TTS_AVAILABLE:
            threading.Thread(target=self._speech_worker, daemon=True).start()
        self._build_ui()
        self._greet()

    def _build_ui(self):
        width = int(self.cfg.get("window_width", 900))
        height = int(self.cfg.get("window_height", 820))
        min_width = max(720, min(width, 900))
        min_height = max(620, min(height, 760))

        self.root.title("Dobbie - Your Magical Assistant")
        self.root.configure(bg="#050b0d")
        self.root.geometry(f"{width}x{height}")
        self.root.minsize(min_width, min_height)
        self.root.attributes("-topmost", bool(self.cfg.get("always_on_top", False)))

        shell = tk.Frame(self.root, bg="#2a1c12")
        shell.pack(fill="both", expand=True, padx=18, pady=18)

        self.ambient_canvas = tk.Canvas(shell, height=190, bg="#050b0d", bd=0, highlightthickness=0)
        self.ambient_canvas.pack(fill="x", padx=0, pady=0)
        self._draw_castle_night_scene(self.ambient_canvas)
        self._start_ambient_animation()

        header_outer = tk.Frame(shell, bg="#5e3a1d", padx=4, pady=4)
        header_outer.pack(fill="x", pady=(0, 10))
        header = tk.Frame(header_outer, bg="#d6b37a", bd=0, highlightthickness=2, highlightbackground="#8b5b2b")
        header.pack(fill="x")

        portrait = tk.Canvas(header, width=182, height=160, bg="#d8c7a5", bd=0, highlightthickness=0)
        portrait.pack(side="left", padx=(10, 14), pady=12)
        self._draw_custom_dobbie_portrait(portrait)

        title_frame = tk.Frame(header, bg="#d8c7a5")
        title_frame.pack(side="left", fill="both", expand=True, padx=(0, 18), pady=16)

        tk.Label(title_frame, text="DOBBY", font=("Papyrus", 48, "bold"), fg="#0e1a12", bg="#d8c7a5").pack(anchor="w")
        tk.Label(
            title_frame,
            text="Your magical desktop helper for apps, files, websites, and socks.",
            font=("Georgia", 12, "italic"),
            fg="#2a2118",
            bg="#d8c7a5",
            wraplength=540,
            justify="left",
        ).pack(anchor="w", pady=(2, 0))
        tk.Label(
            title_frame,
            text="Click Mic and speak naturally, or type a command below.",
            font=("Georgia", 10),
            fg="#2f271c",
            bg="#d8c7a5",
            wraplength=540,
            justify="left",
        ).pack(anchor="w", pady=(8, 0))

        command_bar = tk.Frame(title_frame, bg="#d8c7a5")
        command_bar.pack(anchor="w", pady=(16, 0))
        self._quick_button(command_bar, "CHROME", "open chrome").pack(side="left", padx=(0, 8))
        self._quick_button(command_bar, "FILES", "find file resume").pack(side="left", padx=(0, 8))
        self._quick_button(command_bar, "WEB", "search web weather today").pack(side="left", padx=(0, 8))
        self._quick_button(command_bar, "HELP", "what can you do").pack(side="left")

        self.status_var = tk.StringVar(value="Voice ready. Click Mic and speak a command.")
        status_bar = tk.Frame(shell, bg="#b18b4d", bd=0, highlightthickness=1, highlightbackground="#66441f")
        status_bar.pack(fill="x", pady=(0, 10))
        tk.Label(
            status_bar,
            textvariable=self.status_var,
            font=("Georgia", 10, "italic"),
            fg="#1d120e",
            bg="#b18b4d",
            padx=12,
            pady=6,
        ).pack(fill="x")

        log_title = tk.Label(shell, text="Message Box", font=("Georgia", 10, "bold"), fg="#f0d48c", bg="#2a1c12")
        log_title.pack(anchor="w", pady=(0, 6))

        log_outer = tk.Frame(shell, bg="#5e3a1d", padx=4, pady=4)
        log_outer.pack(fill="both", expand=True)
        log_frame = tk.Frame(log_outer, bg="#d7c29c", bd=0, highlightthickness=2, highlightbackground="#8b5b2b")
        log_frame.pack(fill="both", expand=True)

        self.log = scrolledtext.ScrolledText(
            log_frame,
            wrap="word",
            bg="#e8dcc0",
            fg="#201610",
            font=("Georgia", 11),
            bd=0,
            relief="flat",
            padx=16,
            pady=16,
            height=12,
        )
        self.log.pack(fill="both", expand=True, padx=4, pady=4)
        self.log.tag_configure("dobbie", foreground="#2b1d15", font=("Georgia", 11, "bold"))
        self.log.tag_configure("you", foreground="#163427", font=("Georgia", 11, "bold"))
        self.log.configure(state="disabled")

        input_row = tk.Frame(shell, bg="#2a1c12")
        input_row.pack(fill="x", pady=(12, 0))

        self.entry = tk.Entry(
            input_row,
            font=("Georgia", 13),
            bg="#e8dcc0",
            fg="#1a120d",
            insertbackground="#6d3f1d",
            relief="flat",
            highlightthickness=1,
            highlightbackground="#8b5b2b",
            highlightcolor="#8b5b2b",
        )
        self.entry.pack(side="left", fill="x", expand=True, ipady=11, padx=(0, 10))
        self.entry.bind("<Return>", lambda _e: self._submit_text())
        self.entry.focus_set()

        self._action_button(input_row, "Send", self._submit_text, "#364b3d").pack(side="left", padx=(0, 8))

        mic_state = "normal" if STT_AVAILABLE else "disabled"
        self.mic_button = tk.Button(
            input_row,
            text="🎙",
            font=("Georgia", 16, "bold"),
            bg="#d2a14b",
            fg="#1d120e",
            activebackground="#f6d98d",
            activeforeground="#1d120e",
            relief="flat",
            padx=18,
            pady=8,
            state=mic_state,
            command=self._listen_voice,
            bd=0,
        )
        self.mic_button.pack(side="left")

        if not STT_AVAILABLE:
            self._log_system("(voice input unavailable - install SpeechRecognition + pyaudio to enable the mic)")
            self.status_var.set("Voice input unavailable. Text commands still work.")

    def _draw_castle_night_scene(self, canvas):
        canvas.create_rectangle(0, 0, 1400, 180, fill="#050b0d", outline="")
        canvas.create_oval(980, 20, 1180, 220, fill="#f4e3a6", outline="")
        canvas.create_polygon(0, 180, 0, 120, 90, 60, 160, 120, 250, 55, 330, 120, 470, 60, 600, 120, 760, 70, 850, 120, 960, 80, 1060, 120, 1180, 70, 1250, 120, 1400, 120, 1400, 180, fill="#0c1a1d", outline="#223a36", width=2)
        canvas.create_rectangle(60, 120, 130, 180, fill="#132c2d", outline="#d6b15e", width=1)
        canvas.create_rectangle(180, 130, 250, 180, fill="#132c2d", outline="#d6b15e", width=1)
        canvas.create_rectangle(540, 115, 620, 180, fill="#132c2d", outline="#d6b15e", width=1)
        canvas.create_rectangle(720, 120, 800, 180, fill="#132c2d", outline="#d6b15e", width=1)
        canvas.create_rectangle(1020, 120, 1090, 180, fill="#132c2d", outline="#d6b15e", width=1)
        self.window_flares = []
        for x, y, radius in [(120, 96, 28), (310, 115, 34), (500, 88, 30), (660, 106, 36), (840, 98, 32), (1045, 92, 38), (1180, 110, 30)]:
            flare = canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill="#ffb864", outline="", stipple="gray25")
            self.window_flares.append({"id": flare, "x": x, "y": y, "radius": radius})

        self.spark_nodes = []
        for _ in range(20):
            x = 10 + (_ * 71) % 1370
            y = 20 + (_ * 17) % 150
            size = 2 + (_ % 3)
            speed = 0.8 + (_ % 4) * 0.35
            drift = (-1.5 + (_ % 7) * 0.4)
            spark = canvas.create_oval(x, y, x + size, y + size, fill="#f7e7a3", outline="")
            self.spark_nodes.append({"id": spark, "x": float(x), "y": float(y), "size": float(size), "speed": speed, "drift": drift})

    def _start_ambient_animation(self):
        self._ambient_phase = 0
        self.root.after(35, self._animate_ambient_scene)

    def _animate_ambient_scene(self):
        if not hasattr(self, "window_flares"):
            return
        self._ambient_phase += 1
        for idx, flare in enumerate(self.window_flares):
            pulse = 1.0 + (math.sin(self._ambient_phase / 10 + idx) + 1) * 0.7
            radius = flare["radius"] * pulse
            x = flare["x"]
            y = flare["y"]
            self.ambient_canvas.coords(flare["id"], x - radius, y - radius, x + radius, y + radius)

        for spark in self.spark_nodes:
            spark["x"] += spark["drift"]
            spark["y"] -= spark["speed"]
            if spark["y"] < -4:
                spark["y"] = 180
                spark["x"] = (spark["x"] % 1380) + 10
            if spark["x"] < 0:
                spark["x"] = 1380
            if spark["x"] > 1400:
                spark["x"] = 0
            size = spark["size"]
            self.ambient_canvas.coords(spark["id"], spark["x"], spark["y"], spark["x"] + size, spark["y"] + size)

        self.root.after(35, self._animate_ambient_scene)

    def _draw_custom_dobbie_portrait(self, canvas):
        canvas.create_rectangle(0, 0, 180, 160, fill="#1b2a22", outline=GOLD, width=2)
        canvas.create_oval(128, 20, 170, 60, fill="#f3e0ac", outline="")
        canvas.create_oval(35, 22, 79, 60, fill="#f3e0ac", outline="")
        canvas.create_oval(50, 45, 130, 117, fill="#d4b38b", outline=GOLD, width=2)
        canvas.create_oval(70, 63, 86, 79, fill="#1a1713", outline="")
        canvas.create_oval(94, 63, 110, 79, fill="#1a1713", outline="")
        canvas.create_oval(76, 67, 80, 71, fill="#f4ebd1", outline="")
        canvas.create_oval(100, 67, 104, 71, fill="#f4ebd1", outline="")
        canvas.create_arc(75, 80, 105, 100, start=200, extent=120, style="arc", outline=MAROON, width=3)
        canvas.create_polygon(42, 66, 24, 76, 26, 98, 46, 88, fill="#d7c39d", outline=GOLD, width=2)
        canvas.create_polygon(138, 66, 156, 76, 154, 98, 134, 88, fill="#d7c39d", outline=GOLD, width=2)
        canvas.create_polygon(20, 105, 64, 93, 60, 132, 34, 145, fill="#f2d39e", outline=GOLD, width=2)
        canvas.create_polygon(160, 105, 116, 93, 120, 132, 146, 145, fill="#f2d39e", outline=GOLD, width=2)
        canvas.create_polygon(56, 118, 124, 118, 142, 150, 38, 150, fill="#f8f0dc", outline=GOLD, width=2)
        canvas.create_oval(62, 98, 78, 112, fill="#e5b58a", outline="")
        canvas.create_oval(102, 98, 118, 112, fill="#e5b58a", outline="")
        canvas.create_rectangle(78, 116, 102, 132, fill="#b93a2d", outline=GOLD, width=2)
        canvas.create_text(90, 26, text="✦", fill=GOLD, font=("Georgia", 18, "bold"))
        canvas.create_text(34, 30, text="✧", fill=GOLD, font=("Georgia", 18, "bold"))
        canvas.create_text(146, 30, text="✧", fill=GOLD, font=("Georgia", 18, "bold"))

    def _append(self, who: str, text: str):
        self.log.configure(state="normal")
        stamp = datetime.now().strftime("%H:%M")
        tag = "dobbie" if who.startswith("Dobbie") else "you"
        self.log.insert("end", f"[{stamp}] {who}: ", tag)
        self.log.insert("end", f"{text}\n\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _append_async(self, who: str, text: str):
        self.root.after(0, lambda: self._append(who, text))

    def _set_status_async(self, text: str):
        self.root.after(0, lambda: self.status_var.set(text))

    def _log_system(self, text: str):
        self._append("Dobbie", text)

    def _draw_hogwarts_backdrop(self, canvas):
        canvas.create_rectangle(0, 0, 196, 168, fill=STONE, outline="")
        canvas.create_oval(128, 18, 178, 68, fill=MOON, outline="")
        canvas.create_text(38, 24, text="✦", fill=GOLD, font=("Georgia", 16, "bold"))
        canvas.create_text(160, 38, text="✦", fill=GOLD, font=("Georgia", 14, "bold"))
        canvas.create_text(72, 16, text="✦", fill=GOLD, font=("Georgia", 12, "bold"))
        canvas.create_text(20, 90, text="✦", fill=GOLD, font=("Georgia", 12, "bold"))
        canvas.create_text(170, 90, text="✦", fill=GOLD, font=("Georgia", 12, "bold"))

        canvas.create_polygon(16, 150, 50, 85, 82, 118, 100, 90, 132, 128, 150, 94, 180, 150, fill=MAROON, outline=GOLD, width=2)
        canvas.create_rectangle(68, 104, 82, 150, fill=GOLD, outline="")
        canvas.create_rectangle(100, 104, 116, 150, fill=GOLD, outline="")
        canvas.create_polygon(26, 138, 52, 120, 52, 150, fill="#3a4539", outline=GOLD, width=1)
        canvas.create_polygon(130, 138, 156, 120, 156, 150, fill="#3a4539", outline=GOLD, width=1)
        canvas.create_line(28, 150, 62, 150, fill=GOLD, width=2)
        canvas.create_line(126, 150, 166, 150, fill=GOLD, width=2)

    def _draw_mascot(self, canvas):
        canvas.create_rectangle(5, 5, 170, 151, fill="#1d2a22", outline=GOLD, width=2)
        for x, y in [(22, 20), (138, 24), (28, 128), (145, 118), (82, 18)]:
            canvas.create_text(x, y, text="*", fill=GOLD, font=("Georgia", 15, "bold"))
        canvas.create_polygon(22, 63, 61, 42, 55, 88, fill="#caa77b", outline=GOLD, width=2)
        canvas.create_polygon(148, 63, 109, 42, 115, 88, fill="#caa77b", outline=GOLD, width=2)
        canvas.create_oval(50, 30, 120, 105, fill="#d9b98c", outline=GOLD, width=3)
        canvas.create_oval(63, 57, 77, 73, fill="#20150d", outline="")
        canvas.create_oval(94, 57, 108, 73, fill="#20150d", outline="")
        canvas.create_oval(68, 60, 72, 64, fill=PARCHMENT, outline="")
        canvas.create_oval(99, 60, 103, 64, fill=PARCHMENT, outline="")
        canvas.create_line(85, 67, 79, 82, 91, 82, fill="#7d4f2d", width=3, smooth=True)
        canvas.create_arc(67, 74, 104, 94, start=200, extent=140, style="arc", outline=MAROON, width=3)
        canvas.create_polygon(48, 102, 122, 102, 142, 150, 28, 150, fill="#eee4c8", outline=GOLD, width=2)
        canvas.create_line(63, 111, 84, 149, fill="#c7b98f", width=2)
        canvas.create_line(107, 111, 86, 149, fill="#c7b98f", width=2)
        canvas.create_rectangle(111, 113, 147, 137, fill=PARCHMENT, outline=GOLD, width=2)
        canvas.create_line(118, 124, 140, 124, fill=MAROON, width=3)
        canvas.create_arc(117, 119, 141, 139, start=90, extent=180, style="arc", outline=MAROON, width=3)

    def _quick_button(self, parent, text, command_text):
        return tk.Button(
            parent,
            text=text,
            font=("Georgia", 9, "bold"),
            bg=BG_DARK,
            fg=GOLD,
            activebackground=GOLD,
            activeforeground=INK,
            relief="flat",
            padx=12,
            pady=6,
            command=lambda: self._run_quick_command(command_text),
        )

    def _action_button(self, parent, text, command, color):
        return tk.Button(
            parent,
            text=text,
            font=("Georgia", 11, "bold"),
            bg=color,
            fg=GOLD,
            activebackground=GOLD,
            activeforeground=INK,
            relief="flat",
            padx=18,
            pady=8,
            command=command,
        )

    def _run_quick_command(self, command_text):
        self.entry.delete(0, "end")
        self.entry.insert(0, command_text)
        self._submit_text()

    def _greet(self):
        hour = datetime.now().hour
        part = "morning" if hour < 12 else "afternoon" if hour < 18 else "evening"
        msg = f"Good {part}, master! Dobbie welcomes you back. How may Dobbie serve you today?"
        self._append("Dobbie", msg)
        self._speak(msg)

    def _submit_text(self):
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, "end")
        self._append("You", text)
        self._process(text)

    def _process(self, text: str):
        threading.Thread(target=self._process_thread, args=(text,), daemon=True).start()

    def _process_thread(self, text: str):
        self._set_status_async("Dobbie is working on that command...")
        reply = self.brain.handle(text)
        self._append_async("Dobbie", reply)
        self._set_status_async("Ready. Click Mic or type another command.")
        self._speak_reply(reply)

    def _listen_voice(self):
        threading.Thread(target=self._listen_voice_thread, daemon=True).start()

    def _listen_voice_thread(self):
        self._append_async("Dobbie", "Dobbie is listening, master...")
        self._set_status_async("Listening...")
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.4)
                audio = self.recognizer.listen(source, timeout=6, phrase_time_limit=8)
            text = self.recognizer.recognize_google(audio)
            self._append_async("You (voice)", text)
            self._set_status_async(f"Heard: {text}")
            self._process(text)
        except sr.WaitTimeoutError:
            msg = "Dobbie did not hear anything, master."
            self._append_async("Dobbie", msg)
            self._speak(msg)
            self._set_status_async("Ready. Dobbie did not hear anything.")
        except sr.UnknownValueError:
            msg = "Dobbie could not understand that, master."
            self._append_async("Dobbie", msg)
            self._speak(msg)
            self._set_status_async("Ready. Dobbie could not understand that.")
        except Exception as e:
            msg = f"Dobbie's ears failed, master: {e}"
            self._append_async("Dobbie", msg)
            self._speak(msg)
            self._set_status_async("Voice failed. Check microphone permission/device.")

    def _speak(self, text: str):
        if not TTS_AVAILABLE:
            return
        self.speech_queue.put(text)

    def _speak_reply(self, reply: str):
        self._speak(self._speech_text(reply))

    def _speech_text(self, text: str):
        text = re.sub(r"\s+", " ", text.replace("\n", ". ")).strip()
        return text

    def _speech_worker(self):
        engine = None
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", 165)
        except Exception:
            engine = None
        while True:
            text = self.speech_queue.get()
            try:
                if engine and text:
                    engine.say(text)
                    engine.runAndWait()
            except Exception:
                pass
            finally:
                self.speech_queue.task_done()


def run_self_test():
    cfg = load_config()
    bot = Dobbie(cfg)
    bot._open_url = lambda url: f"URL {url}"
    bot.open_app = lambda name: f"OPEN {name}"
    bot.find_file = lambda term: f"FIND {term}"
    bot.open_file = lambda term: f"OPEN FILE {term}"

    commands = [
        "socks",
        "hello",
        "what can you do",
        "open vs code",
        "find file README",
        "open file README",
        "hunt file project report",
        "search web Python Tkinter tutorial",
        "google weather today",
        "open website youtube.com",
    ]
    for command in commands:
        print(f"{command} -> {bot.handle(command).splitlines()[0]}")


def main():
    parser = ArgumentParser(description="Dobbie desktop assistant")
    parser.add_argument("--self-test", action="store_true", help="test command parsing without opening apps")
    args = parser.parse_args()
    if args.self_test:
        run_self_test()
        return

    root = tk.Tk()
    DobbieApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
