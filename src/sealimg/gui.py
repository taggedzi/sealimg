"""Minimal local GUI for Sealimg sealing workflows."""

from __future__ import annotations

import contextlib
import io
import json
import threading


def run_gui(
    *,
    config_path: str,
    default_profile: str | None = None,
    default_output_root: str | None = None,
) -> int:
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox, ttk
    except Exception as exc:  # pragma: no cover - depends on runtime environment
        raise RuntimeError("Tkinter is required for sealimg gui") from exc

    root = tk.Tk()
    root.title("Sealimg")
    root.geometry("860x600")

    paths: list[str] = []
    running = {"active": False}

    config_var = tk.StringVar(value=config_path)
    profile_var = tk.StringVar(value=default_profile or "")
    output_root_var = tk.StringVar(value=default_output_root or "")
    recipient_var = tk.StringVar(value="")
    passphrase_var = tk.StringVar(value="")
    recursive_var = tk.BooleanVar(value=True)
    wm_visible_var = tk.BooleanVar(value=True)
    wm_invisible_var = tk.BooleanVar(value=False)
    bundle_var = tk.BooleanVar(value=False)
    no_embed_var = tk.BooleanVar(value=False)

    frame = ttk.Frame(root, padding=12)
    frame.pack(fill="both", expand=True)

    controls = ttk.Frame(frame)
    controls.pack(fill="x")

    ttk.Label(controls, text="Config path").grid(row=0, column=0, sticky="w")
    ttk.Entry(controls, textvariable=config_var, width=56).grid(
        row=0, column=1, sticky="ew", padx=6
    )
    ttk.Label(controls, text="Profile").grid(row=1, column=0, sticky="w")
    ttk.Entry(controls, textvariable=profile_var, width=24).grid(
        row=1, column=1, sticky="w", padx=6
    )
    ttk.Label(controls, text="Output root").grid(row=2, column=0, sticky="w")
    ttk.Entry(controls, textvariable=output_root_var, width=56).grid(
        row=2, column=1, sticky="ew", padx=6
    )
    ttk.Label(controls, text="Recipient ID").grid(row=3, column=0, sticky="w")
    ttk.Entry(controls, textvariable=recipient_var, width=56).grid(
        row=3, column=1, sticky="ew", padx=6
    )
    ttk.Label(controls, text="Passphrase").grid(row=4, column=0, sticky="w")
    ttk.Entry(controls, textvariable=passphrase_var, width=56, show="*").grid(
        row=4, column=1, sticky="ew", padx=6
    )
    controls.columnconfigure(1, weight=1)

    flags = ttk.Frame(frame)
    flags.pack(fill="x", pady=(8, 6))
    ttk.Checkbutton(flags, text="Recursive", variable=recursive_var).grid(
        row=0, column=0, sticky="w"
    )
    ttk.Checkbutton(flags, text="Visible watermark", variable=wm_visible_var).grid(
        row=0, column=1, sticky="w", padx=10
    )
    ttk.Checkbutton(flags, text="Invisible watermark", variable=wm_invisible_var).grid(
        row=0, column=2, sticky="w", padx=10
    )
    ttk.Checkbutton(flags, text="Bundle ZIP", variable=bundle_var).grid(
        row=0, column=3, sticky="w", padx=10
    )
    ttk.Checkbutton(flags, text="No embed", variable=no_embed_var).grid(
        row=0, column=4, sticky="w", padx=10
    )

    paths_frame = ttk.LabelFrame(frame, text="Input files or folders")
    paths_frame.pack(fill="both", expand=True, pady=(6, 6))
    listbox = tk.Listbox(paths_frame, height=10)
    listbox.pack(fill="both", expand=True, padx=8, pady=8)

    def _sync_paths() -> None:
        listbox.delete(0, tk.END)
        for item in paths:
            listbox.insert(tk.END, item)

    def _add_files() -> None:
        selected = filedialog.askopenfilenames(title="Select image files")
        if not selected:
            return
        for item in selected:
            text = str(item)
            if text not in paths:
                paths.append(text)
        _sync_paths()

    def _add_folder() -> None:
        selected = filedialog.askdirectory(title="Select folder")
        if not selected:
            return
        text = str(selected)
        if text not in paths:
            paths.append(text)
        _sync_paths()

    def _remove_selected() -> None:
        selected = sorted(listbox.curselection(), reverse=True)
        for idx in selected:
            del paths[idx]
        _sync_paths()

    btns = ttk.Frame(frame)
    btns.pack(fill="x")
    ttk.Button(btns, text="Add files", command=_add_files).pack(side="left")
    ttk.Button(btns, text="Add folder", command=_add_folder).pack(side="left", padx=6)
    ttk.Button(btns, text="Remove selected", command=_remove_selected).pack(side="left")
    ttk.Button(btns, text="Clear all", command=lambda: (paths.clear(), _sync_paths())).pack(
        side="left", padx=6
    )

    output = tk.Text(frame, height=10, wrap="word")
    output.pack(fill="both", expand=True, pady=(8, 0))

    def _append(text: str) -> None:
        output.insert(tk.END, text + "\n")
        output.see(tk.END)

    def _build_cli_args() -> list[str]:
        args = ["seal"]
        args.extend(paths)
        if recursive_var.get():
            args.append("--recursive")
        if profile_var.get().strip():
            args.extend(["--profile", profile_var.get().strip()])
        args.extend(["--wm-visible", "on" if wm_visible_var.get() else "off"])
        args.extend(["--wm-invisible", "on" if wm_invisible_var.get() else "off"])
        args.extend(["--bundle", "on" if bundle_var.get() else "off"])
        if no_embed_var.get():
            args.append("--no-embed")
        if recipient_var.get().strip():
            args.extend(["--recipient-id", recipient_var.get().strip()])
        if output_root_var.get().strip():
            args.extend(["--output-root", output_root_var.get().strip()])
        if config_var.get().strip():
            args.extend(["--config-path", config_var.get().strip()])
        if passphrase_var.get().strip():
            args.extend(["--passphrase", passphrase_var.get().strip()])
        args.append("--json")
        return args

    def _run_seal() -> None:
        if running["active"]:
            return
        if not paths:
            messagebox.showerror("Sealimg", "Add at least one file or folder.")
            return
        if not passphrase_var.get().strip():
            messagebox.showerror("Sealimg", "Passphrase is required.")
            return
        running["active"] = True
        run_btn.configure(state="disabled")
        _append("Starting seal run...")
        cli_args = _build_cli_args()

        def _worker() -> None:
            from . import cli as cli_module

            try:
                buffer = io.StringIO()
                with contextlib.redirect_stdout(buffer):
                    rc = cli_module.main(cli_args)
                text = buffer.getvalue().strip()
                payload = None
                if text:
                    for line in text.splitlines():
                        root.after(0, lambda line=line: _append(line))
                    last_line = text.splitlines()[-1]
                    try:
                        payload = json.loads(last_line)
                    except Exception:
                        payload = None
                if payload and isinstance(payload, dict):
                    count = payload.get("count", 0)
                    ok = payload.get("ok", False)
                    root.after(
                        0,
                        lambda: _append(
                            f"Finished (exit={rc}, ok={ok}, sealed_count={count})"
                        ),
                    )
                else:
                    root.after(0, lambda: _append(f"Finished (exit={rc})"))
            except Exception as exc:
                err_text = str(exc)
                root.after(0, lambda: _append(f"Error: {err_text}"))
            finally:
                root.after(0, lambda: run_btn.configure(state="normal"))
                running["active"] = False

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    run_btn = ttk.Button(btns, text="Seal now", command=_run_seal)
    run_btn.pack(side="right")

    root.mainloop()
    return 0
