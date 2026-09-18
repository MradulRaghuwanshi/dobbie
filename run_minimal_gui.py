import tkinter as tk
from tkinter import scrolledtext

# Import Dobbie and config loader from main.py
from main import load_config, Dobbie

cfg = load_config()
brain = Dobbie(cfg)

root = tk.Tk()
root.title("Dobbie - Minimal Input")
root.geometry("700x400")
root.attributes("-topmost", True)

log = scrolledtext.ScrolledText(root, wrap="word", height=18)
log.pack(fill="both", expand=True, padx=8, pady=(8, 4))
log.insert("end", "Dobbie minimal UI started. Type a command below and press Enter.\n\n")
log.configure(state="disabled")

entry_frame = tk.Frame(root)
entry_frame.pack(fill="x", padx=8, pady=(0, 8))

entry = tk.Entry(entry_frame, font=("Segoe UI", 12))
entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
entry.focus_set()


def append_log(who, text):
    log.configure(state="normal")
    log.insert("end", f"{who}: {text}\n\n")
    log.see("end")
    log.configure(state="disabled")


def send_command(event=None):
    cmd = entry.get().strip()
    if not cmd:
        return
    entry.delete(0, "end")
    append_log("You", cmd)
    try:
        result = brain.handle(cmd)
        if isinstance(result, dict):
            text = result.get("response", str(result))
        else:
            text = str(result)
    except Exception as e:
        text = f"Error processing command: {e}"
    append_log("Dobbie", text)


send_btn = tk.Button(entry_frame, text="Send", command=send_command)
send_btn.pack(side="right")
entry.bind("<Return>", send_command)

# Ensure window is visible on top briefly
root.lift()
root.after(1500, lambda: root.attributes("-topmost", False))

root.mainloop()
