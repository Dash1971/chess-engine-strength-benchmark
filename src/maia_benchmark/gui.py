from __future__ import annotations

import os
import queue
import signal
import subprocess
import sys
import threading
from pathlib import Path
from tkinter import BooleanVar, StringVar, Tk, filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText


ENGINE_FIELDS = (
    ("path", "UCI launcher", "file"),
    ("name", "Name", None),
    ("elo", "Elo", None),
    ("self-elo", "Self Elo", None),
    ("opponent-elo", "Opponent Elo", None),
    ("temperature", "Temperature", None),
    ("top-p", "Top P", None),
    ("book", "Polyglot book", "file"),
)

MATCH_FIELDS = (
    ("number-of-games", "Games", None),
    ("output", "Output PGN", "save"),
    ("openings", "Opening suite", "file"),
    ("nodes", "Nodes per move", None),
    ("move-time-ms", "Move time (ms)", None),
    ("max-plies", "Maximum plies", None),
    ("seed", "Book seed", None),
)


def build_command(values: dict[str, str], resume: bool = False) -> list[str]:
    command = [sys.executable, "-m", "maia_benchmark.cli"]
    required = ("engine-a-path", "engine-b-path", "number-of-games")
    missing = [key for key in required if not values.get(key, "").strip()]
    if missing:
        raise ValueError("Required fields: " + ", ".join(key.replace("-", " ") for key in missing))

    openings = values.get("openings", "").strip()
    if openings and (values.get("engine-a-book", "").strip() or values.get("engine-b-book", "").strip()):
        raise ValueError("Opening suites cannot be combined with engine books.")
    if resume and not openings:
        raise ValueError("Resume requires an opening suite.")

    for key, value in values.items():
        value = value.strip()
        if value:
            command.extend((f"--{key}", value))
    if resume:
        command.append("--resume")
    return command


class BenchmarkGui:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("Maia Engine Strength Benchmark")
        self.root.minsize(820, 680)
        self.variables: dict[str, StringVar] = {}
        self.resume = BooleanVar(value=False)
        self.process: subprocess.Popen[str] | None = None
        self.events: queue.Queue[tuple[str, str | int]] = queue.Queue()

        container = ttk.Frame(root, padding=12)
        container.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(3, weight=1)

        self._engine_panel(container, "a", "Engine A", 0)
        self._engine_panel(container, "b", "Engine B", 1)
        self._match_panel(container)
        self._controls(container)

        self.log = ScrolledText(container, height=14, wrap="word", state="disabled")
        self.log.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=(10, 0))
        self.status = StringVar(value="Ready")
        ttk.Label(container, textvariable=self.status).grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(6, 0)
        )

        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self.root.after(100, self._poll_events)

    def _engine_panel(self, parent: ttk.Frame, side: str, title: str, column: int) -> None:
        frame = ttk.LabelFrame(parent, text=title, padding=10)
        frame.grid(row=0, column=column, sticky="nsew", padx=(0, 5) if column == 0 else (5, 0))
        frame.columnconfigure(1, weight=1)
        for row, (field, label, picker) in enumerate(ENGINE_FIELDS):
            key = f"engine-{side}-{field}"
            self._field(frame, row, key, label, picker)
        self.variables[f"engine-{side}-name"].set(title)

    def _match_panel(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Match", padding=10)
        frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        for column in (1, 4):
            frame.columnconfigure(column, weight=1)
        for index, (field, label, picker) in enumerate(MATCH_FIELDS):
            row, half = divmod(index, 2)
            key = field
            self._field(frame, row, key, label, picker, column=half * 3)
        self.variables["number-of-games"].set("2")
        self.variables["output"].set(str(Path.cwd() / "benchmark-games.pgn"))
        self.variables["nodes"].set("1")
        self.variables["max-plies"].set("300")

    def _field(
        self,
        parent: ttk.Frame,
        row: int,
        key: str,
        label: str,
        picker: str | None,
        column: int = 0,
    ) -> None:
        variable = StringVar()
        self.variables[key] = variable
        ttk.Label(parent, text=label).grid(row=row, column=column, sticky="w", padx=(0, 6), pady=2)
        ttk.Entry(parent, textvariable=variable).grid(
            row=row, column=column + 1, sticky="ew", pady=2
        )
        if picker:
            ttk.Button(
                parent,
                text="Browse…",
                command=lambda k=key, p=picker: self._browse(k, p),
            ).grid(row=row, column=column + 2, padx=(5, 0), pady=2)

    def _controls(self, parent: ttk.Frame) -> None:
        frame = ttk.Frame(parent)
        frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        ttk.Checkbutton(frame, text="Resume interrupted paired match", variable=self.resume).pack(
            side="left"
        )
        self.start_button = ttk.Button(frame, text="Start match", command=self._start)
        self.start_button.pack(side="right")
        self.stop_button = ttk.Button(frame, text="Stop", command=self._stop, state="disabled")
        self.stop_button.pack(side="right", padx=6)
        ttk.Button(frame, text="Reveal PGN", command=self._reveal_output).pack(side="right")

    def _browse(self, key: str, picker: str) -> None:
        if picker == "save":
            selected = filedialog.asksaveasfilename(
                defaultextension=".pgn", filetypes=(("PGN files", "*.pgn"), ("All files", "*"))
            )
        else:
            filetypes = (("PGN files", "*.pgn"), ("All files", "*")) if key == "openings" else ()
            selected = filedialog.askopenfilename(filetypes=filetypes)
        if selected:
            self.variables[key].set(selected)

    def _start(self) -> None:
        try:
            command = build_command(
                {key: variable.get() for key, variable in self.variables.items()}, self.resume.get()
            )
        except ValueError as error:
            messagebox.showerror("Invalid configuration", str(error))
            return

        self._append("Starting match…\n")
        self.status.set("Running")
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        threading.Thread(target=self._run, args=(command,), daemon=True).start()

    def _run(self, command: list[str]) -> None:
        try:
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                start_new_session=True,
            )
            assert self.process.stdout is not None
            for line in self.process.stdout:
                self.events.put(("output", line))
            return_code = self.process.wait()
            self.events.put(("done", return_code))
        except OSError as error:
            self.events.put(("output", f"Could not start benchmark: {error}\n"))
            self.events.put(("done", 1))

    def _stop(self) -> None:
        if self.process is not None and self.process.poll() is None:
            self.status.set("Stopping match…")
            os.killpg(self.process.pid, signal.SIGINT)
            self.stop_button.configure(state="disabled")

    def _poll_events(self) -> None:
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == "output":
                    self._append(str(value))
                else:
                    return_code = int(value)
                    self.process = None
                    self.start_button.configure(state="normal")
                    self.stop_button.configure(state="disabled")
                    self.status.set("Complete" if return_code == 0 else f"Stopped (exit {return_code})")
        except queue.Empty:
            pass
        self.root.after(100, self._poll_events)

    def _append(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text)
        self.log.see("end")
        self.log.configure(state="disabled")

    def _reveal_output(self) -> None:
        path = Path(self.variables["output"].get()).expanduser()
        target = path if path.exists() else path.parent
        if not target.exists():
            messagebox.showerror("PGN not found", f"Neither the PGN nor its folder exists:\n{path}")
            return
        try:
            if sys.platform == "darwin":
                subprocess.Popen(("open", "-R", str(path)) if path.exists() else ("open", str(target)))
            else:
                subprocess.Popen(("xdg-open", str(target if target.is_dir() else target.parent)))
        except OSError as error:
            messagebox.showerror("Could not reveal PGN", str(error))

    def _close(self) -> None:
        if self.process is not None and self.process.poll() is None:
            if not messagebox.askyesno("Match running", "Stop the match and close the window?"):
                return
            os.killpg(self.process.pid, signal.SIGINT)
        self.root.destroy()


def main() -> None:
    if not os.environ.get("DISPLAY") and sys.platform.startswith("linux"):
        raise SystemExit("A graphical display is required to run maia-benchmark-gui.")
    root = Tk()
    BenchmarkGui(root)
    root.mainloop()


if __name__ == "__main__":
    main()
