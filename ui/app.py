"""
ui/app.py  (v2)
Janela principal — design flat, compacto, sem bordas arredondadas.
Stats integradas nos graficos por host.
"""

import customtkinter as ctk
from tkinter import messagebox

from core.session import PingSession
from core.reporter import export_csv, export_png, export_pdf

from ui.host_panel  import HostPanel
from ui.chart_panel import ChartPanel, WINDOW_OPTIONS
from ui.dialogs     import SettingsDialog, ExportDialog

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

APP_NAME    = "InfinityPinger"
APP_VERSION = "0.3.0"

# ── Paleta flat ───────────────────────────────────────────────
C_BG      = "#0E0F14"
C_PANEL   = "#13151F"
C_BORDER  = "#1C1E2C"
C_ACCENT  = "#00B4D8"
C_TEXT    = "#8888AA"
C_BTN     = "#1A1C28"
C_BTN_H   = "#22253A"


def _btn(master, text, cmd, width=90, color=C_BTN, hover=C_BTN_H, **kw):
    return ctk.CTkButton(
        master, text=text, command=cmd,
        width=width, height=28,
        corner_radius=0,
        fg_color=color, hover_color=hover,
        font=ctk.CTkFont(size=11),
        **kw,
    )


class App(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME}  v{APP_VERSION}")
        self.geometry("1100x680")
        self.minsize(800, 480)
        self.configure(fg_color=C_BG)

        import os
        import sys
        import ctypes

        # Garante que o Windows use o ícone do app na barra de tarefas (e não o do python/terminal)
        try:
            myappid = 'orkestrae.infinitypinger.0.3'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

        # Resolve o caminho base quer rodando via source quer rodando empacotado (PyInstaller)
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self._icon_path = os.path.join(base_dir, "icon.ico")
        if os.path.exists(self._icon_path):
            try:
                self.iconbitmap(self._icon_path)
            except Exception:
                pass

        self._interval = 1.0
        self._timeout  = 2.0
        self._session  = PingSession(interval=self._interval, timeout=self._timeout)

        self._build_toolbar()
        self._build_body()
        self._build_statusbar()

        self._chart.start_refresh()
        self._schedule_ui_update()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ═════════════════════════════════════════════════════════
    # TOOLBAR — altura 38px, flat
    # ═════════════════════════════════════════════════════════
    def _build_toolbar(self):
        tb = ctk.CTkFrame(self, fg_color=C_PANEL, height=38, corner_radius=0)
        tb.pack(fill="x", side="top")
        tb.pack_propagate(False)

        # Logo Image
        import os
        from PIL import Image
        pad_left = 12
        if hasattr(self, "_logo_path") and os.path.exists(self._logo_path):
            img = ctk.CTkImage(light_image=Image.open(self._logo_path), size=(24, 24))
            ctk.CTkLabel(tb, text="", image=img).pack(side="left", padx=(12, 4))
            pad_left = 0

        # Title: Orkestrae / InfinityPinger
        title_frame = ctk.CTkFrame(tb, fg_color="transparent")
        title_frame.pack(side="left", padx=(pad_left, 16))

        ctk.CTkLabel(
            title_frame, text="Orkestrae",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color="#666688",
            height=12
        ).pack(anchor="w", pady=(2, 0))

        ctk.CTkLabel(
            title_frame, text=APP_NAME,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=C_ACCENT,
            height=16
        ).pack(anchor="w", pady=(0, 2))

        # Divisor vertical
        ctk.CTkFrame(tb, width=1, height=20, fg_color=C_BORDER,
                     corner_radius=0).pack(side="left", pady=9)

        # Botões primários
        self._btn_start = _btn(
            tb, "▶  Iniciar", self._start_session,
            color="#0D3320", hover="#1A5532",
        )
        self._btn_start.pack(side="left", padx=(8, 2), pady=5)

        self._btn_stop = _btn(
            tb, "■  Parar", self._stop_session,
            color="#2A0A0A", hover="#4A1515",
            state="disabled",
        )
        self._btn_stop.pack(side="left", padx=2, pady=5)

        _btn(tb, "⟳  Limpar", self._clear_history, width=80
             ).pack(side="left", padx=2, pady=5)

        # Divisor
        ctk.CTkFrame(tb, width=1, height=20, fg_color=C_BORDER,
                     corner_radius=0).pack(side="left", padx=8, pady=9)

        _btn(tb, "💾  Exportar", self._open_export_dialog, width=95,
             ).pack(side="left", padx=2, pady=5)

        # Divisor
        ctk.CTkFrame(tb, width=1, height=20, fg_color=C_BORDER,
                     corner_radius=0).pack(side="left", padx=6, pady=9)

        # Seletor de janela de tempo
        ctk.CTkLabel(tb, text="Janela:",
                     font=ctk.CTkFont(size=10), text_color=C_TEXT
                     ).pack(side="left", padx=(0, 2))
        self._window_menu = ctk.CTkOptionMenu(
            tb,
            values=list(WINDOW_OPTIONS.keys()),
            command=self._on_window_change,
            width=72, height=26,
            corner_radius=0,
            fg_color=C_BTN, button_color=C_BTN_H,
            button_hover_color="#2A2D40",
            font=ctk.CTkFont(size=11),
            dropdown_font=ctk.CTkFont(size=11),
        )
        self._window_menu.set("5m")
        self._window_menu.pack(side="left", padx=2, pady=5)

        # Config fica à direita
        _btn(tb, "⚙", self._open_settings, width=34,
             ).pack(side="right", padx=(2, 10), pady=5)
        
        # Botão Sobre (?)
        _btn(tb, "?", self._show_about, width=34,
             ).pack(side="right", padx=(2, 2), pady=5)

        # Status inline na toolbar (direita)
        self._status_lbl = ctk.CTkLabel(
            tb, text="● Parado",
            font=ctk.CTkFont(size=11),
            text_color="#555577",
        )
        self._status_lbl.pack(side="right", padx=8)

    # ═════════════════════════════════════════════════════════
    # CORPO — sidebar esquerda + área de gráficos
    # ═════════════════════════════════════════════════════════
    def _build_body(self):
        body = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        body.pack(fill="both", expand=True)

        # ── Sidebar ───────────────────────────────────────────
        self._host_panel = HostPanel(
            body,
            on_add=self._add_host,
            on_remove=self._remove_host,
            on_toggle=self._toggle_host,
            fg_color=C_PANEL,
            width=190,
            corner_radius=0,
        )
        self._host_panel.pack(side="left", fill="y")

        # Borda direita da sidebar
        ctk.CTkFrame(body, width=1, fg_color=C_BORDER,
                     corner_radius=0).pack(side="left", fill="y")

        # ── Área dos gráficos ─────────────────────────────────
        self._chart = ChartPanel(
            body,
            get_snapshot=self._session.get_snapshot,
            fg_color=C_BG,
            corner_radius=0,
        )
        self._chart.pack(side="left", fill="both", expand=True)

    # ═════════════════════════════════════════════════════════
    # STATUSBAR — altura 22px
    # ═════════════════════════════════════════════════════════
    def _build_statusbar(self):
        sb = ctk.CTkFrame(self, fg_color="#0A0B10", height=22, corner_radius=0)
        sb.pack(fill="x", side="bottom")
        sb.pack_propagate(False)

        self._sb_hosts = ctk.CTkLabel(
            sb, text="Hosts: 0",
            font=ctk.CTkFont(size=9), text_color="#404060",
        )
        self._sb_hosts.pack(side="left", padx=10)

        ctk.CTkLabel(
            sb, text=f"InfinityPinger v{APP_VERSION}",
            font=ctk.CTkFont(size=9), text_color="#303050",
        ).pack(side="right", padx=10)

    # ═════════════════════════════════════════════════════════
    # AÇÕES
    # ═════════════════════════════════════════════════════════
    def _add_host(self, host: str) -> bool:
        return self._session.add_host(host)

    def _remove_host(self, host: str):
        self._session.remove_host(host)

    def _on_window_change(self, key: str):
        self._chart.set_window(key)

    def _toggle_host(self, host: str) -> bool:
        """Pausa ou retoma host. Retorna True se agora esta rodando."""
        if self._session.is_paused(host):
            self._session.resume_host(host)
            return True   # agora rodando
        else:
            self._session.pause_host(host)
            return False  # agora pausado

    def _start_session(self):
        if not self._session.hosts:
            messagebox.showwarning(
                "Sem hosts", "Adicione ao menos um host antes de iniciar."
            )
            return
        self._session.start()
        self._chart.start_refresh()
        self._btn_start.configure(state="disabled")
        self._btn_stop.configure(state="normal")
        self._status_lbl.configure(text="● Rodando", text_color=C_ACCENT)

    def _stop_session(self):
        self._session.stop()
        self._btn_start.configure(state="normal")
        self._btn_stop.configure(state="disabled")
        self._status_lbl.configure(text="● Parado", text_color="#883333")

    def _clear_history(self):
        self._session.clear_history()

    def _open_export_dialog(self):
        snap = self._session.get_snapshot()
        if not snap:
            messagebox.showwarning("Sem dados", "Nenhum dado para exportar.")
            return
        ExportDialog(
            self, snap,
            export_csv_fn=export_csv,
            export_png_fn=export_png,
            export_pdf_fn=export_pdf,
        )

    def _open_settings(self):
        SettingsDialog(
            self,
            current_interval=self._interval,
            current_timeout=self._timeout,
            on_apply=self._apply_settings,
        )

    def _show_about(self):
        import webbrowser
        import os
        import sys
        from PIL import Image, ImageTk
        from datetime import datetime

        top = ctk.CTkToplevel(self)
        top.title("Sobre o InfinityPinger")
        top.geometry("400x380")
        top.resizable(False, False)
        top.configure(fg_color=C_BG)
        top.attributes("-topmost", True)
        
        # Centralizar na tela pai
        top.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 400) // 2
        y = self.winfo_y() + (self.winfo_height() - 380) // 2
        top.geometry(f"+{x}+{y}")

        # Adicionar o icone do titulo se disponivel
        if hasattr(self, '_icon_path') and os.path.exists(self._icon_path):
            try:
                top.after(200, lambda: top.iconbitmap(self._icon_path))
            except Exception:
                pass

        # Container principal
        frame = ctk.CTkFrame(top, fg_color=C_PANEL, corner_radius=8)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Logo centralizada
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logo.png")
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            logo_path = os.path.join(sys._MEIPASS, "logo.png")

        if os.path.exists(logo_path):
            img = ctk.CTkImage(light_image=Image.open(logo_path),
                               dark_image=Image.open(logo_path),
                               size=(80, 80))
            ctk.CTkLabel(frame, image=img, text="").pack(pady=(20, 10))

        # Título
        ctk.CTkLabel(frame, text=f"{APP_NAME} v{APP_VERSION}", 
                     font=ctk.CTkFont(size=18, weight="bold"), text_color=C_ACCENT).pack(pady=(0, 5))

        # Informações de Compilação
        compile_date = datetime.now().strftime("%d/%m/%Y")
        ctk.CTkLabel(frame, text=f"Data de Compilação: {compile_date}", 
                     font=ctk.CTkFont(size=11), text_color=C_TEXT).pack(pady=(0, 15))

        # Autor
        ctk.CTkLabel(frame, text="Desenvolvido por:", 
                     font=ctk.CTkFont(size=12, weight="bold"), text_color="#DDDDDD").pack(pady=(0, 2))
        ctk.CTkLabel(frame, text="Brenio Filho (github.com/brenio55)", 
                     font=ctk.CTkFont(size=12), text_color="#AAAAAA").pack(pady=(0, 15))

        # Orkestrae Link
        ctk.CTkLabel(frame, text="Parte do grupo Orkestrae", 
                     font=ctk.CTkFont(size=12), text_color="#DDDDDD").pack(pady=(0, 2))
        link_lbl = ctk.CTkLabel(frame, text="Orkestrae.com.br", 
                                font=ctk.CTkFont(size=12, underline=True), text_color="#00B4D8", cursor="hand2")
        link_lbl.pack(pady=(0, 10))
        link_lbl.bind("<Button-1>", lambda e: webbrowser.open_new("https://orkestrae.com.br"))

    def _apply_settings(self, interval: float, timeout: float):
        self._interval = interval
        self._timeout  = timeout
        was_running = self._session.is_running
        hosts = list(self._session.hosts)
        self._session.stop()
        self._session = PingSession(interval=interval, timeout=timeout)
        for h in hosts:
            self._session.add_host(h)
        if was_running:
            self._session.start()

    # ═════════════════════════════════════════════════════════
    # ATUALIZAÇÕES UI PERIÓDICAS
    # ═════════════════════════════════════════════════════════
    def _schedule_ui_update(self):
        self._update_ui()
        self.after(1500, self._schedule_ui_update)

    def _update_ui(self):
        try:
            snap = self._session.get_snapshot()

            # Dot colors na sidebar
            for host, data in snap.items():
                self._host_panel.update_dot_color(
                    host, data["color"],
                    data["loss_pct"] > 0,
                    paused=data.get("paused", False),
                )

            # Statusbar
            self._sb_hosts.configure(
                text=f"Hosts: {len(self._session.hosts)}"
            )
        except Exception:
            pass

    # ═════════════════════════════════════════════════════════
    def _on_close(self):
        self._chart.stop_refresh()
        self._session.stop()
        self.destroy()
