"""Minimal local GUI for Sealimg sealing workflows."""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import threading
from pathlib import Path
from typing import Sequence

from .config import SealimgConfig, load_config, save_config


def has_tkinterdnd2() -> bool:
    return importlib.util.find_spec("tkinterdnd2") is not None


def detect_bootstrap_needs(config_path: str) -> tuple[bool, bool]:
    config_file = Path(config_path).expanduser()
    if not config_file.exists():
        return False, False
    try:
        cfg = load_config(config_file)
    except Exception:
        return False, True
    signing_key = Path(cfg.signing_key).expanduser()
    has_keys = signing_key.exists() and signing_key.with_suffix(".pub").exists()
    return has_keys, False


def infer_default_signer_name(config_path: str) -> str:
    config_file = Path(config_path).expanduser()
    if not config_file.exists():
        return "sealimg"
    try:
        cfg = load_config(config_file)
    except Exception:
        return "sealimg"
    author = cfg.author.strip()
    if author and author != "Your Name":
        return author
    return "sealimg"


def build_keygen_cli_args(
    *,
    config_path: str,
    passphrase: str,
    signer_name: str,
    key_name: str = "sealimg",
) -> list[str]:
    cfg_path = Path(config_path).expanduser()
    keys_dir = cfg_path.parent / "keys"
    return [
        "keygen",
        "--ed25519",
        "--name",
        signer_name,
        "--key-name",
        key_name,
        "--output-dir",
        str(keys_dir),
        "--passphrase",
        passphrase,
        "--config-path",
        str(cfg_path),
        "--write-config",
    ]


def build_seal_cli_args(
    *,
    paths: list[str],
    recursive: bool,
    profile: str,
    wm_visible: bool,
    wm_invisible: bool,
    wm_invisible_mode: str,
    bundle: bool,
    no_embed: bool,
    recipient_id: str,
    output_root: str,
    config_path: str,
    passphrase: str,
) -> list[str]:
    args = ["seal"]
    args.extend(paths)
    if recursive:
        args.append("--recursive")
    if profile.strip():
        args.extend(["--profile", profile.strip()])
    args.extend(["--wm-visible", "on" if wm_visible else "off"])
    args.extend(["--wm-invisible", "on" if wm_invisible else "off"])
    if wm_invisible_mode.strip():
        args.extend(["--wm-invisible-mode", wm_invisible_mode.strip()])
    args.extend(["--bundle", "on" if bundle else "off"])
    if no_embed:
        args.append("--no-embed")
    if recipient_id.strip():
        args.extend(["--recipient-id", recipient_id.strip()])
    if output_root.strip():
        args.extend(["--output-root", output_root.strip()])
    if config_path.strip():
        args.extend(["--config-path", config_path.strip()])
    if passphrase.strip():
        args.extend(["--passphrase", passphrase.strip()])
    args.append("--json")
    return args


def extract_last_json_object(text: str) -> dict[str, object] | None:
    if not text:
        return None
    try:
        payload = json.loads(text.splitlines()[-1])
    except Exception:
        return None
    if isinstance(payload, dict):
        return payload
    return None


def parse_dropped_paths(data: str) -> list[str]:
    text = data.strip()
    if not text:
        return []
    items: list[str] = []
    token: list[str] = []
    in_braces = False
    for ch in text:
        if ch == "{":
            if in_braces:
                token.append(ch)
            else:
                in_braces = True
            continue
        if ch == "}":
            if in_braces:
                in_braces = False
                value = "".join(token).strip()
                if value:
                    items.append(value)
                token = []
            else:
                token.append(ch)
            continue
        if ch.isspace() and not in_braces:
            value = "".join(token).strip()
            if value:
                items.append(value)
            token = []
            continue
        token.append(ch)
    value = "".join(token).strip()
    if value:
        items.append(value)
    return items


def resolve_config_dialog_start_dir(current_path: str, default_path: str) -> str:
    candidate = Path(current_path).expanduser()
    if candidate.is_dir():
        return str(candidate)
    if candidate.parent.exists():
        return str(candidate.parent)
    fallback = Path(default_path).expanduser()
    if fallback.is_dir():
        return str(fallback)
    if fallback.parent.exists():
        return str(fallback.parent)
    return str(Path.cwd())


def resolve_output_root_dialog_start_dir(current_path: str, default_path: str | None) -> str:
    candidate = Path(current_path).expanduser()
    if candidate.exists() and candidate.is_dir():
        return str(candidate)
    if candidate.parent.exists():
        return str(candidate.parent)
    if default_path:
        fallback = Path(default_path).expanduser()
        if fallback.exists() and fallback.is_dir():
            return str(fallback)
        if fallback.parent.exists():
            return str(fallback.parent)
    return str(Path.cwd())


def select_profile_name(
    available_profiles: list[str],
    requested: str | None = None,
    *,
    preferred: str = "web",
) -> str:
    if requested and requested in available_profiles:
        return requested
    if preferred in available_profiles:
        return preferred
    if available_profiles:
        return available_profiles[0]
    return preferred


def load_profile_choices(
    config_path: str,
    requested: str | None = None,
) -> tuple[list[str], str]:
    cfg_path = Path(config_path).expanduser()
    if not cfg_path.exists():
        selected = select_profile_name(["web"], requested=requested)
        return ["web"], selected
    cfg = load_config(cfg_path)
    names = sorted(cfg.profiles.keys())
    selected = select_profile_name(
        names,
        requested=requested or cfg.default_profile,
    )
    return names, selected


def upsert_profile_in_config(
    config_path: str,
    *,
    profile_name: str,
    long_edge: int,
    quality: int,
    wm_visible_enabled: bool,
    wm_invisible_enabled: bool,
    wm_invisible_mode: str,
    wm_style: str,
    wm_text: str,
    make_default: bool = False,
) -> None:
    cfg_path = Path(config_path).expanduser()
    cfg = load_config(cfg_path)
    data = cfg.to_dict()
    data["profiles"][profile_name] = {
        "long_edge": int(long_edge),
        "jpeg_quality": int(quality),
        "wm_visible": {
            "enabled": bool(wm_visible_enabled),
            "style": str(wm_style),
            "text": str(wm_text),
        },
        "wm_invisible": {
            "enabled": bool(wm_invisible_enabled),
            "mode": str(wm_invisible_mode),
        },
    }
    if make_default:
        data["default_profile"] = profile_name
    save_config(cfg_path, SealimgConfig.from_dict(data))


def delete_profile_from_config(config_path: str, profile_name: str) -> str:
    cfg_path = Path(config_path).expanduser()
    cfg = load_config(cfg_path)
    data = cfg.to_dict()
    profiles = data["profiles"]
    if profile_name not in profiles:
        return data["default_profile"]
    if len(profiles) <= 1:
        raise ValueError("cannot delete the last remaining profile")
    del profiles[profile_name]
    if data["default_profile"] == profile_name:
        data["default_profile"] = select_profile_name(sorted(profiles.keys()))
    save_config(cfg_path, SealimgConfig.from_dict(data))
    return data["default_profile"]


def derive_profile_watermark_state(profile: dict[str, object] | None) -> dict[str, object]:
    data = profile or {}
    wm_visible = data.get("wm_visible", {})
    wm_invisible = data.get("wm_invisible", {})
    visible_get = getattr(wm_visible, "get", lambda *_: None)
    invisible_get = getattr(wm_invisible, "get", lambda *_: None)
    return {
        "visible_enabled": bool(visible_get("enabled", True)),
        "visible_style": str(visible_get("style", "diag-low")),
        "visible_text": str(visible_get("text", "")),
        "invisible_enabled": bool(invisible_get("enabled", False)),
        "invisible_mode": str(invisible_get("mode", "auto")),
    }


def build_gui_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sealimg-gui",
        description="Launch the local Sealimg desktop GUI.",
    )
    parser.add_argument("--config-path", default="~/.sealimg/config.yml")
    parser.add_argument("--profile", default=None)
    parser.add_argument("--output-root", default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_gui_parser().parse_args(argv)
    return run_gui(
        config_path=args.config_path,
        default_profile=args.profile,
        default_output_root=args.output_root,
    )


def run_gui(
    *,
    config_path: str,
    default_profile: str | None = None,
    default_output_root: str | None = None,
) -> int:
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox, simpledialog, ttk
    except Exception as exc:  # pragma: no cover - depends on runtime environment
        raise RuntimeError("Tkinter is required for sealimg gui") from exc

    dnd_files_token: str | None = None
    if has_tkinterdnd2():
        try:
            from tkinterdnd2 import DND_FILES, TkinterDnD

            root = TkinterDnD.Tk()
            dnd_files_token = DND_FILES
        except Exception:
            root = tk.Tk()
    else:
        root = tk.Tk()
    root.title("Sealimg")
    root.geometry("860x600")

    paths: list[str] = []
    running = {"active": False}

    config_var = tk.StringVar(value=config_path)
    profile_var = tk.StringVar(value=default_profile or "web")
    output_root_var = tk.StringVar(value=default_output_root or "")
    recipient_var = tk.StringVar(value="")
    passphrase_var = tk.StringVar(value="")
    recursive_var = tk.BooleanVar(value=True)
    wm_visible_var = tk.BooleanVar(value=True)
    wm_invisible_var = tk.BooleanVar(value=False)
    wm_invisible_mode_var = tk.StringVar(value="auto")
    wm_visible_summary_var = tk.StringVar(value="On")
    wm_invisible_summary_var = tk.StringVar(value="Off")
    wm_invisible_mode_summary_var = tk.StringVar(value="auto")
    wm_visible_style_summary_var = tk.StringVar(value="diag-low")
    wm_visible_text_summary_var = tk.StringVar(value="")
    bundle_var = tk.BooleanVar(value=False)
    no_embed_var = tk.BooleanVar(value=False)

    frame = ttk.Frame(root, padding=12)
    frame.pack(fill="both", expand=True)

    controls = ttk.Frame(frame)
    controls.pack(fill="x")

    default_config_path = config_path
    default_output_root_path = default_output_root

    ttk.Label(controls, text="Config path").grid(row=0, column=0, sticky="w")
    ttk.Entry(controls, textvariable=config_var, width=48).grid(
        row=0, column=1, sticky="ew", padx=6
    )
    def _browse_config() -> None:
        current = config_var.get().strip()
        selected = filedialog.askopenfilename(
            title="Select config file",
            initialdir=resolve_config_dialog_start_dir(current, default_config_path),
            initialfile=Path(current).name if current else Path(default_config_path).name,
            filetypes=[("YAML files", "*.yml *.yaml"), ("All files", "*.*")],
        )
        if selected:
            config_var.set(str(selected))
            _refresh_profiles(preferred="web")

    ttk.Button(controls, text="Browse...", command=_browse_config).grid(
        row=0, column=2, sticky="w"
    )
    ttk.Label(controls, text="Profile").grid(row=1, column=0, sticky="w")
    profile_combo = ttk.Combobox(controls, state="readonly", textvariable=profile_var, width=24)
    profile_combo.grid(row=1, column=1, sticky="w", padx=6)
    ttk.Label(controls, text="Output root").grid(row=2, column=0, sticky="w")
    ttk.Entry(controls, textvariable=output_root_var, width=48).grid(
        row=2, column=1, sticky="ew", padx=6
    )
    def _browse_output_root() -> None:
        current = output_root_var.get().strip()
        selected = filedialog.askdirectory(
            title="Select output root folder",
            initialdir=resolve_output_root_dialog_start_dir(current, default_output_root_path),
            mustexist=False,
        )
        if selected:
            output_root_var.set(str(selected))

    ttk.Button(controls, text="Browse...", command=_browse_output_root).grid(
        row=2, column=2, sticky="w"
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

    profile_info = ttk.LabelFrame(frame, text="Profile watermark settings (read-only)")
    profile_info.pack(fill="x", pady=(8, 6))
    ttk.Label(profile_info, text="Visible").grid(row=0, column=0, sticky="w", padx=(8, 2), pady=6)
    ttk.Label(profile_info, textvariable=wm_visible_summary_var).grid(
        row=0, column=1, sticky="w", padx=(0, 12), pady=6
    )
    ttk.Label(profile_info, text="Invisible").grid(row=0, column=2, sticky="w", padx=(0, 2), pady=6)
    ttk.Label(profile_info, textvariable=wm_invisible_summary_var).grid(
        row=0, column=3, sticky="w", padx=(0, 12), pady=6
    )
    ttk.Label(profile_info, text="Mode").grid(row=0, column=4, sticky="w", padx=(0, 2), pady=6)
    ttk.Label(profile_info, textvariable=wm_invisible_mode_summary_var).grid(
        row=0, column=5, sticky="w", padx=(0, 12), pady=6
    )
    ttk.Label(profile_info, text="Visible style").grid(
        row=1, column=0, sticky="w", padx=(8, 2), pady=(0, 6)
    )
    ttk.Label(profile_info, textvariable=wm_visible_style_summary_var).grid(
        row=1, column=1, sticky="w", columnspan=2, pady=(0, 6)
    )
    ttk.Label(profile_info, text="Visible text").grid(
        row=1, column=3, sticky="w", padx=(0, 2), pady=(0, 6)
    )
    ttk.Label(profile_info, textvariable=wm_visible_text_summary_var).grid(
        row=1, column=4, sticky="w", columnspan=2, pady=(0, 6)
    )

    flags = ttk.Frame(frame)
    flags.pack(fill="x", pady=(0, 6))
    ttk.Checkbutton(flags, text="Recursive", variable=recursive_var).grid(
        row=0, column=0, sticky="w"
    )
    ttk.Checkbutton(flags, text="Bundle ZIP", variable=bundle_var).grid(
        row=0, column=1, sticky="w", padx=10
    )
    ttk.Checkbutton(flags, text="No embed", variable=no_embed_var).grid(
        row=0, column=2, sticky="w", padx=10
    )

    paths_frame = ttk.LabelFrame(frame, text="Input files or folders")
    paths_frame.pack(fill="both", expand=True, pady=(6, 6))
    dnd_status_var = tk.StringVar(
        value="Drag and drop files/folders here when supported, or use Add files/Add folder."
    )
    ttk.Label(paths_frame, textvariable=dnd_status_var).pack(anchor="w", padx=8, pady=(8, 0))
    listbox = tk.Listbox(paths_frame, height=10)
    listbox.pack(fill="both", expand=True, padx=8, pady=8)

    def _sync_paths() -> None:
        listbox.delete(0, tk.END)
        for item in paths:
            listbox.insert(tk.END, item)

    def _add_path_items(items: list[str]) -> None:
        changed = False
        for item in items:
            text = str(item).strip()
            if not text:
                continue
            if text not in paths:
                paths.append(text)
                changed = True
        if changed:
            _sync_paths()

    def _add_files() -> None:
        selected = filedialog.askopenfilenames(title="Select image files")
        if not selected:
            return
        _add_path_items([str(item) for item in selected])

    def _add_folder() -> None:
        selected = filedialog.askdirectory(title="Select folder")
        if not selected:
            return
        _add_path_items([str(selected)])

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

    def _refresh_profiles(preferred: str | None = None) -> None:
        cfg_path = config_var.get().strip()
        try:
            names, selected = load_profile_choices(
                cfg_path,
                requested=preferred or profile_var.get(),
            )
            cfg_path_obj = Path(cfg_path).expanduser()
            cfg = load_config(cfg_path_obj) if cfg_path_obj.exists() else None
        except Exception as exc:
            messagebox.showerror("Sealimg", f"Unable to load profiles: {exc}")
            return
        profile_combo["values"] = names
        profile_var.set(selected)
        profile_data = cfg.profiles.get(selected) if cfg else {}
        state = derive_profile_watermark_state(profile_data)
        wm_visible_var.set(bool(state["visible_enabled"]))
        wm_invisible_var.set(bool(state["invisible_enabled"]))
        wm_invisible_mode_var.set(str(state["invisible_mode"]))
        wm_visible_summary_var.set("On" if wm_visible_var.get() else "Off")
        wm_invisible_summary_var.set("On" if wm_invisible_var.get() else "Off")
        wm_invisible_mode_summary_var.set(wm_invisible_mode_var.get())
        wm_visible_style_summary_var.set(str(state["visible_style"]))
        wm_visible_text_summary_var.set(str(state["visible_text"]) or "(empty)")

    def _open_profile_manager() -> None:
        cfg_path = config_var.get().strip()
        try:
            cfg = load_config(Path(cfg_path).expanduser())
        except Exception as exc:
            messagebox.showerror("Sealimg", f"Unable to load config for profile manager: {exc}")
            return

        win = tk.Toplevel(root)
        win.title("Manage Profiles")
        win.geometry("780x420")
        win.transient(root)
        win.grab_set()

        list_frame = ttk.Frame(win, padding=10)
        list_frame.pack(fill="both", expand=True)

        left = ttk.Frame(list_frame)
        left.pack(side="left", fill="y")
        right = ttk.Frame(list_frame)
        right.pack(side="left", fill="both", expand=True, padx=(12, 0))

        names = sorted(cfg.profiles.keys())
        name_var = tk.StringVar(value=select_profile_name(names, requested=cfg.default_profile))
        long_edge_var = tk.StringVar(value="2560")
        quality_var = tk.StringVar(value="82")
        wm_visible_var_local = tk.BooleanVar(value=True)
        wm_invisible_var_local = tk.BooleanVar(value=False)
        wm_invisible_mode_var_local = tk.StringVar(value="auto")
        wm_style_var = tk.StringVar(value="diag-low")
        wm_text_var = tk.StringVar(value="")
        make_default_var = tk.BooleanVar(value=False)

        lb = tk.Listbox(left, height=14, exportselection=False)
        lb.pack(fill="y", expand=True)

        def _sync_list(target: str | None = None) -> None:
            nonlocal names
            try:
                current_cfg = load_config(Path(cfg_path).expanduser())
            except Exception as exc:
                messagebox.showerror("Sealimg", f"Unable to reload config: {exc}")
                return
            names = sorted(current_cfg.profiles.keys())
            lb.delete(0, tk.END)
            for n in names:
                label = f"{n} (default)" if n == current_cfg.default_profile else n
                lb.insert(tk.END, label)
            selected_name = select_profile_name(names, requested=target or name_var.get())
            name_var.set(selected_name)
            if selected_name in names:
                idx = names.index(selected_name)
                lb.selection_clear(0, tk.END)
                lb.selection_set(idx)
                lb.see(idx)
                _load_selected()

        def _load_selected(_event=None) -> None:
            selected = lb.curselection()
            if not selected:
                return
            idx = selected[0]
            if idx >= len(names):
                return
            n = names[idx]
            try:
                current_cfg = load_config(Path(cfg_path).expanduser())
            except Exception as exc:
                messagebox.showerror("Sealimg", f"Unable to load selected profile: {exc}")
                return
            p = current_cfg.profiles.get(n, {})
            name_var.set(n)
            long_edge_var.set(str(p.get("long_edge", 2560)))
            quality_var.set(str(p.get("jpeg_quality", 82)))
            wm_visible = p.get("wm_visible", {})
            wm_invisible = p.get("wm_invisible", {})
            wm_visible_var_local.set(bool(wm_visible.get("enabled", True)))
            wm_invisible_var_local.set(bool(wm_invisible.get("enabled", False)))
            wm_invisible_mode_var_local.set(str(wm_invisible.get("mode", "auto")))
            wm_style_var.set(str(wm_visible.get("style", "diag-low")))
            wm_text_var.set(str(wm_visible.get("text", "")))
            make_default_var.set(current_cfg.default_profile == n)

        lb.bind("<<ListboxSelect>>", _load_selected)

        ttk.Label(right, text="Profile name").grid(row=0, column=0, sticky="w")
        ttk.Entry(right, textvariable=name_var, width=28).grid(row=0, column=1, sticky="w", padx=6)
        ttk.Checkbutton(right, text="Set as default", variable=make_default_var).grid(
            row=0, column=2, sticky="w", padx=8
        )

        ttk.Label(right, text="Long edge").grid(row=1, column=0, sticky="w")
        ttk.Entry(right, textvariable=long_edge_var, width=12).grid(
            row=1, column=1, sticky="w", padx=6
        )
        ttk.Label(right, text="JPEG quality").grid(row=2, column=0, sticky="w")
        ttk.Entry(right, textvariable=quality_var, width=12).grid(
            row=2, column=1, sticky="w", padx=6
        )

        ttk.Checkbutton(right, text="Visible watermark", variable=wm_visible_var_local).grid(
            row=3, column=0, sticky="w"
        )
        ttk.Checkbutton(right, text="Invisible watermark", variable=wm_invisible_var_local).grid(
            row=3, column=1, sticky="w"
        )
        ttk.Label(right, text="Invisible mode").grid(row=4, column=0, sticky="w")
        ttk.Combobox(
            right,
            state="readonly",
            values=("auto", "image-id", "recipient", "owner"),
            textvariable=wm_invisible_mode_var_local,
            width=14,
        ).grid(row=4, column=1, sticky="w", padx=6)

        ttk.Label(right, text="Visible style").grid(row=5, column=0, sticky="w")
        ttk.Entry(right, textvariable=wm_style_var, width=20).grid(
            row=5, column=1, sticky="w", padx=6
        )
        ttk.Label(right, text="Visible text").grid(row=6, column=0, sticky="w")
        ttk.Entry(right, textvariable=wm_text_var, width=48).grid(
            row=6, column=1, columnspan=2, sticky="ew", padx=6
        )
        right.columnconfigure(2, weight=1)

        btn_row = ttk.Frame(right)
        btn_row.grid(row=7, column=0, columnspan=3, sticky="w", pady=(12, 0))

        def _add_new() -> None:
            suggested = simpledialog.askstring("New profile", "Profile name:", parent=win)
            if not suggested:
                return
            name_var.set(suggested.strip())
            long_edge_var.set("2560")
            quality_var.set("82")
            wm_visible_var_local.set(True)
            wm_invisible_var_local.set(False)
            wm_invisible_mode_var_local.set("auto")
            wm_style_var.set("diag-low")
            wm_text_var.set("")
            make_default_var.set(False)

        def _save_profile() -> None:
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("Sealimg", "Profile name is required.", parent=win)
                return
            try:
                upsert_profile_in_config(
                    cfg_path,
                    profile_name=name,
                    long_edge=int(long_edge_var.get().strip()),
                    quality=int(quality_var.get().strip()),
                    wm_visible_enabled=wm_visible_var_local.get(),
                    wm_invisible_enabled=wm_invisible_var_local.get(),
                    wm_invisible_mode=wm_invisible_mode_var_local.get().strip(),
                    wm_style=wm_style_var.get().strip() or "diag-low",
                    wm_text=wm_text_var.get(),
                    make_default=make_default_var.get(),
                )
            except Exception as exc:
                messagebox.showerror("Sealimg", f"Unable to save profile: {exc}", parent=win)
                return
            _sync_list(target=name)
            _refresh_profiles(preferred=name)

        def _delete_profile() -> None:
            name = name_var.get().strip()
            if not name:
                return
            if not messagebox.askyesno("Delete profile", f"Delete profile '{name}'?", parent=win):
                return
            try:
                new_default = delete_profile_from_config(cfg_path, name)
            except Exception as exc:
                messagebox.showerror("Sealimg", f"Unable to delete profile: {exc}", parent=win)
                return
            _sync_list(target=new_default)
            _refresh_profiles(preferred=new_default)

        ttk.Button(btn_row, text="Add new...", command=_add_new).pack(side="left")
        ttk.Button(btn_row, text="Save", command=_save_profile).pack(side="left", padx=6)
        ttk.Button(btn_row, text="Delete", command=_delete_profile).pack(side="left")
        ttk.Button(btn_row, text="Close", command=win.destroy).pack(side="left", padx=6)

        _sync_list()

    ttk.Button(controls, text="Manage...", command=_open_profile_manager).grid(
        row=1, column=2, sticky="w"
    )
    _refresh_profiles(preferred=default_profile or "web")
    profile_combo.bind(
        "<<ComboboxSelected>>",
        lambda _event: _refresh_profiles(preferred=profile_var.get()),
    )

    def _build_cli_args() -> list[str]:
        return build_seal_cli_args(
            paths=paths,
            recursive=recursive_var.get(),
            profile=profile_var.get(),
            wm_visible=wm_visible_var.get(),
            wm_invisible=wm_invisible_var.get(),
            wm_invisible_mode=wm_invisible_mode_var.get(),
            bundle=bundle_var.get(),
            no_embed=no_embed_var.get(),
            recipient_id=recipient_var.get(),
            output_root=output_root_var.get(),
            config_path=config_var.get(),
            passphrase=passphrase_var.get(),
        )

    def _enable_drag_drop() -> bool:
        if not dnd_files_token:
            return False
        try:
            listbox.drop_target_register(dnd_files_token)
            listbox.dnd_bind("<<Drop>>", _on_drop)
        except Exception:
            return False
        return True

    def _on_drop(event) -> None:
        dropped = parse_dropped_paths(getattr(event, "data", ""))
        _add_path_items(dropped)
        if dropped:
            _append(f"Added {len(dropped)} dropped item(s).")

    def _ensure_setup() -> bool:
        cfg_path = config_var.get().strip()
        has_keys, config_invalid = detect_bootstrap_needs(cfg_path)
        if config_invalid:
            messagebox.showerror(
                "Sealimg",
                "Config file is invalid and cannot be read. Fix it or remove it and try again.",
            )
            return False
        if has_keys:
            _append("Setup check: signing key is available.")
            return True
        if not passphrase_var.get().strip():
            messagebox.showerror("Sealimg", "Passphrase is required for key generation.")
            return False
        consent = messagebox.askyesno(
            "Sealimg setup",
            "No signing key was found for this config. Generate one now?",
        )
        if not consent:
            _append("Canceled: signing key is required to seal images.")
            return False
        signer = infer_default_signer_name(cfg_path)
        signer = simpledialog.askstring(
            "Signer name",
            "Signer display name for the new key:",
            initialvalue=signer,
        )
        if signer is None or not signer.strip():
            _append("Canceled: signer name is required for key generation.")
            return False
        _append("Generating signing key and initializing config...")
        from . import cli as cli_module

        keygen_args = build_keygen_cli_args(
            config_path=cfg_path,
            passphrase=passphrase_var.get().strip(),
            signer_name=signer.strip(),
        )
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            keygen_rc = cli_module.main(keygen_args)
        text = buffer.getvalue().strip()
        if text:
            for line in text.splitlines():
                _append(line)
        if keygen_rc != 0:
            messagebox.showerror("Sealimg", "Key generation failed. See output for details.")
            return False
        _append("Key generation complete.")
        return True

    def _run_setup() -> None:
        if running["active"]:
            return
        _ensure_setup()

    def _run_seal() -> None:
        if running["active"]:
            return
        if not paths:
            messagebox.showerror("Sealimg", "Add at least one file or folder.")
            return
        if not _ensure_setup():
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
                payload: dict[str, object] | None = None
                if text:
                    for line in text.splitlines():
                        root.after(0, lambda line=line: _append(line))
                    payload = extract_last_json_object(text)
                if payload:
                    count = payload.get("count", 0)
                    ok = payload.get("ok", False)
                    errors = payload.get("errors", [])
                    if isinstance(errors, list):
                        for err in errors:
                            if not isinstance(err, dict):
                                continue
                            path = err.get("input", "<unknown>")
                            code = err.get("code", "error")
                            msg = err.get("message", "")
                            root.after(
                                0,
                                lambda path=path, code=code, msg=msg: _append(
                                    f"Error [{code}] {path}: {msg}"
                                ),
                            )
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

    setup_btn = ttk.Button(btns, text="Setup keys", command=_run_setup)
    setup_btn.pack(side="right", padx=(0, 6))
    run_btn = ttk.Button(btns, text="Seal now", command=_run_seal)
    run_btn.pack(side="right")

    if _enable_drag_drop():
        dnd_status_var.set("Drag and drop is enabled on this system.")
    else:
        dnd_status_var.set(
            "Drag and drop is unavailable. Install tkinterdnd2 or use Add files/Add folder."
        )

    root.mainloop()
    return 0
