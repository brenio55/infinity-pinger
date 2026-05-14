"""
ui/app.py
Janela principal do InfinityPinger.
"""

import threading
import customtkinter as ctk
from tkinter import messagebox

from core.session import PingSession
from core.reporter import export_csv, export_png, export_pdf

from ui.host_panel  import HostPanel
from ui.chart_panel import ChartPanel
from ui.stats_table import StatsTable
from ui.dialogs     import SettingsDialog, ExportDialog


# ── Configuração global do CTk ─────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

APP_NAME    = "InfinityPinger"
APP_VERSION = "0.1.0"


class App(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title(f"{APP_NAME}  v{APP_VERSION}")
        self.geometry("1280x760")
        self.minsize(900, 560)
        self.configure(fg_color="#0A0C17")

        # Tenta definir ícone (ignora se não existir)
        try:
            self.iconbitmap("assets/icon.ico")
        except Exception:
            pass

        # ── Sessão ────────────────────────────────────────
        self._interval = 1.0
        self._timeout  = 2.0
        self._session  = PingSession(
            interval=self._interval,
            timeout=self._timeout,
        )

        # ── Build UI ──────────────────────────────────────
        self._build_toolbar()
        self._build_main_area()
        self._build_statusbar()

        # Inicia o refresh do gráfico
        self._chart.start_refresh()

        # Inicia atualização periódica da tabela e status
        self._schedule_stats_update()

        # Protocolo de fechamento
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ═══════════════════════════════════════════════════
    # TOOLBAR
    # ═══════════════════════════════════════════════════
    def _build_toolbar(self):
        tb = ctk.CTkFrame(self, fg_color="#0D0F1A", height=52, corner_radius=0)
        tb.pack(fill="x", side="top")
        tb.pack_propagate(False)

        # Logo / título
        ctk.CTkLabel(
            tb,
            text=f"◈  {APP_NAME}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#00B4D8",
        ).pack(side="left", padx=16)

        ctk.CTkFrame(tb, width=1, fg_color="#2A2A3E").pack(side="left", fill="y", pady=8, padx=4)

        # Botões de ação
        btn_defaults = dict(height=36, corner_radius=8, font=ctk.CTkFont(size=12))

        self._btn_start = ctk.CTkButton(
            tb, text="▶  Iniciar", width=110,
            fg_color="#006400", hover_color="#228B22",
            command=self._start_session, **btn_defaults,
        )
        self._btn_start.pack(side="left", padx=(12, 4), pady=8)

        self._btn_stop = ctk.CTkButton(
            tb, text="■  Parar", width=110,
            fg_color="#660000", hover_color="#8B0000",
            state="disabled",
            command=self._stop_session, **btn_defaults,
        )
        self._btn_stop.pack(side="left", padx=4, pady=8)

        ctk.CTkButton(
            tb, text="🗑  Limpar", width=110,
            fg_color="#2A2A3E", hover_color="#3A3A50",
            command=self._clear_history, **btn_defaults,
        ).pack(side="left", padx=4, pady=8)

        ctk.CTkFrame(tb, width=1, fg_color="#2A2A3E").pack(side="left", fill="y", pady=8, padx=4)

        ctk.CTkButton(
            tb, text="💾  Salvar Relatório", width=150,
            fg_color="#1B2A4A", hover_color="#243A60",
            command=self._open_export_dialog, **btn_defaults,
        ).pack(side="left", padx=4, pady=8)

        ctk.CTkButton(
            tb, text="⚙  Config.", width=100,
            fg_color="#2A2A3E", hover_color="#3A3A50",
            command=self._open_settings, **btn_defaults,
        ).pack(side="right", padx=12, pady=8)

    # ═══════════════════════════════════════════════════
    # ÁREA PRINCIPAL
    # ═══════════════════════════════════════════════════
    def _build_main_area(self):
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=0, pady=0)

        # ── Sidebar de hosts ──────────────────────────────
        self._host_panel = HostPanel(
            main,
            on_add=self._session.add_host,
            on_remove=self._session.remove_host,
            fg_color="#0D0F1A",
            width=220,
            corner_radius=0,
        )
        self._host_panel.pack(side="left", fill="y")

        ctk.CTkFrame(main, width=1, fg_color="#2A2A3E").pack(side="left", fill="y")

        # ── Área direita: gráfico + tabela ────────────────
        right = ctk.CTkFrame(main, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True)

        self._chart = ChartPanel(
            right,
            get_snapshot=self._session.get_snapshot,
            fg_color="#0A0C17",
        )
        self._chart.pack(fill="both", expand=True)

        ctk.CTkFrame(right, height=1, fg_color="#2A2A3E").pack(fill="x", pady=2)

        # ── Painel inferior: tabela de stats ─────────────
        stats_container = ctk.CTkFrame(right, fg_color="#0D0F1A", height=180)
        stats_container.pack(fill="x", side="bottom")
        stats_container.pack_propagate(False)

        ctk.CTkLabel(
            stats_container,
            text="Estatísticas",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#888899", anchor="w",
        ).pack(fill="x", padx=12, pady=(6, 0))

        self._stats = StatsTable(stats_container, fg_color="transparent")
        self._stats.pack(fill="both", expand=True, padx=4, pady=4)

    # ═══════════════════════════════════════════════════
    # STATUSBAR
    # ═══════════════════════════════════════════════════
    def _build_statusbar(self):
        sb = ctk.CTkFrame(self, fg_color="#080A14", height=26, corner_radius=0)
        sb.pack(fill="x", side="bottom")
        sb.pack_propagate(False)

        self._status_lbl = ctk.CTkLabel(
            sb, text="  ◉  Parado",
            font=ctk.CTkFont(size=10),
            text_color="#666688", anchor="w",
        )
        self._status_lbl.pack(side="left", padx=12)

        self._hosts_lbl = ctk.CTkLabel(
            sb, text="Hosts: 0",
            font=ctk.CTkFont(size=10),
            text_color="#666688",
        )
        self._hosts_lbl.pack(side="right", padx=12)

    # ═══════════════════════════════════════════════════
    # AÇÕES
    # ═══════════════════════════════════════════════════
    def _start_session(self):
        hosts = self._session.hosts
        if not hosts:
            messagebox.showwarning("Sem hosts", "Adicione ao menos um host antes de iniciar.")
            return
        self._session.start()
        self._chart.start_refresh()
        self._btn_start.configure(state="disabled")
        self._btn_stop.configure(state="normal")
        self._status_lbl.configure(text="  ◉  Rodando", text_color="#00B4D8")

    def _stop_session(self):
        self._session.stop()
        self._btn_start.configure(state="normal")
        self._btn_stop.configure(state="disabled")
        self._status_lbl.configure(text="  ◉  Parado", text_color="#FF4466")

    def _clear_history(self):
        self._session.clear_history()
        self._stats.clear()

    def _open_export_dialog(self):
        snap = self._session.get_snapshot()
        if not snap:
            messagebox.showwarning("Sem dados", "Nenhum dado disponível para exportar.")
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

    def _apply_settings(self, interval: float, timeout: float):
        self._interval = interval
        self._timeout  = timeout
        # Recria a sessão com os novos parâmetros
        was_running = self._session.is_running
        hosts = list(self._session.hosts)
        self._session.stop()
        self._session = PingSession(interval=interval, timeout=timeout)
        for h in hosts:
            self._session.add_host(h)
        if was_running:
            self._session.start()

    # ═══════════════════════════════════════════════════
    # ATUALIZAÇÕES PERIÓDICAS
    # ═══════════════════════════════════════════════════
    def _schedule_stats_update(self):
        self._update_stats()
        self.after(1500, self._schedule_stats_update)

    def _update_stats(self):
        try:
            snap = self._session.get_snapshot()
            self._stats.update_data(snap)

            # Atualiza dots no painel de hosts
            for host, data in snap.items():
                self._host_panel.update_dot_color(
                    host, data["color"], data["loss_pct"] > 0
                )

            # Statusbar
            n = len(self._session.hosts)
            self._hosts_lbl.configure(text=f"Hosts: {n}")
        except Exception:
            pass

    # ═══════════════════════════════════════════════════
    # FECHAMENTO
    # ═══════════════════════════════════════════════════
    def _on_close(self):
        self._chart.stop_refresh()
        self._session.stop()
        self.destroy()
