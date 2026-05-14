"""
ui/chart_panel.py  (v4)
- Stairs (step) plot por host
- LOZ: fundo vermelho durante perda de pacotes
- Timeline compartilhado na base (5min / 10min)
- Janela de tempo selecionavel
- 5px padding top/bottom, 5px gap entre subplots
- Responsivo: sem scroll quando cabe, scroll quando necessario
"""

import warnings
import time as _time
import tkinter as tk
from datetime import datetime
from typing import Callable

import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

warnings.filterwarnings("ignore", message=".*tight_layout.*")

# Paleta
BG       = "#0E0F14"
PANEL    = "#13151F"
GRID     = "#1C1E2C"
TEXT     = "#8888AA"
LOSS_CLR = "#CC1122"

# Layout
MIN_ROW_H  = 100   # px minimo por subplot host
TIMELINE_H = 32    # px para o eixo de tempo
TOP_PAD    = 5
BOT_PAD    = 5
GAP_PX     = 5
REFRESH_MS = 900
Y_MIN_MS   = 200

WINDOW_OPTIONS = {
    "30s":  30,
    "1m":   60,
    "5m":   300,
    "15m":  900,
    "30m":  1800,
    "1h":   3600,
}
DEFAULT_WINDOW = "5m"


class ChartPanel(ctk.CTkFrame):

    def __init__(self, master, get_snapshot: Callable[[], dict], **kwargs):
        kwargs.setdefault("corner_radius", 0)
        super().__init__(master, **kwargs)
        self.get_snapshot = get_snapshot

        self._running          = False
        self._after_id         = None
        self._last_hosts: list[str] = []
        self._avail_w: int     = 800
        self._avail_h: int     = 500
        self._last_layout: tuple = (0, 0, 0)
        self._view_sec: int    = WINDOW_OPTIONS[DEFAULT_WINDOW]
        self._ax_timeline      = None

        # Scroll infra
        self._scrollbar = tk.Scrollbar(self, orient="vertical")
        self._tk_canvas = tk.Canvas(
            self, bg=BG, highlightthickness=0, bd=0,
            yscrollcommand=self._scrollbar.set,
        )
        self._scrollbar.configure(command=self._tk_canvas.yview)
        self._tk_canvas.pack(side="left", fill="both", expand=True)

        self._inner    = tk.Frame(self._tk_canvas, bg=BG)
        self._inner_id = self._tk_canvas.create_window(
            (0, 0), window=self._inner, anchor="nw"
        )
        self._inner.bind("<Configure>", self._on_inner_resize)
        self._tk_canvas.bind("<Configure>", self._on_canvas_resize)
        self._tk_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self._fig: Figure | None             = None
        self._mpl_canvas: FigureCanvasTkAgg | None = None
        self._axes: dict                     = {}

    # ── API externa ────────────────────────────────────────
    def set_window(self, key: str):
        self._view_sec    = WINDOW_OPTIONS.get(key, 300)
        self._last_layout = (0, 0, 0)

    # ── Resize ─────────────────────────────────────────────
    def _on_inner_resize(self, _e):
        self._tk_canvas.configure(
            scrollregion=self._tk_canvas.bbox("all")
        )

    def _on_canvas_resize(self, event):
        w, h = max(event.width, 200), max(event.height, 200)
        if w != self._avail_w or h != self._avail_h:
            self._avail_w = w
            self._avail_h = h
            self._last_layout = (0, 0, 0)

    def _on_mousewheel(self, event):
        self._tk_canvas.yview_scroll(-1 * (event.delta // 120), "units")

    # ── Rebuild figura ─────────────────────────────────────
    def _rebuild_figure(self, hosts: list[str]):
        n   = len(hosts)
        w   = self._avail_w
        h   = self._avail_h
        dpi = 96

        # Espaco para linhas de host (excluindo timeline, pads, gaps)
        # n gaps: (n-1) entre hosts + 1 entre ultimo host e timeline
        gaps_total     = n * GAP_PX
        overhead       = TOP_PAD + BOT_PAD + TIMELINE_H + gaps_total
        ideal_row_h    = max((h - overhead) // n, 20)
        min_total      = n * MIN_ROW_H + overhead
        needs_scroll   = min_total > h

        if needs_scroll:
            row_h = MIN_ROW_H
            fig_h = min_total
            self._show_scrollbar()
        else:
            row_h = ideal_row_h
            fig_h = h
            self._hide_scrollbar()

        layout_key = (w, fig_h, n)
        if layout_key == self._last_layout:
            return
        self._last_layout = layout_key

        # Destroi anterior
        if self._mpl_canvas:
            self._mpl_canvas.get_tk_widget().destroy()
            self._mpl_canvas = None
        if self._fig:
            import matplotlib.pyplot as plt
            plt.close(self._fig)
            self._fig = None

        w_in = max(w   / dpi, 2)
        h_in = max(fig_h / dpi, 1)

        self._fig = Figure(figsize=(w_in, h_in), dpi=dpi, facecolor=BG)
        self._axes       = {}
        self._ax_timeline = None

        # GridSpec: n linhas de host + 1 timeline
        hr = [row_h] * n + [TIMELINE_H]
        gs = GridSpec(
            n + 1, 1,
            figure=self._fig,
            height_ratios=hr,
            left=0.055, right=0.995,
            top=1.0 - TOP_PAD / fig_h,
            bottom=BOT_PAD / fig_h,
            hspace=GAP_PX / max(row_h, 1),
        )

        for i, host in enumerate(hosts):
            ax = self._fig.add_subplot(gs[i])
            ax.set_facecolor(PANEL)
            ax.tick_params(colors=TEXT, labelsize=7, length=2, pad=2)
            ax.tick_params(axis="x", labelbottom=False)
            for sp in ax.spines.values():
                sp.set_color(GRID)
                sp.set_linewidth(0.5)
            ax.grid(True, color=GRID, linewidth=0.5, linestyle="-")
            ax.set_ylabel("ms", fontsize=7, color=TEXT, labelpad=2)
            self._axes[host] = ax

        # Timeline
        ax_tl = self._fig.add_subplot(gs[n])
        ax_tl.set_facecolor(PANEL)
        for sp in ax_tl.spines.values():
            sp.set_visible(False)
        ax_tl.spines["bottom"].set_visible(True)
        ax_tl.spines["bottom"].set_color(GRID)
        ax_tl.yaxis.set_visible(False)
        ax_tl.tick_params(axis="x", colors=TEXT, length=3, pad=2)
        self._ax_timeline = ax_tl

        self._mpl_canvas = FigureCanvasTkAgg(self._fig, master=self._inner)
        widget = self._mpl_canvas.get_tk_widget()
        widget.configure(width=w, height=fig_h)
        widget.pack(fill="both", expand=True)
        self._mpl_canvas.draw()

        self._tk_canvas.itemconfig(self._inner_id, width=w)
        self._tk_canvas.configure(scrollregion=(0, 0, w, fig_h))

    # ── Scrollbar show/hide ────────────────────────────────
    def _show_scrollbar(self):
        if not self._scrollbar.winfo_ismapped():
            self._scrollbar.pack(side="right", fill="y",
                                 before=self._tk_canvas)

    def _hide_scrollbar(self):
        if self._scrollbar.winfo_ismapped():
            self._scrollbar.pack_forget()
        self._tk_canvas.yview_moveto(0)

    # ── Refresh loop ───────────────────────────────────────
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

    def _refresh(self):
        try:
            snapshot = self.get_snapshot()
            hosts    = list(snapshot.keys())

            if hosts != self._last_hosts or self._last_layout == (0, 0, 0):
                self._last_hosts = hosts
                if hosts:
                    self._rebuild_figure(hosts)

            if hosts and self._fig:
                self._render(snapshot)
        except Exception:
            pass
        self._schedule()

    # ── Render ─────────────────────────────────────────────
    def _render(self, snapshot: dict):
        now      = _time.time()
        t_min_ts = now - self._view_sec
        t_max_ts = now
        dt_min   = datetime.fromtimestamp(t_min_ts)
        dt_max   = datetime.fromtimestamp(t_max_ts)

        for host, data in snapshot.items():
            ax = self._axes.get(host)
            if ax is None:
                continue

            color  = data["color"]
            paused = data.get("paused", False)
            loss   = data["loss_pct"]
            avg    = data["avg_ms"]
            mx     = data["max_ms"]

            # Filtra pela janela de tempo
            pairs  = [(t, l) for t, l in zip(data["timestamps"],
                                               data["latencies"])
                      if t >= t_min_ts]
            f_ts   = [p[0] for p in pairs]
            f_lat  = [p[1] for p in pairs]
            cur    = f_lat[-1] if f_lat else None

            ax.cla()
            ax.set_facecolor(PANEL)
            ax.tick_params(colors=TEXT, labelsize=7, length=2, pad=2)
            ax.tick_params(axis="x", labelbottom=False)
            for sp in ax.spines.values():
                sp.set_color(GRID)
                sp.set_linewidth(0.5)
            ax.grid(True, color=GRID, linewidth=0.5, linestyle="-")
            ax.set_ylabel("ms", fontsize=7, color=TEXT, labelpad=2)
            ax.set_xlim(dt_min, dt_max)

            y_top = max(mx * 1.15, Y_MIN_MS) if mx is not None else Y_MIN_MS
            ax.set_ylim(0, y_top)

            if paused:
                ax.text(0.5, 0.5, "PAUSADO", transform=ax.transAxes,
                        ha="center", va="center", fontsize=10,
                        color="#334455", fontweight="bold")
            elif f_ts:
                dts  = [datetime.fromtimestamp(t) for t in f_ts]
                lats = [l if l is not None else float("nan") for l in f_lat]

                # ── LOZ: spans vermelhos onde lat=None ────────
                in_loss    = False
                loss_start = None
                for i, (dt_pt, lat) in enumerate(zip(dts, f_lat)):
                    if lat is None and not in_loss:
                        in_loss    = True
                        loss_start = dt_pt
                    elif lat is not None and in_loss:
                        ax.axvspan(loss_start, dt_pt,
                                   color=LOSS_CLR, alpha=0.28, zorder=0)
                        in_loss = False
                if in_loss and loss_start is not None:
                    # Loss ainda ativo no fim da janela — pinta até agora
                    ax.axvspan(loss_start, dt_max,
                               color=LOSS_CLR, alpha=0.40, zorder=0)

                # ── Stairs ────────────────────────────────────
                ax.fill_between(dts, lats, step="post",
                                alpha=0.13, color=color, zorder=1)
                ax.step(dts, lats, where="post",
                        color=color, linewidth=1.3, zorder=2)

            # Labels overlay (dentro dos axes)
            lbl_color  = "#334455" if paused else color
            loss_color = ("#33CC66" if loss == 0 else
                          "#FFAA00" if loss <= 10 else "#FF3344")
            cur_str    = f"{cur:.0f} ms" if cur is not None and not paused else (
                         "pausado" if paused else "—")
            avg_str    = f"avg {avg:.0f}" if avg is not None and not paused else ""

            ax.text(0.005, 0.97, f"{host}   {cur_str}   {avg_str}",
                    transform=ax.transAxes, ha="left", va="top",
                    fontsize=8, color=lbl_color, fontweight="bold",
                    clip_on=False)
            if not paused:
                ax.text(0.998, 0.97, f"loss {loss:.0f}%",
                        transform=ax.transAxes, ha="right", va="top",
                        fontsize=7, color=loss_color, clip_on=False)

        # ── Timeline ──────────────────────────────────────────
        if self._ax_timeline is not None:
            ax_tl = self._ax_timeline
            ax_tl.cla()
            ax_tl.set_facecolor(PANEL)
            for sp in ax_tl.spines.values():
                sp.set_visible(False)
            ax_tl.spines["bottom"].set_visible(True)
            ax_tl.spines["bottom"].set_color(GRID)
            ax_tl.yaxis.set_visible(False)
            ax_tl.set_xlim(dt_min, dt_max)
            ax_tl.set_ylim(0, 1)

            # Major: multiplos de 10 min (fonte maior)
            ax_tl.xaxis.set_major_locator(
                mdates.MinuteLocator(byminute=range(0, 60, 10))
            )
            ax_tl.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
            ax_tl.tick_params(axis="x", which="major",
                              colors=TEXT, labelsize=8, length=5, pad=3)

            # Minor: 5 em 5 min (fonte menor, sem label)
            ax_tl.xaxis.set_minor_locator(
                mdates.MinuteLocator(byminute=range(0, 60, 5))
            )
            ax_tl.tick_params(axis="x", which="minor",
                              colors=GRID, labelsize=0, length=3)

            # Para janelas < 10 min, ajusta para segundos/minutos
            if self._view_sec <= 120:
                ax_tl.xaxis.set_major_locator(
                    mdates.SecondLocator(bysecond=range(0, 60, 30))
                )
                ax_tl.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
                ax_tl.xaxis.set_minor_locator(
                    mdates.SecondLocator(bysecond=range(0, 60, 10))
                )
            elif self._view_sec <= 600:
                ax_tl.xaxis.set_major_locator(
                    mdates.MinuteLocator(byminute=range(0, 60, 2))
                )
                ax_tl.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
                ax_tl.xaxis.set_minor_locator(
                    mdates.MinuteLocator(byminute=range(0, 60, 1))
                )
                ax_tl.tick_params(axis="x", which="major",
                                  colors=TEXT, labelsize=8, length=5)

        self._mpl_canvas.draw_idle()
