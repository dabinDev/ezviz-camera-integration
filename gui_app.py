import os
import time
import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime
from tkinter import ttk, filedialog
from urllib.parse import urljoin
import threading
import requests
import json


def _configure_vlc_on_windows() -> None:
    if os.name != "nt":
        return

    candidates = []
    env_dir = os.getenv("VLC_DIR")
    if env_dir:
        candidates.append(env_dir)

    candidates.extend(
        [
            r"C:\\Program Files\\VideoLAN\\VLC",
            r"C:\\Program Files (x86)\\VideoLAN\\VLC",
            r"D:\\VideoLAN\\VLC",
            r"D:\\VideoLAN",
        ]
    )

    for d in candidates:
        if d and os.path.isdir(d):
            try:
                os.add_dll_directory(d)
            except Exception:
                pass
            if not os.getenv("VLC_PLUGIN_PATH"):
                plugin_dir = os.path.join(d, "plugins")
                if os.path.isdir(plugin_dir):
                    os.environ["VLC_PLUGIN_PATH"] = plugin_dir


_configure_vlc_on_windows()

try:
    import vlc
except Exception as e:
    _vlc_import_error = e
    vlc = None

from ezviz_auth import get_access_token
from ezviz_device import (
    disable_device_encrypt,
    enable_device_encrypt,
    get_device_list,
    get_device_info,
    get_device_capacity,
    get_device_camera_list,
    get_device_status,
    get_sound_switch_status,
    set_sound_switch,
    get_scene_switch_status,
    set_scene_switch,
    get_live_url,
    list_record_files_by_time,
    ptz_start,
    ptz_stop,
    capture_picture,
    set_device_defence,
)


class EzvizDesktopApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Ezviz Desktop Client")
        self.root.geometry("1100x700")

        self.app_key = os.getenv("EZVIZ_APP_KEY")
        self.app_secret = os.getenv("EZVIZ_APP_SECRET")
        if not self.app_key or not self.app_secret:
            messagebox.showerror(
                "缺少配置",
                "缺少环境变量 EZVIZ_APP_KEY / EZVIZ_APP_SECRET。\n\n"
                "请先在系统环境变量中设置，或在 PowerShell 中临时设置：\n"
                "$env:EZVIZ_APP_KEY='你的APP_KEY'\n"
                "$env:EZVIZ_APP_SECRET='你的APP_SECRET'",
            )
            raise RuntimeError("缺少环境变量 EZVIZ_APP_KEY / EZVIZ_APP_SECRET")

        self.token = None
        self.devices = []

        self._current_device_serial = None
        self._current_channel_no = None
        self._current_validate_code = None
        self._current_url = None
        self._current_expire_ts = None
        self._refresh_job = None

        if vlc is None:
            messagebox.showerror(
                "VLC 未安装/未找到",
                "无法加载 VLC 播放组件（缺少 libvlc.dll）。\n\n"
                "请安装 VLC 播放器（VideoLAN VLC）。\n"
                "安装后如仍报错，可设置环境变量 VLC_DIR 指向 VLC 安装目录，例如：\n"
                "C:\\Program Files\\VideoLAN\\VLC\n\n"
                f"错误详情: {_vlc_import_error}",
            )
            raise RuntimeError("VLC 未安装/未找到（缺少 libvlc.dll）") from _vlc_import_error

        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

        self._vlc_events = self.player.event_manager()
        self._vlc_events.event_attach(vlc.EventType.MediaPlayerEncounteredError, self._on_vlc_error)

        self._build_ui()
        self._bind_events()

    def _format_ms_ts(self, value) -> str:
        try:
            if value is None:
                return ""
            if isinstance(value, str) and value.isdigit():
                value = int(value)
            if isinstance(value, (int, float)):
                # Heuristic: treat 13-digit values as milliseconds.
                if value > 10_000_000_000:
                    dt = datetime.fromtimestamp(value / 1000)
                else:
                    dt = datetime.fromtimestamp(value)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            return str(value)
        except Exception:
            return str(value)

    def _toast(self, text: str, duration_ms: int = 2200):
        try:
            win = tk.Toplevel(self.root)
            win.overrideredirect(True)
            win.attributes("-topmost", True)
            label = tk.Label(win, text=text, bg="#333333", fg="white", padx=12, pady=8, justify=tk.LEFT)
            label.pack()

            win.update_idletasks()
            x = self.root.winfo_rootx() + self.root.winfo_width() - win.winfo_width() - 20
            y = self.root.winfo_rooty() + self.root.winfo_height() - win.winfo_height() - 60
            win.geometry(f"+{x}+{y}")

            self.root.after(duration_ms, win.destroy)
        except Exception:
            pass

    def _run_bg(self, work_fn, ok_text: str | None = None, err_prefix: str | None = None, on_ok=None):
        def runner():
            try:
                res = work_fn()
                if ok_text:
                    self.root.after(0, lambda: self._toast(ok_text))
                if on_ok is not None:
                    self.root.after(0, lambda: on_ok(res))
            except Exception as e:
                prefix = (err_prefix + ": ") if err_prefix else ""
                msg = prefix + str(e)
                lower = msg.lower()
                if "4018" in lower or "h264" in lower:
                    msg = (
                        msg
                        + "\n\n建议: 在萤石云APP/设备设置里把视频编码切换为 H.264。\n"
                        + "部分设备/码流可能不支持切换或需要关闭H.265/HEVC。"
                    )
                self.root.after(0, lambda m=msg: self._toast(m, duration_ms=5000))

        threading.Thread(target=runner, daemon=True).start()

    def _build_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_live = ttk.Frame(self.notebook)
        self.tab_record = ttk.Frame(self.notebook)
        self.tab_control = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_live, text="直播")
        self.notebook.add(self.tab_record, text="录像/下载")
        self.notebook.add(self.tab_control, text="相机控制")

        # Live tab
        self.left = tk.Frame(self.tab_live, width=360)
        self.left.pack(side=tk.LEFT, fill=tk.Y)

        self.right = tk.Frame(self.tab_live)
        self.right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.btn_refresh = tk.Button(self.left, text="刷新设备列表", command=self.refresh_devices)
        self.btn_refresh.pack(fill=tk.X, padx=10, pady=(10, 6))

        self.devices_list = tk.Listbox(self.left)
        self.devices_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.btn_play = tk.Button(self.left, text="播放选中设备", command=self.play_selected)
        self.btn_play.pack(fill=tk.X, padx=10, pady=(0, 6))

        self.btn_stop = tk.Button(self.left, text="停止", command=self.stop)
        self.btn_stop.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.video_panel = tk.Frame(self.right, bg="black")
        self.video_panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Control tab
        self.ctrl_left = tk.Frame(self.tab_control, width=420)
        self.ctrl_left.pack(side=tk.LEFT, fill=tk.Y)
        self.ctrl_right = tk.Frame(self.tab_control)
        self.ctrl_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Label(self.ctrl_left, text="设备:").pack(anchor="w", padx=10, pady=(10, 6))
        self.ctrl_device_var = tk.StringVar(value="")
        self.ctrl_device_combo = ttk.Combobox(self.ctrl_left, textvariable=self.ctrl_device_var, state="readonly", width=34)
        self.ctrl_device_combo.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.ctrl_status_box = tk.LabelFrame(self.ctrl_left, text="状态")
        self.ctrl_status_box.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.cam_status_var = tk.StringVar(value="未选择设备")
        self.cam_status_label = tk.Label(self.ctrl_status_box, textvariable=self.cam_status_var, justify=tk.LEFT, anchor="w")
        self.cam_status_label.pack(fill=tk.X, padx=8, pady=8)

        self.btn_refresh_status = tk.Button(self.ctrl_status_box, text="刷新状态", command=self.refresh_camera_status)
        self.btn_refresh_status.pack(fill=tk.X, padx=8, pady=(0, 8))

        self.ctrl_actions_box = tk.LabelFrame(self.ctrl_left, text="控制")
        self.ctrl_actions_box.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.btn_arm = tk.Button(self.ctrl_actions_box, text="布防(开启)", command=lambda: self.set_defence(True))
        self.btn_disarm = tk.Button(self.ctrl_actions_box, text="撤防(关闭)", command=lambda: self.set_defence(False))
        self.btn_encrypt_on = tk.Button(self.ctrl_actions_box, text="开启加密", command=self.encrypt_on)
        self.btn_encrypt_off = tk.Button(self.ctrl_actions_box, text="关闭加密", command=self.encrypt_off)
        self.btn_arm.pack(fill=tk.X, padx=8, pady=(8, 6))
        self.btn_disarm.pack(fill=tk.X, padx=8, pady=(0, 6))
        self.btn_encrypt_on.pack(fill=tk.X, padx=8, pady=(0, 6))
        self.btn_encrypt_off.pack(fill=tk.X, padx=8, pady=(0, 8))

        self.ctrl_switch_box = tk.LabelFrame(self.ctrl_left, text="开关")
        self.ctrl_switch_box.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.sound_var = tk.IntVar(value=0)
        self.scene_var = tk.IntVar(value=0)
        self.chk_sound = tk.Checkbutton(self.ctrl_switch_box, text="提示音(配网/重启)", variable=self.sound_var, command=self.toggle_sound)
        self.chk_scene = tk.Checkbutton(self.ctrl_switch_box, text="镜头遮蔽(隐私模式)", variable=self.scene_var, command=self.toggle_scene)
        self.chk_sound.pack(anchor="w", padx=8, pady=(8, 4))
        self.chk_scene.pack(anchor="w", padx=8, pady=(0, 8))

        self.btn_refresh_misc = tk.Button(self.ctrl_switch_box, text="刷新开关/能力", command=self.refresh_misc)
        self.btn_refresh_misc.pack(fill=tk.X, padx=8, pady=(0, 8))

        self.ctrl_ptz_box = tk.LabelFrame(self.ctrl_left, text="云台(PTZ)")
        self.ctrl_ptz_box.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.ptz_speed_var = tk.IntVar(value=1)
        tk.Label(self.ctrl_ptz_box, text="速度(1-8):").pack(anchor="w", padx=8, pady=(8, 0))
        self.ptz_speed = ttk.Spinbox(self.ctrl_ptz_box, from_=1, to=8, textvariable=self.ptz_speed_var, width=8)
        self.ptz_speed.pack(anchor="w", padx=8, pady=(0, 8))

        self.ptz_grid = tk.Frame(self.ctrl_ptz_box)
        self.ptz_grid.pack(padx=8, pady=(0, 8))
        # Directions per Ezviz: 0-up,1-down,2-left,3-right,8-zoom in,9-zoom out
        self._ptz_buttons = []
        self._ptz_add_btn("上", 0, 0, 1)
        self._ptz_add_btn("左", 2, 1, 0)
        self._ptz_add_btn("右", 3, 1, 2)
        self._ptz_add_btn("下", 1, 2, 1)
        self._ptz_add_btn("变焦+", 8, 3, 0)
        self._ptz_add_btn("变焦-", 9, 3, 2)

        self.ctrl_capture_box = tk.LabelFrame(self.ctrl_left, text="抓拍")
        self.ctrl_capture_box.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.btn_capture = tk.Button(self.ctrl_capture_box, text="抓拍并保存", command=self.capture_and_save)
        self.btn_capture.pack(fill=tk.X, padx=8, pady=8)

        self.ctrl_log = tk.Text(self.ctrl_right, height=10)
        self.ctrl_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Record tab
        self.record_top = tk.Frame(self.tab_record)
        self.record_top.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        tk.Label(self.record_top, text="设备:").pack(side=tk.LEFT)
        self.record_device_var = tk.StringVar(value="")
        self.record_device_combo = ttk.Combobox(self.record_top, textvariable=self.record_device_var, state="readonly", width=28)
        self.record_device_combo.pack(side=tk.LEFT, padx=(6, 10))

        tk.Label(self.record_top, text="开始(YYYY-mm-dd HH:MM:SS):").pack(side=tk.LEFT)
        self.record_start_var = tk.StringVar(value=time.strftime("%Y-%m-%d 00:00:00"))
        self.record_start_entry = ttk.Entry(self.record_top, textvariable=self.record_start_var, width=20)
        self.record_start_entry.pack(side=tk.LEFT, padx=(6, 10))

        tk.Label(self.record_top, text="结束:").pack(side=tk.LEFT)
        self.record_end_var = tk.StringVar(value=time.strftime("%Y-%m-%d %H:%M:%S"))
        self.record_end_entry = ttk.Entry(self.record_top, textvariable=self.record_end_var, width=20)
        self.record_end_entry.pack(side=tk.LEFT, padx=(6, 10))

        tk.Label(self.record_top, text="类型:").pack(side=tk.LEFT)
        self._rectype_map = {"全部": 0, "连续": 1, "事件": 2}
        self._rectype_rev = {v: k for k, v in self._rectype_map.items()}
        self.record_rectype_var = tk.StringVar(value="全部")
        self.record_rectype_combo = ttk.Combobox(
            self.record_top,
            textvariable=self.record_rectype_var,
            state="readonly",
            width=8,
            values=list(self._rectype_map.keys()),
        )
        self.record_rectype_combo.pack(side=tk.LEFT, padx=(6, 10))

        self.btn_record_query = ttk.Button(self.record_top, text="查询录像", command=self.query_records)
        self.btn_record_query.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_record_play = ttk.Button(self.record_top, text="回放", command=self.play_selected_record)
        self.btn_record_play.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_record_download = ttk.Button(self.record_top, text="下载", command=self.download_selected_record)
        self.btn_record_download.pack(side=tk.LEFT)

        self.record_list = tk.Listbox(self.tab_record)
        self.record_list.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.status_var = tk.StringVar(value="就绪")
        self.status = tk.Label(self.root, textvariable=self.status_var, anchor="w")
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

        self.root.update_idletasks()
        self.player.set_hwnd(self.video_panel.winfo_id())

    def _bind_events(self):
        self.devices_list.bind("<Double-Button-1>", lambda _e: self.play_selected())
        self.record_list.bind("<Double-Button-1>", lambda _e: self.play_selected_record())
        self.devices_list.bind("<<ListboxSelect>>", lambda _e: self.update_camera_status())
        self.ctrl_device_combo.bind("<<ComboboxSelected>>", lambda _e: self.update_camera_status())
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def set_status(self, text: str):
        self.status_var.set(text)
        self.root.update_idletasks()

    def _clear_refresh_job(self):
        if self._refresh_job is not None:
            try:
                self.root.after_cancel(self._refresh_job)
            except Exception:
                pass
            self._refresh_job = None

    def _schedule_refresh(self, delay_ms: int):
        self._clear_refresh_job()
        self._refresh_job = self.root.after(delay_ms, self._refresh_stream_if_needed)

    def _ensure_token(self):
        if self.token:
            return
        self.set_status("获取 AccessToken...")
        self.token = get_access_token(self.app_key, self.app_secret)

    def refresh_devices(self):
        try:
            self._ensure_token()
            self.set_status("获取设备列表...")
            self.devices = get_device_list(self.token) or []

            self.devices_list.delete(0, tk.END)
            for d in self.devices:
                name = d.get("deviceName") or d.get("deviceSerial")
                serial = d.get("deviceSerial")
                status = "在线" if d.get("status") == 1 else "离线"
                self.devices_list.insert(tk.END, f"{name} ({serial}) - {status}")

            self.record_device_combo["values"] = [
                f"{(d.get('deviceName') or d.get('deviceSerial'))} ({d.get('deviceSerial')})" for d in self.devices
            ]
            self.ctrl_device_combo["values"] = self.record_device_combo["values"]
            if self.devices and not self.record_device_var.get():
                self.record_device_var.set(self.record_device_combo["values"][0])
            if self.devices and not self.ctrl_device_var.get():
                self.ctrl_device_var.set(self.ctrl_device_combo["values"][0])

            self.set_status(f"设备数量: {len(self.devices)}")
            self.update_camera_status()
        except Exception as e:
            messagebox.showerror("错误", str(e))
            self.set_status("错误")

    def _get_selected_device(self) -> dict | None:
        idxs = self.devices_list.curselection()
        if not idxs:
            # fallback to control tab selection
            val = getattr(self, "ctrl_device_var", tk.StringVar(value="")).get()
            if val and "(" in val and ")" in val:
                serial = val[val.rfind("(") + 1 : val.rfind(")")]
                for d in self.devices:
                    if d.get("deviceSerial") == serial:
                        return d
            return None
        idx = idxs[0]
        if idx < 0 or idx >= len(self.devices):
            return None
        return self.devices[idx]

    def update_camera_status(self):
        d = self._get_selected_device()
        if not d:
            self.cam_status_var.set("未选择设备")
            return
        serial = d.get("deviceSerial")
        name = d.get("deviceName") or serial
        online = "在线" if d.get("status") == 1 else "离线"
        defence = "布防" if d.get("defence") == 1 else "撤防"
        encrypt = "加密" if d.get("isEncrypt") == 1 else "不加密"
        extra = ""
        if hasattr(self, "_last_device_status") and isinstance(self._last_device_status, dict):
            ds = self._last_device_status
            # Show a few common fields if present.
            parts = []
            for k in ("status", "defence", "sleep", "deviceSerial", "channelNo", "alarmSound", "onlineStatus"):
                if k in ds and ds.get(k) is not None:
                    parts.append(f"{k}: {ds.get(k)}")
            if parts:
                extra = "\n\n" + "\n".join(parts)

        self.cam_status_var.set(f"{name}\n序列号: {serial}\n状态: {online}\n布防: {defence}\n加密: {encrypt}{extra}")

    def refresh_camera_status(self):
        self._ensure_token()
        d = self._get_selected_device()
        if not d:
            self._toast("请先选择设备")
            return
        serial = d.get("deviceSerial")
        channel_no = self._get_channel_no(d)

        def work():
            return get_device_status(self.token, serial, channel_no)

        def on_ok(res):
            self._last_device_status = res
            self.update_camera_status()

        self._run_bg(work, ok_text="状态已刷新", err_prefix="刷新状态失败", on_ok=on_ok)

    def refresh_misc(self):
        self._ensure_token()
        d = self._get_selected_device()
        if not d:
            self._toast("请先选择设备")
            return
        serial = d.get("deviceSerial")

        def work():
            info = get_device_info(self.token, serial)
            cap = get_device_capacity(self.token, serial)
            cams = get_device_camera_list(self.token, serial)
            sound = get_sound_switch_status(self.token, serial)
            scene = get_scene_switch_status(self.token, serial)
            return {"info": info, "cap": cap, "cams": cams, "sound": sound, "scene": scene}

        def on_ok(res: dict):
            self._last_device_info = res.get("info")
            self._last_device_capacity = res.get("cap")
            self._last_device_cams = res.get("cams")
            self._last_sound = res.get("sound")
            self._last_scene = res.get("scene")

            # Try to infer enable flags from returned dicts.
            sv = self._last_sound or {}
            scv = self._last_scene or {}
            # common fields: enable/status
            self.sound_var.set(1 if int(sv.get("enable") or sv.get("status") or 0) == 1 else 0)
            self.scene_var.set(1 if int(scv.get("enable") or scv.get("status") or 0) == 1 else 0)

            # Log details to the right pane.
            self._log_ctrl("--- device/info ---")
            self._log_ctrl(json.dumps(self._last_device_info or {}, ensure_ascii=False, indent=2))
            self._log_ctrl("--- device/capacity ---")
            self._log_ctrl(json.dumps(self._last_device_capacity or {}, ensure_ascii=False, indent=2))
            self._log_ctrl("--- device/camera/list ---")
            self._log_ctrl(json.dumps(self._last_device_cams or [], ensure_ascii=False, indent=2))
            self._log_ctrl("--- sound/switch/status ---")
            self._log_ctrl(json.dumps(self._last_sound or {}, ensure_ascii=False, indent=2))
            self._log_ctrl("--- scene/switch/status ---")
            self._log_ctrl(json.dumps(self._last_scene or {}, ensure_ascii=False, indent=2))

            self.update_camera_status()

        self._run_bg(work, ok_text="开关/能力已刷新", err_prefix="刷新失败", on_ok=on_ok)

    def toggle_sound(self):
        self._ensure_token()
        d = self._get_selected_device()
        if not d:
            self._toast("请先选择设备")
            return
        serial = d.get("deviceSerial")
        enable = bool(self.sound_var.get())
        self._run_bg(
            lambda: set_sound_switch(self.token, serial, enable),
            ok_text="提示音已更新",
            err_prefix="提示音设置失败",
            on_ok=lambda _r: self.refresh_misc(),
        )

    def toggle_scene(self):
        self._ensure_token()
        d = self._get_selected_device()
        if not d:
            self._toast("请先选择设备")
            return
        serial = d.get("deviceSerial")
        enable = bool(self.scene_var.get())
        self._run_bg(
            lambda: set_scene_switch(self.token, serial, enable),
            ok_text="镜头遮蔽已更新",
            err_prefix="镜头遮蔽设置失败",
            on_ok=lambda _r: self.refresh_misc(),
        )

    def set_defence(self, enable: bool):
        self._ensure_token()
        d = self._get_selected_device()
        if not d:
            self._toast("请先选择设备")
            return
        serial = d.get("deviceSerial")
        action = "布防" if enable else "撤防"
        self._run_bg(
            lambda: set_device_defence(self.token, serial, enable),
            ok_text=f"{action}成功",
            err_prefix=f"{action}失败",
            on_ok=lambda _r: self.refresh_devices(),
        )

    def encrypt_on(self):
        self._ensure_token()
        d = self._get_selected_device()
        if not d:
            self._toast("请先选择设备")
            return
        serial = d.get("deviceSerial")
        self._run_bg(
            lambda: enable_device_encrypt(self.token, serial),
            ok_text="开启加密成功",
            err_prefix="开启加密失败",
            on_ok=lambda _r: self.refresh_devices(),
        )

    def encrypt_off(self):
        self._ensure_token()
        d = self._get_selected_device()
        if not d:
            self._toast("请先选择设备")
            return
        serial = d.get("deviceSerial")
        validate_code = simpledialog.askstring("设备验证码", f"请输入 {serial} 的设备验证码(validateCode):")
        if not validate_code:
            return
        self._run_bg(
            lambda: disable_device_encrypt(self.token, serial, validate_code),
            ok_text="关闭加密成功",
            err_prefix="关闭加密失败",
            on_ok=lambda _r: self.refresh_devices(),
        )

    def _log_ctrl(self, text: str):
        try:
            self.ctrl_log.insert(tk.END, text + "\n")
            self.ctrl_log.see(tk.END)
        except Exception:
            pass

    def _ptz_add_btn(self, label: str, direction: int, r: int, c: int):
        btn = tk.Button(self.ptz_grid, text=label, width=10)
        btn.grid(row=r, column=c, padx=4, pady=4)
        btn.bind("<ButtonPress-1>", lambda _e, d=direction: self._ptz_press(d))
        btn.bind("<ButtonRelease-1>", lambda _e, d=direction: self._ptz_release(d))
        self._ptz_buttons.append(btn)

    def _ptz_press(self, direction: int):
        self._ensure_token()
        d = self._get_selected_device()
        if not d:
            return
        serial = d.get("deviceSerial")
        channel_no = self._get_channel_no(d)
        speed = int(self.ptz_speed_var.get() or 1)
        self._run_bg(
            lambda: ptz_start(self.token, serial, channel_no, direction, speed=speed),
            ok_text=None,
            err_prefix="PTZ",
            on_ok=lambda _r: self._log_ctrl(f"PTZ start dir={direction} speed={speed}"),
        )

    def _ptz_release(self, direction: int):
        self._ensure_token()
        d = self._get_selected_device()
        if not d:
            return
        serial = d.get("deviceSerial")
        channel_no = self._get_channel_no(d)
        self._run_bg(
            lambda: ptz_stop(self.token, serial, channel_no, direction),
            ok_text=None,
            err_prefix="PTZ",
            on_ok=lambda _r: self._log_ctrl(f"PTZ stop dir={direction}"),
        )

    def capture_and_save(self):
        self._ensure_token()
        d = self._get_selected_device()
        if not d:
            self._toast("请先选择设备")
            return
        serial = d.get("deviceSerial")
        channel_no = self._get_channel_no(d)

        out_path = filedialog.asksaveasfilename(
            title="保存抓拍图片",
            defaultextension=".jpg",
            filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png"), ("All Files", "*.*")],
        )
        if not out_path:
            return

        def work():
            pic_url = capture_picture(self.token, serial, channel_no)
            r = requests.get(pic_url, timeout=30)
            r.raise_for_status()
            with open(out_path, "wb") as f:
                f.write(r.content)
            return pic_url

        self._run_bg(
            work,
            ok_text="抓拍已保存",
            err_prefix="抓拍失败",
            on_ok=lambda pic_url: self._log_ctrl(f"抓拍URL: {pic_url}"),
        )

    def _get_selected_device_for_records(self) -> dict | None:
        val = self.record_device_var.get()
        if not val:
            return None
        # parse serial inside parentheses
        if "(" in val and ")" in val:
            serial = val[val.rfind("(") + 1 : val.rfind(")")]
            for d in self.devices:
                if d.get("deviceSerial") == serial:
                    return d
        return None

    def query_records(self):
        try:
            self._ensure_token()
            device = self._get_selected_device_for_records()
            if not device:
                messagebox.showinfo("提示", "请先选择设备")
                return

            device_serial = device.get("deviceSerial")
            channel_no = self._get_channel_no(device)
            start_s = self.record_start_var.get().strip()
            end_s = self.record_end_var.get().strip()
            start_dt = datetime.strptime(start_s, "%Y-%m-%d %H:%M:%S")
            end_dt = datetime.strptime(end_s, "%Y-%m-%d %H:%M:%S")
            if end_dt <= start_dt:
                messagebox.showinfo("提示", "结束时间必须大于开始时间")
                return

            self.set_status("查询录像中...")
            try:
                rec_type = self._rectype_map.get(self.record_rectype_var.get(), 0)
            except Exception:
                rec_type = 0
            files = list_record_files_by_time(self.token, device_serial, channel_no, start_dt, end_dt, rec_type=rec_type)
            self._record_items = files
            self.record_list.delete(0, tk.END)
            for it in files:
                bt_raw = it.get("startTime") or it.get("beginTime") or it.get("begin_time") or it.get("begin")
                et_raw = it.get("endTime") or it.get("stopTime") or it.get("endTime") or it.get("end")
                bt = self._format_ms_ts(bt_raw)
                et = self._format_ms_ts(et_raw)
                rec_type = it.get("recType") if "recType" in it else it.get("type")
                self.record_list.insert(tk.END, f"{bt} ~ {et}  recType={rec_type}")
            self.set_status(f"录像数量: {len(files)}")
        except Exception as e:
            messagebox.showerror("错误", str(e))
            self.set_status("错误")

    def _get_selected_record_item(self) -> dict | None:
        idxs = self.record_list.curselection()
        if not idxs:
            return None
        if not hasattr(self, "_record_items"):
            return None
        idx = idxs[0]
        if idx < 0 or idx >= len(self._record_items):
            return None
        return self._record_items[idx]

    def _extract_playable_url_from_record_item(self, item: dict) -> str | None:
        # Try common fields.
        for k in ("url", "playUrl", "playURL", "hls", "hlsHd", "downloadUrl", "downloadURL"):
            v = item.get(k)
            if isinstance(v, str) and v.startswith(("http://", "https://", "rtmp://")):
                return v
        return None

    def play_selected_record(self):
        try:
            item = self._get_selected_record_item()
            if not item:
                messagebox.showinfo("提示", "请先选择一条录像")
                return
            url = self._extract_playable_url_from_record_item(item)
            if not url:
                item_json = json.dumps(item, ensure_ascii=False, indent=2)
                try:
                    self.root.clipboard_clear()
                    self.root.clipboard_append(item_json)
                except Exception:
                    pass
                messagebox.showwarning(
                    "无法回放",
                    "当前接口返回的录像信息里没有可直接播放的 URL。\n"
                    "如果你开通了云存储/回放能力，通常会有 hls/m3u8 地址。\n"
                    "我已把该条录像 JSON 复制到剪贴板，你直接粘贴给我即可。\n\n"
                    f"{item_json}",
                )
                return
            self.set_status("回放中...")
            media = self.instance.media_new(url)
            self.player.set_media(media)
            self.player.play()
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def download_selected_record(self):
        item = self._get_selected_record_item()
        if not item:
            messagebox.showinfo("提示", "请先选择一条录像")
            return
        url = self._extract_playable_url_from_record_item(item)
        if not url or not url.endswith(".m3u8"):
            messagebox.showwarning("暂不支持", "当前仅支持下载 m3u8(HLS) 回放地址。")
            return

        out_path = filedialog.asksaveasfilename(
            title="保存为",
            defaultextension=".ts",
            filetypes=[("MPEG-TS", "*.ts"), ("All Files", "*.*")],
        )
        if not out_path:
            return

        def worker():
            try:
                self.root.after(0, lambda: self.set_status("下载中..."))
                self._download_hls_to_ts(url, out_path)
                self.root.after(0, lambda: self.set_status("下载完成"))
                self.root.after(0, lambda: messagebox.showinfo("完成", f"已保存: {out_path}"))
            except Exception as e:
                self.root.after(0, lambda: self.set_status("下载失败"))
                self.root.after(0, lambda: messagebox.showerror("下载失败", str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _download_hls_to_ts(self, m3u8_url: str, out_path: str) -> None:
        r = requests.get(m3u8_url, timeout=30)
        r.raise_for_status()
        base = m3u8_url.rsplit("/", 1)[0] + "/"
        lines = [ln.strip() for ln in r.text.splitlines() if ln.strip() and not ln.startswith("#")]
        if not lines:
            raise Exception("m3u8 解析失败：未找到分片")

        with open(out_path, "wb") as f:
            for seg in lines:
                seg_url = seg
                if not seg_url.startswith("http"):
                    seg_url = urljoin(base, seg_url)
                rs = requests.get(seg_url, timeout=60)
                rs.raise_for_status()
                f.write(rs.content)

    def _get_channel_no(self, device: dict) -> int:
        channel_list = device.get("channelList")
        if isinstance(channel_list, list) and channel_list:
            ch = channel_list[0]
            if isinstance(ch, dict) and "channelNo" in ch:
                return int(ch["channelNo"])
        return 1

    def _get_best_live_url(self, device_serial: str, channel_no: int) -> str:
        for protocol in (2, 1, 3, None):
            try:
                url = get_live_url(self.token, device_serial, channel_no, protocol=protocol)
            except TypeError:
                url = get_live_url(self.token, device_serial, channel_no)
            if isinstance(url, str) and not url.startswith("ezopen://"):
                return url
        return get_live_url(self.token, device_serial, channel_no)

    def _get_best_live_info(self, device_serial: str, channel_no: int) -> tuple[str, int | None]:
        for protocol in (2, 1, 3, None):
            try:
                url = get_live_url(self.token, device_serial, channel_no, protocol=protocol)
            except TypeError:
                url = get_live_url(self.token, device_serial, channel_no)
            if isinstance(url, str) and not url.startswith("ezopen://"):
                return url, None
        return get_live_url(self.token, device_serial, channel_no), None

    def _try_parse_expire_ts_from_url(self, url: str) -> int | None:
        if not isinstance(url, str):
            return None
        marker = "expire="
        idx = url.find(marker)
        if idx == -1:
            return None
        idx += len(marker)
        end = idx
        while end < len(url) and url[end].isdigit():
            end += 1
        try:
            return int(url[idx:end])
        except Exception:
            return None

    def _get_live_url_with_encrypt_handling(self, device_serial: str, channel_no: int) -> str:
        try:
            return self._get_best_live_url(device_serial, channel_no)
        except Exception as e:
            msg = str(e)
            if "[60019]" not in msg and "加密已开启" not in msg:
                raise

            validate_code = simpledialog.askstring(
                "需要验证码",
                f"设备({device_serial})已开启视频加密。\n请输入设备验证码(validateCode)以关闭加密后继续：",
                parent=self.root,
            )
            if not validate_code:
                raise

            self.set_status("关闭视频加密...")
            disable_device_encrypt(self.token, device_serial, validate_code.strip())

            last_err = None
            for _ in range(5):
                try:
                    return self._get_best_live_url(device_serial, channel_no)
                except Exception as retry_e:
                    last_err = retry_e
                    if "[60019]" not in str(retry_e) and "加密已开启" not in str(retry_e):
                        raise
                    time.sleep(1)

            return f"ezopen://{validate_code.strip()}@open.ys7.com/{device_serial}/{channel_no}.hd.live"

    def _refresh_stream_if_needed(self):
        self._refresh_job = None
        if not self._current_device_serial or not self._current_channel_no:
            return

        now = int(time.time())
        if self._current_expire_ts is not None:
            # refresh 60s before expiry
            if now < self._current_expire_ts - 60:
                delay = max(5, (self._current_expire_ts - 60 - now))
                self._schedule_refresh(delay * 1000)
                return

        try:
            url = self._get_live_url_with_encrypt_handling(self._current_device_serial, self._current_channel_no)
            expire_ts = self._try_parse_expire_ts_from_url(url)

            if url and url != self._current_url and not url.startswith("ezopen://"):
                media = self.instance.media_new(url)
                self.player.set_media(media)
                self.player.play()
                self._current_url = url
                self._current_expire_ts = expire_ts

            if expire_ts is not None:
                self._current_expire_ts = expire_ts
                delay = max(10, (expire_ts - 60 - int(time.time())))
                self._schedule_refresh(delay * 1000)
        except Exception:
            # retry later
            self._schedule_refresh(15_000)

    def _on_vlc_error(self, _event):
        # VLC error callbacks are not on Tk thread.
        try:
            self.root.after(0, lambda: self._schedule_refresh(500))
        except Exception:
            pass

    def play_selected(self):
        try:
            self._ensure_token()
            idxs = self.devices_list.curselection()
            if not idxs:
                messagebox.showinfo("提示", "请先选择一个设备")
                return

            device = self.devices[idxs[0]]
            device_serial = device.get("deviceSerial")
            if not device_serial:
                raise Exception("设备信息缺少 deviceSerial")
            channel_no = self._get_channel_no(device)

            # prevent duplicate clicks from re-fetching repeatedly
            if self._current_device_serial == device_serial and self._current_channel_no == channel_no and self._current_url:
                self.set_status("播放中")
                return

            self._clear_refresh_job()
            self._current_device_serial = device_serial
            self._current_channel_no = channel_no
            self._current_url = None
            self._current_expire_ts = None

            self.set_status("获取播放地址...")
            url = self._get_live_url_with_encrypt_handling(device_serial, channel_no)
            self._current_expire_ts = self._try_parse_expire_ts_from_url(url)

            if url.startswith("ezopen://"):
                messagebox.showwarning(
                    "无法直接播放",
                    "当前获取到的是 ezopen:// 播放地址。\n\n"
                    "桌面客户端内嵌 VLC 只能直接播放标准流（如 m3u8/rtmp/http-flv）。\n"
                    "你可以尝试在萤石开放平台开启标准流(HLS/RTMP)能力后再获取。\n\n"
                    f"播放地址：{url}",
                )
                self.set_status("获取到 ezopen:// 地址（无法内嵌播放）")
                return

            self.set_status("开始播放...")
            media = self.instance.media_new(url)
            self.player.set_media(media)
            self.player.play()
            self._current_url = url

            if self._current_expire_ts is not None:
                delay = max(10, (self._current_expire_ts - 60 - int(time.time())))
                self._schedule_refresh(delay * 1000)
            self.set_status(f"播放中: {device.get('deviceName') or device_serial}")
        except Exception as e:
            messagebox.showerror("错误", str(e))
            self.set_status("错误")

    def stop(self):
        try:
            self._clear_refresh_job()
            self._current_device_serial = None
            self._current_channel_no = None
            self._current_url = None
            self._current_expire_ts = None
            self.player.stop()
        finally:
            self.set_status("已停止")

    def on_close(self):
        try:
            self.stop()
        finally:
            self.root.destroy()


def main():
    root = tk.Tk()
    app = EzvizDesktopApp(root)
    app.refresh_devices()
    root.mainloop()


if __name__ == "__main__":
    main()
