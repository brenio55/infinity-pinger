"""
ui/chart_panel.py
Painel central com grafico matplotlib embedded no CustomTkinter.
Atualizacao em tempo real via after() do Tkinter (thread-safe).
"""

import warnings
import time
from datetime import datetime
from typing import Callable
import tkinter as tk

warnings.filterwarnings("ignore", message=".*tight_layout.*")

import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


# Paleta de fundo escura
BG_DARK  = "#0D0F1A"
BG_PANEL = "#12152A"
GRID_CLR = "#1E2240"
TEXT_CLR = "#AAAACC"


class ChartPanel(ctk.CTkFrame):

    REFRESH_MS = 800   # intervalo de redesenho (ms)

    def __init__(self, master, get_snapshot: Callable[[], dict], **kwargs):
        super().__init__(master, **kwargs)
        self.get_snapshot = get_snapshot
        self._running = False
        self._after_id = None

        self._build()

    # ── Construção do layout ──────────────────────────────
    def _build(self):
        # Figura matplotlib
        self._fig = Figure(figsize=(10, 5), facecolor=BG_DARK)

        # Sub-plots: latência (3/4) + loss (1/4)
        gs = self._fig.add_gridspec(2, 1, height_ratios=[3, 1], hspace=0.35)
        self._ax_lat  = self._fig.add_subplot(gs[0])
        self._ax_loss = self._fig.add_subplot(gs[1])

        for ax in (self._ax_lat, self._ax_loss):
            ax.set_facecolor(BG_PANEL)
            ax.tick_params(colors=TEXT_CLR, labelsize=8)
            for spine in ax.spines.values():
                spine.set_color(GRID_CLR)
            ax.grid(True, color=GRID_CLR, linewidth=0.6, linestyle="--")
            ax.yaxis.label.set_color(TEXT_CLR)
            ax.xaxis.label.set_color(TEXT_CLR)
            ax.title.set_color("#DDDDFF")

        self._ax_lat.set_title("Latencia (ms)", fontsize=11, pad=6)
        self._ax_lat.set_ylabel("ms", fontsize=9)

        self._ax_loss.set_title("Perda de Pacotes (%)", fontsize=9, pad=4)
        self._ax_loss.set_ylabel("%", fontsize=9)
        self._ax_loss.set_ylim(-2, 105)

        # Frame nativo tk para isolar o matplotlib do CTkFrame
        chart_container = tk.Frame(self, bg=BG_DARK)
        chart_container.pack(fill="both", expand=True)

        # Canvas matplotlib — nomeado _mpl_canvas para nao colidir com CTkFrame._canvas
        self._mpl_canvas = FigureCanvasTkAgg(self._fig, master=chart_container)
        self._mpl_canvas.get_tk_widget().pack(fill="both", expand=True)

        # Toolbar matplotlib (zoom, pan, save)
        toolbar_frame = tk.Frame(self, bg="#0D0F1A")
        toolbar_frame.pack(fill="x", side="bottom")
        toolbar = NavigationToolbar2Tk(self._mpl_canvas, toolbar_frame)
        toolbar.config(background="#0D0F1A")
        toolbar.update()

    # ── Controle de atualizacao ───────────────────────────
    def start_refresh(self):
        self._running = True
        self._schedule()

    def stop_refresh(self):
        self._running = False
        if self._after_id:
            try:
                self.after_cancel(self._after_id)
            except Exception:
                pass

    def _schedule(self):
        if self._running:
            self._after_id = self.after(self.REFRESH_MS, self._refresh)

    # ── Redesenho ─────────────────────────────────────────
    def _refresh(self):
        try:
            snapshot = self.get_snapshot()
            self._render(snapshot)
        except Exception:
            pass
        self._schedule()

    def _render(self, snapshot: dict):
        self._ax_lat.cla()
        self._ax_loss.cla()

        # Re-aplicar estilos apos cla()
        for ax in (self._ax_lat, self._ax_loss):
            ax.set_facecolor(BG_PANEL)
            ax.tick_params(colors=TEXT_CLR, labelsize=8)
            for spine in ax.spines.values():
                spine.set_color(GRID_CLR)
            ax.grid(True, color=GRID_CLR, linewidth=0.6, linestyle="--")

        self._ax_lat.set_title("Latencia (ms)", fontsize=11, pad=6, color="#DDDDFF")
        self._ax_lat.set_ylabel("ms", fontsize=9, color=TEXT_CLR)
        self._ax_loss.set_title("Perda de Pacotes (%)", fontsize=9, pad=4, color="#DDDDFF")
        self._ax_loss.set_ylabel("%", fontsize=9, color=TEXT_CLR)
        self._ax_loss.set_ylim(-2, 105)

        hosts = list(snapshot.keys())
        loss_vals   = []
        loss_colors = []

        for host, data in snapshot.items():
            color    = data["color"]
            ts_list  = data["timestamps"]
            lat_list = data["latencies"]

            loss_vals.append(data["loss_pct"])
            loss_colors.append(color)

            if not ts_list:
                continue

            datetimes = [datetime.fromtimestamp(t) for t in ts_list]
            lats = [l if l is not None else float("nan") for l in lat_list]

            self._ax_lat.plot(
                datetimes, lats,
                color=color, linewidth=1.5,
                label=host,
                marker="o", markersize=2.5, markevery=max(1, len(lats)//30),
            )

            # Marcar timeouts com linha vertical vermelha
            for i, lat in enumerate(lat_list):
                if lat is None and i < len(datetimes):
                    self._ax_lat.axvline(
                        datetimes[i], color="#FF3355",
                        alpha=0.25, linewidth=0.8,
                    )

        # Barras de loss
        if hosts:
            bar_positions = range(len(hosts))
            bars = self._ax_loss.bar(
                bar_positions, loss_vals,
                color=loss_colors, alpha=0.85, width=0.5,
            )
            self._ax_loss.set_xticks(list(bar_positions))
            self._ax_loss.set_xticklabels(hosts, fontsize=8, color=TEXT_CLR)
            for bar, val in zip(bars, loss_vals):
                if val > 0:
                    self._ax_loss.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 1.5,
                        f"{val:.1f}%",
                        ha="center", va="bottom",
                        fontsize=7, color="#EEEEEE",
                    )

        # Formato do eixo X de latencia
        if any(snapshot.values()):
            self._ax_lat.xaxis.set_major_formatter(
                mdates.DateFormatter("%H:%M:%S")
            )
            try:
                self._fig.autofmt_xdate(rotation=25, ha="right")
            except Exception:
                pass

        if hosts:
            self._ax_lat.legend(
                loc="upper left", fontsize=8,
                facecolor="#1A1A2E", edgecolor=GRID_CLR,
                labelcolor="#EEEEEE",
            )

        try:
            self._fig.tight_layout(pad=1.0)
        except Exception:
            pass
        self._mpl_canvas.draw_idle()

    def redraw_now(self):
        """Forca redesenho imediato."""
        snapshot = self.get_snapshot()
        self._render(snapshot)
