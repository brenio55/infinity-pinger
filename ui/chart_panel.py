"""
ui/chart_panel.py  (v3)
Graficos por host que preenchem o espaco disponivel de forma responsiva.
- Sem scrollbar enquanto os graficos cabem na tela
- Scrollbar so aparece quando o total excede a altura disponivel
- 5px de padding no topo e entre subplots
- Figura redimensionada dinamicamente ao resize da janela
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
BG    = "#0E0F14"
PANEL = "#13151F"
GRID  = "#1C1E2C"
TEXT  = "#8888AA"

# ── Constantes de layout ──────────────────────────────────────
MIN_ROW_H  = 120    # altura mínima por host (px) antes de ativar scroll
TOP_PAD    = 5      # padding topo (px)
GAP_PX     = 5      # gap entre subplots (px)
REFRESH_MS = 900
Y_MIN_MS   = 200    # escala Y mínima (ms)


class ChartPanel(ctk.CTkFrame):
    """
    Painel de gráficos por host.
    Preenche todo o espaço disponível dividindo igualmente entre os hosts.
    Scroll só é ativado se a altura mínima × N exceder o espaço visível.
    """

    def __init__(self, master, get_snapshot: Callable[[], dict], **kwargs):
        kwargs.setdefault("corner_radius", 0)
        super().__init__(master, **kwargs)
        self.get_snapshot = get_snapshot

        self._running      = False
        self._after_id     = None
        self._last_hosts:  list[str] = []
        self._avail_w:     int = 800
        self._avail_h:     int = 500
        self._last_layout: tuple = (0, 0, 0)  # (w, h, n_hosts)

        # ── Infraestrutura scroll ─────────────────────────────
        self._scrollbar = tk.Scrollbar(self, orient="vertical")
        self._tk_canvas = tk.Canvas(
            self, bg=BG,
            highlightthickness=0, bd=0,
            yscrollcommand=self._scrollbar.set,
        )
        self._scrollbar.configure(command=self._tk_canvas.yview)

        # Começa sem scrollbar visível
        self._tk_canvas.pack(side="left", fill="both", expand=True)

        self._inner = tk.Frame(self._tk_canvas, bg=BG)
        self._inner_id = self._tk_canvas.create_window(
            (0, 0), window=self._inner, anchor="nw"
        )

        self._inner.bind("<Configure>", self._on_inner_resize)
        self._tk_canvas.bind("<Configure>", self._on_canvas_resize)
        self._tk_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Matplotlib
        self._fig        = None
        self._mpl_canvas = None
        self._axes       = {}

    # ── Resize handlers ───────────────────────────────────────
    def _on_inner_resize(self, _event):
        self._tk_canvas.configure(
            scrollregion=self._tk_canvas.bbox("all")
        )

    def _on_canvas_resize(self, event):
        new_w = max(event.width,  200)
        new_h = max(event.height, 200)

        if new_w == self._avail_w and new_h == self._avail_h:
            return

        self._avail_w = new_w
        self._avail_h = new_h

        # Força rebuild na próxima varredura (não chamar aqui para evitar loop)
        self._last_layout = (0, 0, 0)

    def _on_mousewheel(self, event):
        self._tk_canvas.yview_scroll(-1 * (event.delta // 120), "units")

    # ── Build / rebuild da figura ─────────────────────────────
    def _rebuild_figure(self, hosts: list[str]):
        n   = len(hosts)
        w   = self._avail_w
        h   = self._avail_h
        dpi = 96

        # Calcula altura por row
        total_min = n * MIN_ROW_H + max(n - 1, 0) * GAP_PX + TOP_PAD
        needs_scroll = total_min > h

        if needs_scroll:
            # Usa altura mínima e ativa scrollbar
            row_h   = MIN_ROW_H
            fig_h   = n * row_h + max(n - 1, 0) * GAP_PX + TOP_PAD
            self._show_scrollbar()
        else:
            # Preenche todo o espaço disponível
            gap_total = max(n - 1, 0) * GAP_PX + TOP_PAD
            row_h     = max((h - gap_total) // n, 40)
            fig_h     = h
            self._hide_scrollbar()

        layout_key = (w, fig_h, n)
        if layout_key == self._last_layout:
            return
        self._last_layout = layout_key

        # ── Destrói figura anterior ───────────────────────────
        if self._mpl_canvas:
            self._mpl_canvas.get_tk_widget().destroy()
            self._mpl_canvas = None
        if self._fig:
            import matplotlib.pyplot as plt
            plt.close(self._fig)
            self._fig = None

        # ── Cria nova figura ──────────────────────────────────
        w_in  = max(w   / dpi, 2)
        h_in  = max(fig_h / dpi, 1)

        self._fig = Figure(figsize=(w_in, h_in), dpi=dpi, facecolor=BG)
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

        # subplots_adjust em coordenadas de figura (0–1)
        top_frac    = 1.0 - (TOP_PAD / fig_h)
        bottom_frac = 0.02
        hspace      = GAP_PX / max(row_h, 1)

        self._fig.subplots_adjust(
            left=0.055, right=0.995,
            top=top_frac, bottom=bottom_frac,
            hspace=hspace,
        )

        # ── Embute no canvas interno ──────────────────────────
        self._tk_canvas.itemconfig(self._inner_id, width=w)
        self._mpl_canvas = FigureCanvasTkAgg(self._fig, master=self._inner)
        widget = self._mpl_canvas.get_tk_widget()
        widget.configure(width=w, height=fig_h)
        widget.pack(fill="both", expand=True)
        self._mpl_canvas.draw()

        self._tk_canvas.configure(
            scrollregion=(0, 0, w, fig_h)
        )

    # ── Scrollbar show/hide ───────────────────────────────────
    def _show_scrollbar(self):
        if not self._scrollbar.winfo_ismapped():
            self._scrollbar.pack(side="right", fill="y", before=self._tk_canvas)

    def _hide_scrollbar(self):
        if self._scrollbar.winfo_ismapped():
            self._scrollbar.pack_forget()
        # Resetar scroll para o topo
        self._tk_canvas.yview_moveto(0)

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
            snapshot  = self.get_snapshot()
            hosts     = list(snapshot.keys())

            if hosts != self._last_hosts or self._last_layout == (0, 0, 0):
                self._last_hosts = hosts
                if hosts:
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
            mx       = data["max_ms"]
            paused   = data.get("paused", False)
            cur      = lat_list[-1] if lat_list else None

            ax.cla()
            ax.set_facecolor(PANEL)
            ax.tick_params(colors=TEXT, labelsize=7, length=2, pad=2)
            for spine in ax.spines.values():
                spine.set_color(GRID)
                spine.set_linewidth(0.5)
            ax.grid(True, color=GRID, linewidth=0.5, linestyle="-")
            ax.set_ylabel("ms", fontsize=7, color=TEXT, labelpad=2)

            # Escala Y
            y_top = max(mx * 1.15, Y_MIN_MS) if mx is not None else Y_MIN_MS
            ax.set_ylim(0, y_top)

            if paused:
                ax.text(
                    0.5, 0.5, "PAUSADO",
                    transform=ax.transAxes,
                    ha="center", va="center",
                    fontsize=10, color="#334455",
                    fontweight="bold",
                )
            elif ts_list:
                datetimes = [datetime.fromtimestamp(t) for t in ts_list]
                lats = [l if l is not None else float("nan") for l in lat_list]

                ax.fill_between(datetimes, lats, alpha=0.15, color=color)
                ax.plot(datetimes, lats, color=color, linewidth=1.2,
                        solid_capstyle="round")

                for i, lat in enumerate(lat_list):
                    if lat is None and i < len(datetimes):
                        ax.axvline(datetimes[i], color="#CC2233",
                                   alpha=0.4, linewidth=0.8)

                ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
                ax.tick_params(axis="x", labelsize=6, rotation=0)

            # ── Labels overlay (dentro dos axes — sem corte) ──
            label_color = "#334455" if paused else color
            loss_color  = (
                "#33CC66" if loss == 0 else
                "#FFAA00" if loss <= 10 else
                "#FF3344"
            )
            cur_str  = f"{cur:.0f} ms"  if cur is not None and not paused else ("pausado" if paused else "—")
            avg_str  = f"avg {avg:.0f}" if avg is not None and not paused else ""

            ax.text(
                0.005, 0.97,
                f"{host}   {cur_str}   {avg_str}",
                transform=ax.transAxes,
                ha="left", va="top",
                fontsize=8, color=label_color,
                fontweight="bold", clip_on=False,
            )
            if not paused:
                ax.text(
                    0.998, 0.97,
                    f"loss {loss:.0f}%",
                    transform=ax.transAxes,
                    ha="right", va="top",
                    fontsize=7, color=loss_color,
                    clip_on=False,
                )

        self._mpl_canvas.draw_idle()
