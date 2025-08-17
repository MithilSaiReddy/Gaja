import os
import json
import glob
import tempfile
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

CONFIG_FILE = "config.json"

# -------------------------------
# Config Handling
# -------------------------------
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_config(aerender, aftereffects):
    config = {"aerender": aerender, "aftereffects": aftereffects}
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def find_after_effects():
    apps = sorted(glob.glob("/Applications/Adobe After Effects */Adobe After Effects *.app"))
    if not apps:
        return None, None
    latest_app = apps[-1]
    aerender = os.path.join(os.path.dirname(latest_app), "aerender")
    return aerender, latest_app

config = load_config()
AERENDER_PATH = config.get("aerender")
AFTEREFFECTS_APP = config.get("aftereffects")

if not AERENDER_PATH or not AFTEREFFECTS_APP:
    auto_aerender, auto_app = find_after_effects()
    if auto_aerender and auto_app:
        AERENDER_PATH = AERENDER_PATH or auto_aerender
        AFTEREFFECTS_APP = AFTEREFFECTS_APP or auto_app

AERENDER_PATH = AERENDER_PATH or "/Applications/Adobe After Effects 2024/aerender"
AFTEREFFECTS_APP = AFTEREFFECTS_APP or "/Applications/Adobe After Effects 2025/Adobe After Effects 2024.app"

# -------------------------------
# Comp Fetching
# -------------------------------
def get_comps(project_path):
    """Extract comp names from an .aep project using AppleScript + ExtendScript."""
    jsx_code = f"""
    var f = new File("{project_path.replace("\\", "/")}");
    app.open(f);
    var comps = [];
    for (var i = 1; i <= app.project.items.length; i++) {{
        if (app.project.items[i] instanceof CompItem) {{
            comps.push(app.project.items[i].name);
        }}
    }}
    var outputFile = new File("{tempfile.gettempdir().replace("\\", "/")}/comps.txt");
    outputFile.open("w");
    outputFile.write(comps.join("\\n"));
    outputFile.close();
    app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
    """

    jsx_file = os.path.join(tempfile.gettempdir(), "list_comps.jsx")
    with open(jsx_file, "w") as f:
        f.write(jsx_code)

    try:
        subprocess.run([
            "osascript", "-e",
            f'tell application "{AFTEREFFECTS_APP}" to DoScriptFile "{jsx_file}"'
        ], check=True)
    except Exception as e:
        print("⚠️ Failed to run After Effects script:", e)
        return []

    comps_file = os.path.join(tempfile.gettempdir(), "comps.txt")
    if os.path.exists(comps_file):
        with open(comps_file, "r") as f:
            comps = f.read().splitlines()
        return comps
    return []

# -------------------------------
# Render Process
# -------------------------------
def run_render(project, comp, output, log_widget):
    project = os.path.abspath(project)
    output = os.path.abspath(output)
    command = [AERENDER_PATH, "-project", project, "-comp", comp, "-output", output]

    log_widget.insert(tk.END, f"▶ Starting render...\n{' '.join(command)}\n\n")
    log_widget.see(tk.END)

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    for line in process.stdout:
        log_widget.insert(tk.END, line)
        log_widget.see(tk.END)

    process.wait()
    messagebox.showinfo("✅ Done", f"Render finished!\nOutput: {output}")

# -------------------------------
# GUI
# -------------------------------
class AERenderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("After Effects Renderer")
        self.root.geometry("700x500")

        # Menu
        menubar = tk.Menu(root)
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="Set AE Paths", command=self.set_paths)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        root.config(menu=menubar)

        # Project
        tk.Label(root, text="After Effects Project (.aep):").pack(anchor="w")
        self.project_entry = tk.Entry(root, width=80)
        self.project_entry.pack(fill="x")
        tk.Button(root, text="Browse", command=self.browse_project).pack(anchor="e")

        # Comp dropdown
        tk.Label(root, text="Composition:").pack(anchor="w")
        self.comp_var = tk.StringVar()
        self.comp_dropdown = ttk.Combobox(root, textvariable=self.comp_var, width=77, state="readonly")
        self.comp_dropdown.pack(fill="x")

        # Output
        tk.Label(root, text="Output File:").pack(anchor="w")
        self.output_entry = tk.Entry(root, width=80)
        self.output_entry.pack(fill="x")
        tk.Button(root, text="Browse", command=self.browse_output).pack(anchor="e")

        # Start button
        tk.Button(root, text="Start Render", command=self.start_render).pack(pady=10)

        # Log
        tk.Label(root, text="Render Log:").pack(anchor="w")
        self.log_widget = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=15, bg="black", fg="lime")
        self.log_widget.pack(fill="both", expand=True)

    def browse_project(self):
        filename = filedialog.askopenfilename(filetypes=[("After Effects Project", "*.aep")])
        if filename:
            self.project_entry.delete(0, tk.END)
            self.project_entry.insert(0, filename)

            # auto-fetch comps
            comps = get_comps(filename)
            if comps:
                self.comp_dropdown["values"] = comps
                self.comp_var.set(comps[0])

    def browse_output(self):
        filename = filedialog.asksaveasfilename(defaultextension=".mov",
                                                filetypes=[("QuickTime Movie", "*.mov"), ("MP4 Video", "*.mp4")])
        if filename:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, filename)

    def start_render(self):
        project = self.project_entry.get().strip()
        comp = self.comp_var.get().strip()
        output = self.output_entry.get().strip()

        if not project or not comp or not output:
            messagebox.showerror("Error", "Please fill in all fields.")
            return

        threading.Thread(target=run_render, args=(project, comp, output, self.log_widget), daemon=True).start()

    def set_paths(self):
        def save_and_close():
            aerender = aerender_entry.get().strip()
            ae_app = ae_app_entry.get().strip()
            if aerender and ae_app:
                save_config(aerender, ae_app)
                global AERENDER_PATH, AFTEREFFECTS_APP
                AERENDER_PATH, AFTEREFFECTS_APP = aerender, ae_app
                messagebox.showinfo("Saved", "Paths updated successfully!")
                win.destroy()

        win = tk.Toplevel(self.root)
        win.title("Set After Effects Paths")
        win.geometry("500x200")

        tk.Label(win, text="aerender Path:").pack(anchor="w", padx=10, pady=(10, 0))
        aerender_entry = tk.Entry(win, width=60)
        aerender_entry.pack(padx=10, pady=2)
        aerender_entry.insert(0, AERENDER_PATH)

        tk.Label(win, text="After Effects App Path:").pack(anchor="w", padx=10, pady=(10, 0))
        ae_app_entry = tk.Entry(win, width=60)
        ae_app_entry.pack(padx=10, pady=2)
        ae_app_entry.insert(0, AFTEREFFECTS_APP)

        tk.Button(win, text="Save", command=save_and_close).pack(pady=10)

# -------------------------------
# Run App
# -------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = AERenderApp(root)
    root.mainloop()
