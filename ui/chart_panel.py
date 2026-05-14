"""
ui/chart_panel.py  (v2)
Uma figura matplotlib com um subplot por host (empilhados).
Design flat, compacto. Recriado dinamicamente quando hosts mudam.
"""

import warnings
import tkinter as tk
from datetime import datetime
from typing import Callable

import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

warnings.filterwarnings("ignore", message=".*tight_layout.*")

# ── Paleta ────────────────────────────────────────────────────
BG       = "#0E0F14"     # fundo geral
PANEL    = "#13151F"     # fundo dos axes
GRID     = "#1C1E2C"     # linhas de grade
TEXT     = "#8888AA"     # labels dos eixos
DIVIDER  = "#1C1E2C"     # linha divisória entre hosts

ROW_H_PX    = 110        # altura de cada subplot em pixels
REFRESH_MS  = 900


class ChartPanel(ctk.CTkFrame):
    """Painel scrollável com um gráfico por host."""

    def __init__(self, master, get_snapshot: Callable[[], dict], **kwargs):
        kwargs.setdefault("corner_radius", 0)
        super().__init__(master, **kwargs)
        self.get_snapshot = get_snapshot

        self._running   = False
        self._after_id  = None
        self._last_hosts: list[str] = []   # rastrea mudanças na lista de hosts

        # Container scrollável (tk nativo — melhor suporte com matplotlib)
        self._scroll_frame = tk.Frame(self, bg=BG)
        self._scroll_frame.pack(fill="both", expand=True)

        # Canvas tk + scrollbar vertical
        self._tk_canvas = tk.Canvas(
            self._scroll_frame, bg=BG,
            highlightthickness=0, bd=0,
        )
        self._scrollbar = tk.Scrollbar(
            self._scroll_frame, orient="vertical",
            command=self._tk_canvas.yview,
        )
        self._scrollbar.pack(side="right", fill="y")
        self._tk_canvas.pack(side="left", fill="both", expand=True)
        self._tk_canvas.configure(yscrollcommand=self._scrollbar.set)

        # Frame interno que contém a figura
        self._inner = tk.Frame(self._tk_canvas, bg=BG)
        self._inner_id = self._tk_canvas.create_window(
            (0, 0), window=self._inner, anchor="nw"
        )
        self._inner.bind("<Configure>", self._on_inner_resize)
        self._tk_canvas.bind("<Configure>", self._on_canvas_resize)

        # Scroll com roda do mouse
        self._tk_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Figura e canvas matplotlib
        self._fig: Figure | None = None
        self._mpl_canvas: FigureCanvasTkAgg | None = None
        self._axes = {}     # host → Axes

    # ── Scroll helpers ────────────────────────────────────────
    def _on_inner_resize(self, event):
        self._tk_canvas.configure(scrollregion=self._tk_canvas.bbox("all"))

    def _on_canvas_resize(self, event):
        self._tk_canvas.itemconfig(self._inner_id, width=event.width)
        # Recria figura com nova largura
        if self._mpl_canvas and self._last_hosts:
            self._rebuild_figure(self._last_hosts)

    def _on_mousewheel(self, event):
        self._tk_canvas.yview_scroll(-1 * (event.delta // 120), "units")

    # ── Rebuild da figura ─────────────────────────────────────
    def _rebuild_figure(self, hosts: list[str]):
        """Recria a figura matplotlib com N subplots (um por host)."""
        n = max(len(hosts), 1)

        # Largura em polegadas baseada na largura do canvas tk
        try:
            w_px = self._tk_canvas.winfo_width() or 800
        except Exception:
            w_px = 800
        dpi   = 96
        w_in  = max(w_px / dpi, 4)
        h_in  = (n * ROW_H_PX) / dpi

        # Destrói canvas anterior
        if self._mpl_canvas:
            self._mpl_canvas.get_tk_widget().destroy()
            self._mpl_canvas = None
        if self._fig:
            import matplotlib.pyplot as plt
            plt.close(self._fig)
            self._fig = None

        self._fig = Figure(
            figsize=(w_in, h_in), dpi=dpi,
            facecolor=BG,
        )
        self._axes = {}

        for i, host in enumerate(hosts):
            ax = self._fig.add_subplot(n, 1, i + 1)
            ax.set_facecolor(PANEL)
            ax.tick_params(colors=TEXT, labelsize=7, length=2, pad=2)
            for spine in ax.spines.values():
                spine.set_color(GRID)
                spine.set_linewidth(0.5)
            ax.grid(True, color=GRID, linewidth=0.5, linestyle="-")
            ax.set_ylabel("ms", fontsize=7, color=TEXT, labelpad=2)
            self._axes[host] = ax

        self._fig.subplots_adjust(
            left=0.06, right=0.99,
            top=0.97, bottom=0.05,
            hspace=0.08,
        )

        self._mpl_canvas = FigureCanvasTkAgg(self._fig, master=self._inner)
        self._mpl_canvas.get_tk_widget().pack(fill="both", expand=True)
        self._mpl_canvas.draw()

        # Atualiza scroll region
        self._tk_canvas.configure(
            scrollregion=(0, 0, w_px, n * ROW_H_PX)
        )

    # ── Controle de refresh ───────────────────────────────────
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
            self._after_id = self.after(REFRESH_MS, self._refresh)

    # ── Ciclo principal ───────────────────────────────────────
    def _refresh(self):
        try:
            snapshot = self.get_snapshot()
            hosts = list(snapshot.keys())

            # Recria figura se a lista de hosts mudou
            if hosts != self._last_hosts:
                self._last_hosts = hosts
                self._rebuild_figure(hosts)

            if hosts and self._fig:
                self._render(snapshot)
        except Exception:
            pass
        self._schedule()

    # ── Renderização ──────────────────────────────────────────
    def _render(self, snapshot: dict):
        for host, data in snapshot.items():
            ax = self._axes.get(host)
            if ax is None:
                continue

            color    = data["color"]
            ts_list  = data["timestamps"]
            lat_list = data["latencies"]
            loss     = data["loss_pct"]
            avg      = data["avg_ms"]
            cur      = lat_list[-1] if lat_list else None

            ax.cla()
            ax.set_facecolor(PANEL)
            ax.tick_params(colors=TEXT, labelsize=7, length=2, pad=2)
            for spine in ax.spines.values():
                spine.set_color(GRID)
                spine.set_linewidth(0.5)
            ax.grid(True, color=GRID, linewidth=0.5, linestyle="-")
            ax.set_ylabel("ms", fontsize=7, color=TEXT, labelpad=2)

            if ts_list:
                datetimes = [datetime.fromtimestamp(t) for t in ts_list]
                lats = [l if l is not None else float("nan") for l in lat_list]

                # Área preenchida sob a linha
                ax.fill_between(
                    datetimes, lats,
                    alpha=0.15, color=color,
                )
                ax.plot(
                    datetimes, lats,
                    color=color, linewidth=1.2,
                    solid_capstyle="round",
                )

                # Timeouts → barras verticais vermelhas
                for i, lat in enumerate(lat_list):
                    if lat is None and i < len(datetimes):
                        ax.axvline(
                            datetimes[i], color="#CC2233",
                            alpha=0.4, linewidth=0.8,
                        )

                ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
                ax.tick_params(axis="x", labelsize=6, rotation=0)

            # ── Label do host (canto superior esquerdo) ───────
            loss_color = (
                "#33CC66" if loss == 0 else
                "#FFAA00" if loss <= 10 else
                "#FF3344"
            )
            cur_str = f"{cur:.0f} ms" if cur is not None else "—"
            avg_str = f"avg {avg:.0f}" if avg is not None else ""
            label = (
                f"  {host}    "
                f"{cur_str}    "
                f"{avg_str}    "
                f"loss {loss:.0f}%"
            )
            ax.set_title(
                label,
                loc="left",
                fontsize=8,
                color=color,
                pad=3,
                fontweight="bold",
            )
            # Indicador de loss no título
            ax.set_title(
                f"loss {loss:.0f}%  ",
                loc="right",
                fontsize=7,
                color=loss_color,
                pad=3,
            )

        self._mpl_canvas.draw_idle()
