import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import urllib.request
import subprocess
import winreg
import shutil
import ctypes
import time
import os

# ─── App Definitions ─────────────────────────────────────────────────────────

APPS = [
    {
        "name": "Brave Browser",
        "icon": "🌐",
        "category": "Browsers",
        "url": "https://laptop-updates.brave.com/latest/winx64",
        "filename": "BraveSetup.exe",
        "reg_names": ["Brave"],
        "settings_note": None,
        "settings_url": None,
    },
    {
        "name": "Discord",
        "icon": "💬",
        "category": "Communication",
        "url": "https://discord.com/api/downloads/distributions/app/installers/latest?channel=stable&platform=win&arch=x64",
        "filename": "DiscordSetup.exe",
        "reg_names": ["Discord"],
        "settings_note": None,
        "settings_url": None,
    },
    {
        "name": "Steam",
        "icon": "🎮",
        "category": "Gaming",
        "url": "https://cdn.akamai.steamstatic.com/client/installer/SteamSetup.exe",
        "filename": "SteamSetup.exe",
        "reg_names": ["Steam"],
        "settings_note": None,
        "settings_url": None,
    },
    {
        "name": "OBS Studio",
        "icon": "🎥",
        "category": "Streaming",
        "url": "https://github.com/obsproject/obs-studio/releases/latest/download/OBS-Studio-installer.exe",
        "filename": "OBSSetup.exe",
        "reg_names": ["OBS Studio"],
        "settings_note": "Export scenes:   OBS → Scene Collection → Export\nExport profile:  OBS → Profile → Export\nDrop both files into your new install to restore.",
        "settings_url": None,
    },
    {
        "name": "Logitech G HUB",
        "icon": "🖱️",
        "category": "Peripherals",
        "url": "https://download01.logi.com/web/ftp/pub/techsupport/gaming/lghub_installer.exe",
        "filename": "LGHUB_Setup.exe",
        "reg_names": ["LGHUB", "Logitech G HUB"],
        "settings_note": "Back up your profiles before reinstalling:\n%LOCALAPPDATA%\\LGHUB\\settings.db\nRestore that file after G HUB is installed.",
        "settings_url": None,
    },
    {
        "name": "Razer Synapse",
        "icon": "🐍",
        "category": "Peripherals",
        "url": "https://dl.razerzone.com/synapse3/RazerSynapse3Setup.exe",
        "filename": "RazerSynapseSetup.exe",
        "reg_names": ["Razer Synapse", "Razer Synapse 3"],
        "settings_note": "Sign into your Razer ID after install.\nAll profiles sync automatically from Razer Cloud.",
        "settings_url": None,
    },
    {
        "name": "Splashtop Personal",
        "icon": "🖥️",
        "category": "Remote Access",
        "url": "https://redirect.splashtop.com/stp-src/win?web_source=disabled&web_medium=disabled&utm_source=disabled&utm_medium=disabled&utm_campaign=disabled&utm_content=disabled&utm_term=disabled&page=disabled&platform=web&ajs_aid=6bb5ff1e-6175-467c-9b6b-dbd92064924b&optid=oeu1776542977971r0.9941469947251369",
        "filename": "SplashtopSetup.exe",
        "reg_names": ["Splashtop", "Splashtop Personal"],
        "settings_note": "Sign into your Splashtop account after install\nto restore all your device access.",
        "settings_url": None,
    },
    {
        "name": "Exodus Wallet",
        "icon": "💰",
        "category": "Finance",
        "url": "https://downloads.exodus.com/releases/exodus-windows-x64-26.3.11.exe",
        "filename": "ExodusSetup.exe",
        "reg_names": ["Exodus"],
        "settings_note": "Restore your wallet with your 12-word recovery phrase.\n⚠  NEVER store your seed phrase digitally.",
        "settings_url": None,
    },
]

# ─── Theme ───────────────────────────────────────────────────────────────────

BG         = "#0d0f14"
SURFACE    = "#13161f"
SURFACE2   = "#1a1e2e"
BORDER     = "#222638"
ACCENT     = "#4f8ef7"
SUCCESS    = "#3ecf8e"
WARNING    = "#f5a623"
ERROR      = "#f74f4f"
TEXT       = "#dde3f5"
TEXT_DIM   = "#6b7490"
TEXT_MUTED = "#323754"

FT  = ("Segoe UI", 10, "bold")
FS  = ("Segoe UI", 9)
FC  = ("Consolas", 9)

INSTALLER_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "installers")

# ─── Registry Check ───────────────────────────────────────────────────────────

def is_installed(reg_names):
    paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER,  r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    for hive, path in paths:
        try:
            key = winreg.OpenKey(hive, path)
            for i in range(winreg.QueryInfoKey(key)[0]):
                try:
                    sub = winreg.OpenKey(key, winreg.EnumKey(key, i))
                    try:
                        val, _ = winreg.QueryValueEx(sub, "DisplayName")
                        for name in reg_names:
                            if name.lower() in val.lower():
                                return True
                    except OSError:
                        pass
                except OSError:
                    pass
        except OSError:
            pass
    return False

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

# ─── App ─────────────────────────────────────────────────────────────────────

class InstallerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.overrideredirect(True)
        self.geometry("920x680")
        self.configure(bg=BG)
        self.resizable(False, False)
        self._drag_x = self._drag_y = 0

        # Center
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 920) // 2
        y = (self.winfo_screenheight() - 680) // 2
        self.geometry(f"920x680+{x}+{y}")

        self._cancelled = False
        self._running   = False

        self.app_check  = {}   # name → BooleanVar
        self.app_status = {}   # name → Label
        self.app_bar    = {}   # name → Progressbar

        os.makedirs(INSTALLER_DIR, exist_ok=True)

        self._build()
        self._check_all()

    # ── Build ──────────────────────────────────────────────────────────────

    def _build(self):
        # Title bar
        tb = tk.Frame(self, bg=SURFACE, height=46)
        tb.pack(fill="x")
        tb.pack_propagate(False)
        tb.bind("<ButtonPress-1>", lambda e: setattr(self, '_drag_x', e.x) or setattr(self, '_drag_y', e.y))
        tb.bind("<B1-Motion>",     lambda e: self.geometry(f"+{self.winfo_x()+e.x-self._drag_x}+{self.winfo_y()+e.y-self._drag_y}"))

        tk.Label(tb, text="  FreshStart", font=("Segoe UI", 14, "bold"),
                 bg=SURFACE, fg=TEXT).pack(side="left")
        tk.Label(tb, text="  System Setup", font=("Segoe UI", 11),
                 bg=SURFACE, fg=TEXT_DIM).pack(side="left")

        if not is_admin():
            tk.Label(tb, text=" ⚠ Run as Administrator ", font=FS,
                     bg=WARNING, fg="#1a0f00").pack(side="left", padx=16)

        ctrl = tk.Frame(tb, bg=SURFACE)
        ctrl.pack(side="right", padx=6)
        tk.Button(ctrl, text="─", font=("Segoe UI", 12), bg=SURFACE, fg=TEXT_DIM,
                  relief="flat", bd=0, padx=11, pady=5, cursor="hand2",
                  activebackground=SURFACE2, command=self.iconify).pack(side="left")
        tk.Button(ctrl, text="✕", font=("Segoe UI", 12), bg=SURFACE, fg=TEXT_DIM,
                  relief="flat", bd=0, padx=11, pady=5, cursor="hand2",
                  activebackground="#2a1010", activeforeground=ERROR,
                  command=self._close).pack(side="left")

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # Body
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)

        # ── Left: app list ────────────────────────────────────────────────
        left = tk.Frame(body, bg=BG, width=545)
        left.pack(side="left", fill="both", expand=True, padx=(18,8), pady=14)
        left.pack_propagate(False)

        lh = tk.Frame(left, bg=BG)
        lh.pack(fill="x", pady=(0,8))
        tk.Label(lh, text="Select Apps", font=FT, bg=BG, fg=TEXT).pack(side="left")

        sf = tk.Frame(lh, bg=BG)
        sf.pack(side="right")
        for lbl, fn in [("All", self._sel_all), ("None", self._sel_none)]:
            tk.Button(sf, text=lbl, font=FS, bg=SURFACE2, fg=TEXT_DIM,
                      relief="flat", bd=0, padx=9, pady=3, cursor="hand2",
                      activebackground=BORDER, command=fn).pack(side="left", padx=2)

        list_outer = tk.Frame(left, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        list_outer.pack(fill="both", expand=True)

        canvas = tk.Canvas(list_outer, bg=SURFACE, highlightthickness=0, bd=0)
        vsb = ttk.Scrollbar(list_outer, orient="vertical", command=canvas.yview)
        self.lf = tk.Frame(canvas, bg=SURFACE)
        self.lf.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0), window=self.lf, anchor="nw")
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

        self._build_list()

        # ── Right: log ────────────────────────────────────────────────────
        right = tk.Frame(body, bg=BG, width=335)
        right.pack(side="right", fill="both", padx=(8,18), pady=14)
        right.pack_propagate(False)

        tk.Label(right, text="Log", font=FT, bg=BG, fg=TEXT).pack(anchor="w", pady=(0,8))

        lw = tk.Frame(right, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        lw.pack(fill="both", expand=True)

        self.log = scrolledtext.ScrolledText(lw, bg=SURFACE, fg=TEXT_DIM, font=FC,
            bd=0, relief="flat", wrap="word", state="disabled",
            insertbackground=TEXT, padx=10, pady=10, selectbackground=BORDER)
        self.log.pack(fill="both", expand=True)
        self.log.tag_config("ok",   foreground=SUCCESS)
        self.log.tag_config("err",  foreground=ERROR)
        self.log.tag_config("warn", foreground=WARNING)
        self.log.tag_config("hi",   foreground=ACCENT)
        self.log.tag_config("dim",  foreground=TEXT_MUTED)

        # ── Bottom bar ────────────────────────────────────────────────────
        btm = tk.Frame(self, bg=SURFACE, padx=18, pady=10,
                       highlightbackground=BORDER, highlightthickness=1)
        btm.pack(fill="x", side="bottom")

        lb = tk.Frame(btm, bg=SURFACE)
        lb.pack(side="left", fill="y")

        self.status_lbl = tk.Label(lb, text="Ready.", font=FS, bg=SURFACE, fg=TEXT_DIM)
        self.status_lbl.pack(anchor="w")

        s = ttk.Style()
        s.theme_use("clam")
        s.configure("G.Horizontal.TProgressbar",
            background=ACCENT, troughcolor=SURFACE2, borderwidth=0, thickness=4)
        s.configure("App.Horizontal.TProgressbar",
            background=ACCENT2 if False else SURFACE2, troughcolor=BG, borderwidth=0, thickness=3)

        self.global_bar = ttk.Progressbar(lb, orient="horizontal", length=340,
            mode="determinate", style="G.Horizontal.TProgressbar")
        self.global_bar.pack(anchor="w", pady=(4,0))

        rb = tk.Frame(btm, bg=SURFACE)
        rb.pack(side="right")

        tk.Button(rb, text="Clear Log", font=FS, bg=SURFACE2, fg=TEXT_DIM,
                  relief="flat", bd=0, padx=12, pady=9, cursor="hand2",
                  activebackground=BORDER, command=self._clear_log).pack(side="left", padx=(0,8))

        self.cancel_btn = tk.Button(rb, text="Cancel", font=FT,
                  bg=SURFACE2, fg=TEXT_DIM, relief="flat", bd=0,
                  padx=14, pady=9, cursor="hand2",
                  activebackground=BORDER, state="disabled", command=self._cancel)
        self.cancel_btn.pack(side="left", padx=(0,8))

        self.go_btn = tk.Button(rb, text="  Download & Install  ", font=FT,
                  bg=ACCENT, fg="white", relief="flat", bd=0,
                  padx=18, pady=9, cursor="hand2",
                  activebackground="#3a7de0", command=self._start)
        self.go_btn.pack(side="left")

    def _build_list(self):
        cats = {}
        for app in APPS:
            cats.setdefault(app["category"], []).append(app)

        for cat, apps in cats.items():
            ch = tk.Frame(self.lf, bg=SURFACE2, pady=4, padx=12)
            ch.pack(fill="x", pady=(10,0))
            tk.Label(ch, text=cat.upper(), font=("Segoe UI", 7, "bold"),
                     bg=SURFACE2, fg=TEXT_MUTED).pack(side="left")

            for app in apps:
                var = tk.BooleanVar(value=True)
                self.app_check[app["name"]] = var

                row = tk.Frame(self.lf, bg=SURFACE, padx=10, pady=8)
                row.pack(fill="x")
                row.bind("<Enter>", lambda e, r=row: r.configure(bg=SURFACE2))
                row.bind("<Leave>", lambda e, r=row: r.configure(bg=SURFACE))

                # Left col
                lc = tk.Frame(row, bg=SURFACE)
                lc.pack(side="left", fill="y")

                tk.Checkbutton(lc, variable=var, bg=SURFACE,
                    activebackground=SURFACE2, selectcolor=BG,
                    relief="flat", bd=0, cursor="hand2").pack(side="left")

                tk.Label(lc, text=app["icon"], font=("Segoe UI Emoji", 12),
                         bg=SURFACE).pack(side="left", padx=(2,7))

                nc = tk.Frame(lc, bg=SURFACE)
                nc.pack(side="left")

                tk.Label(nc, text=app["name"], font=FT,
                         bg=SURFACE, fg=TEXT).pack(anchor="w")

                bar = ttk.Progressbar(nc, orient="horizontal", length=200,
                    mode="determinate", style="G.Horizontal.TProgressbar")
                bar.pack(anchor="w", pady=(3,0))
                self.app_bar[app["name"]] = bar

                # Right col
                rc = tk.Frame(row, bg=SURFACE)
                rc.pack(side="right", fill="y")

                sl = tk.Label(rc, text="● checking", font=FS, bg=SURFACE, fg=TEXT_MUTED)
                sl.pack(side="right", padx=(10,0))
                self.app_status[app["name"]] = sl

                if app.get("settings_note") or app.get("settings_url"):
                    tk.Button(rc, text="⚙", font=FS, bg=SURFACE2, fg=TEXT_DIM,
                              relief="flat", bd=0, padx=7, pady=4, cursor="hand2",
                              activebackground=BORDER,
                              command=lambda a=app: self._settings_popup(a)
                    ).pack(side="right", padx=(0,6))

    # ── Drag ──────────────────────────────────────────────────────────────────

    def _drag_start(self, e):
        self._drag_x = e.x; self._drag_y = e.y

    def _drag_move(self, e):
        self.geometry(f"+{self.winfo_x()+e.x-self._drag_x}+{self.winfo_y()+e.y-self._drag_y}")

    # ── Registry Check ────────────────────────────────────────────────────────

    def _check_all(self):
        def worker():
            for app in APPS:
                inst = is_installed(app["reg_names"])
                def upd(a=app, i=inst):
                    sl = self.app_status[a["name"]]
                    if i:
                        sl.configure(text="● installed", fg=SUCCESS)
                        self.app_check[a["name"]].set(False)
                    else:
                        sl.configure(text="● not installed", fg=TEXT_MUTED)
                self.after(0, upd)
        threading.Thread(target=worker, daemon=True).start()

    # ── Install Flow ──────────────────────────────────────────────────────────

    def _start(self):
        if self._running:
            return
        selected = [a for a in APPS if self.app_check[a["name"]].get()]
        if not selected:
            self._log("Nothing selected.", "warn")
            return

        self._cancelled = False
        self._running   = True
        self.go_btn.configure(state="disabled", bg=SURFACE2, fg=TEXT_DIM)
        self.cancel_btn.configure(state="normal", bg="#2a1010", fg=ERROR)
        self.global_bar.configure(maximum=len(selected) * 2, value=0)  # dl + install per app

        def run():
            downloaded = []

            # ── Phase 1: Download ──────────────────────────────────────────
            self._log("\n━━ Phase 1 — Downloading ━━", "hi")

            for idx, app in enumerate(selected):
                if self._cancelled:
                    break

                name = app["name"]
                dest = os.path.join(INSTALLER_DIR, app["filename"])
                self._setstatus(name, "● downloading…", ACCENT)
                self._log(f"↓  {app['icon']}  {name}", "hi")

                try:
                    req = urllib.request.Request(
                        app["url"],
                        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                    )
                    with urllib.request.urlopen(req, timeout=90) as resp:
                        total = int(resp.headers.get("Content-Length", 0) or 0)
                        got   = 0
                        with open(dest, "wb") as f:
                            while True:
                                if self._cancelled:
                                    break
                                chunk = resp.read(16384)
                                if not chunk:
                                    break
                                f.write(chunk)
                                got += len(chunk)
                                if total:
                                    pct = got / total * 100
                                    mb  = got / 1_048_576
                                    tmb = total / 1_048_576
                                    self.after(0, lambda p=pct, n=name: self.app_bar[n].configure(value=p))
                                    self.after(0, lambda m=mb, t=tmb, n=name:
                                        self.status_lbl.configure(text=f"{n}  {m:.1f}/{t:.1f} MB"))

                    if self._cancelled:
                        self._setstatus(name, "● cancelled", WARNING)
                        break

                    self.after(0, lambda n=name: self.app_bar[n].configure(value=100))
                    mb_final = os.path.getsize(dest) / 1_048_576
                    self._log(f"   ✓ {mb_final:.1f} MB  →  installers/{app['filename']}", "ok")
                    self._setstatus(name, "● ready", TEXT_DIM)
                    downloaded.append((app, dest))

                except Exception as ex:
                    self._log(f"   ✗ Failed: {ex}", "err")
                    self._setstatus(name, "● dl failed", ERROR)

                self.after(0, lambda v=idx+1: self.global_bar.configure(value=v))

            if self._cancelled:
                self._log("\n⚠  Cancelled during download.", "warn")
                self.after(0, self._reset)
                return

            if not downloaded:
                self._log("\n✗  Nothing downloaded successfully.", "err")
                self.after(0, self._reset)
                return

            # ── Phase 2: Run installers one by one ────────────────────────
            total_dl = len(selected)
            self._log(f"\n━━ Phase 2 — Installing ({len(downloaded)} app(s)) ━━", "hi")
            self._log("Close each installer to continue to the next.", "warn")

            for idx, (app, path) in enumerate(downloaded):
                if self._cancelled:
                    break

                name = app["name"]
                self._setstatus(name, "● installing…", WARNING)
                self._log(f"\n▸ [{idx+1}/{len(downloaded)}]  {app['icon']}  {name}", "hi")
                self.after(0, lambda: self.status_lbl.configure(
                    text=f"Waiting for installer to close… ({name})"))

                try:
                    proc = subprocess.Popen(
                        [path],
                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                    )
                    while proc.poll() is None:
                        if self._cancelled:
                            proc.terminate()
                            break
                        time.sleep(0.4)

                    if self._cancelled:
                        self._setstatus(name, "● cancelled", WARNING)
                        break

                    self._setstatus(name, "● done", SUCCESS)
                    self._log(f"   ✓  {name} — installer closed.", "ok")

                except Exception as ex:
                    self._log(f"   ✗  Could not launch: {ex}", "err")
                    self._setstatus(name, "● error", ERROR)

                self.after(0, lambda v=total_dl+idx+1: self.global_bar.configure(value=v))

            if self._cancelled:
                self._log("\n⚠  Cancelled during install.", "warn")
                self.after(0, self._reset)
                return

            self._log("\n━━ All done! ━━", "ok")
            self._log("A restart is recommended if you installed peripheral drivers.", "warn")
            self.after(0, self._cleanup_prompt)
            self.after(0, self._reset)

        threading.Thread(target=run, daemon=True).start()

    # ── Cleanup Prompt ────────────────────────────────────────────────────────

    def _cleanup_prompt(self):
        popup = tk.Toplevel(self)
        popup.configure(bg=BG)
        popup.resizable(False, False)
        popup.overrideredirect(True)
        popup.geometry("440x210")
        popup.grab_set()

        px = self.winfo_x() + (920 - 440) // 2
        py = self.winfo_y() + (680 - 210) // 2
        popup.geometry(f"440x210+{px}+{py}")

        def ds(e): popup._dx = e.x; popup._dy = e.y
        def dm(e): popup.geometry(f"+{popup.winfo_x()+e.x-popup._dx}+{popup.winfo_y()+e.y-popup._dy}")

        bar = tk.Frame(popup, bg=SURFACE2, height=38)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        bar.bind("<ButtonPress-1>", ds)
        bar.bind("<B1-Motion>",     dm)
        tk.Label(bar, text="  ✓  Installation Complete", font=FT,
                 bg=SURFACE2, fg=SUCCESS).pack(side="left", padx=6, pady=8)

        tk.Frame(popup, bg=BORDER, height=1).pack(fill="x")

        msg_frame = tk.Frame(popup, bg=BG, pady=16)
        msg_frame.pack(fill="x", padx=20)

        tk.Label(msg_frame, text="What would you like to do with the downloaded installers?",
                 font=FS, bg=BG, fg=TEXT, wraplength=400, justify="left").pack(anchor="w")

        try:
            size_mb = sum(
                os.path.getsize(os.path.join(INSTALLER_DIR, f))
                for f in os.listdir(INSTALLER_DIR)
                if os.path.isfile(os.path.join(INSTALLER_DIR, f))
            ) / 1_048_576
            tk.Label(msg_frame, text=f"  installers/   {size_mb:.1f} MB",
                     font=("Consolas", 8), bg=BG, fg=TEXT_MUTED).pack(anchor="w", pady=(6,0))
        except Exception:
            pass

        btn_row = tk.Frame(popup, bg=BG)
        btn_row.pack(fill="x", padx=20, pady=10)

        def delete_and_close():
            try:
                shutil.rmtree(INSTALLER_DIR)
                self._log("🗑  Installer folder deleted.", "ok")
            except Exception as ex:
                self._log(f"Could not delete folder: {ex}", "err")
            popup.destroy()

        tk.Button(btn_row, text="🗑  Delete Installers", font=FT,
                  bg=ERROR, fg="white", relief="flat", bd=0,
                  padx=14, pady=8, cursor="hand2",
                  activebackground="#c43a3a",
                  command=delete_and_close).pack(side="left")

        tk.Button(btn_row, text="📁  Keep Them", font=FT,
                  bg=SURFACE2, fg=TEXT_DIM, relief="flat", bd=0,
                  padx=14, pady=8, cursor="hand2",
                  activebackground=BORDER,
                  command=popup.destroy).pack(side="left", padx=10)

    # ── Settings Popup ────────────────────────────────────────────────────────

    def _settings_popup(self, app):
        popup = tk.Toplevel(self)
        popup.configure(bg=BG)
        popup.resizable(False, False)
        popup.overrideredirect(True)
        popup.geometry("480x240")
        popup.grab_set()

        px = self.winfo_x() + (920 - 480) // 2
        py = self.winfo_y() + (680 - 240) // 2
        popup.geometry(f"480x240+{px}+{py}")

        def ds(e): popup._dx = e.x; popup._dy = e.y
        def dm(e): popup.geometry(f"+{popup.winfo_x()+e.x-popup._dx}+{popup.winfo_y()+e.y-popup._dy}")

        bar = tk.Frame(popup, bg=SURFACE2, height=38)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        bar.bind("<ButtonPress-1>", ds)
        bar.bind("<B1-Motion>",     dm)
        tk.Label(bar, text=f"  {app['icon']}  {app['name']} — Settings",
                 font=FT, bg=SURFACE2, fg=TEXT).pack(side="left", padx=6, pady=8)
        tk.Button(bar, text="✕", font=FS, bg=SURFACE2, fg=TEXT_DIM,
                  relief="flat", bd=0, padx=10, cursor="hand2",
                  activebackground="#2a1010", command=popup.destroy).pack(side="right")

        tk.Frame(popup, bg=BORDER, height=1).pack(fill="x")

        if app.get("settings_note"):
            nf = tk.Frame(popup, bg=SURFACE2, padx=16, pady=14)
            nf.pack(fill="x", padx=16, pady=14)
            tk.Label(nf, text=app["settings_note"], font=("Consolas", 9),
                     bg=SURFACE2, fg=TEXT, justify="left", wraplength=420).pack(anchor="w")

        if app.get("settings_url"):
            import webbrowser
            tk.Button(popup, text="Open Guide →", font=FT,
                      bg=ACCENT, fg="white", relief="flat", bd=0,
                      padx=14, pady=8, cursor="hand2",
                      command=lambda: webbrowser.open(app["settings_url"])
            ).pack(anchor="w", padx=16, pady=(0,10))

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _cancel(self):
        if not self._running:
            return
        self._cancelled = True
        self._log("\n⚠  Cancelling…", "warn")
        self.cancel_btn.configure(state="disabled")

    def _reset(self):
        self._running = False
        self.go_btn.configure(state="normal", bg=ACCENT, fg="white")
        self.cancel_btn.configure(state="disabled", bg=SURFACE2, fg=TEXT_DIM)
        self.status_lbl.configure(text="Done.")

    def _setstatus(self, name, text, color):
        def upd():
            lbl = self.app_status.get(name)
            if lbl:
                lbl.configure(text=text, fg=color)
        self.after(0, upd)

    def _log(self, msg, tag=None):
        def upd():
            self.log.configure(state="normal")
            self.log.insert("end", msg + "\n", tag or "")
            self.log.see("end")
            self.log.configure(state="disabled")
        self.after(0, upd)

    def _clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def _sel_all(self):
        for v in self.app_check.values(): v.set(True)

    def _sel_none(self):
        for v in self.app_check.values(): v.set(False)

    def _close(self):
        if self._running:
            self._cancelled = True
        self.destroy()

# ─── Entry ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = InstallerApp()
    app.mainloop()
