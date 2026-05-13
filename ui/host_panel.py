"""
ui/host_panel.py  (v3)
Sidebar compacta, flat — lista de hosts com add/remove
e botao start/stop individual por host.
"""

import customtkinter as ctk
from typing import Callable

C_BG     = "#13151F"
C_ROW    = "#0E0F14"
C_BORDER = "#1C1E2C"
C_ACCENT = "#00B4D8"
C_TEXT   = "#9999BB"


class HostPanel(ctk.CTkFrame):

    def __init__(
        self,
        master,
        on_add:    Callable[[str], bool],
        on_remove: Callable[[str], None],
        on_toggle: Callable[[str], bool],   # host → True se estava pausado (agora ativo)
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.on_add    = on_add
        self.on_remove = on_remove
        self.on_toggle = on_toggle
        self._rows: dict[str, dict] = {}   # host → {"frame", "dot", "toggle_btn"}
        self._build()

    def _build(self):
        # ── Cabeçalho ─────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color=C_BG, height=32, corner_radius=0)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(
            hdr, text="HOSTS",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color="#444466",
        ).pack(side="left", padx=10, pady=8)

        # ── Input ─────────────────────────────────────────
        inp = ctk.CTkFrame(self, fg_color=C_BG, height=34, corner_radius=0)
        inp.pack(fill="x")
        inp.pack_propagate(False)

        self._entry = ctk.CTkEntry(
            inp,
            placeholder_text="host ou IP…",
            font=ctk.CTkFont(size=11),
            height=26,
            corner_radius=0,
            border_width=1,
            border_color=C_BORDER,
            fg_color=C_ROW,
        )
        self._entry.pack(side="left", fill="x", expand=True, padx=(8, 0), pady=4)
        self._entry.bind("<Return>", lambda _: self._add())

        ctk.CTkButton(
            inp, text="+", width=26, height=26,
            corner_radius=0,
            fg_color=C_ACCENT, hover_color="#008FB0",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#000000",
            command=self._add,
        ).pack(side="left", padx=(2, 8), pady=4)

        # Divisor
        ctk.CTkFrame(self, height=1, fg_color=C_BORDER,
                     corner_radius=0).pack(fill="x")

        # ── Lista scrollável ───────────────────────────────
        self._list = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=C_BORDER,
            scrollbar_button_hover_color="#2A2C3E",
        )
        self._list.pack(fill="both", expand=True)

    # ── Ações ─────────────────────────────────────────────
    def _add(self):
        host = self._entry.get().strip()
        if not host:
            return
        if self.on_add(host):
            self._entry.delete(0, "end")
            self._add_row(host)

    def _add_row(self, host: str, is_paused: bool = False):
        row = ctk.CTkFrame(
            self._list,
            fg_color=C_ROW,
            corner_radius=0,
            height=30,
        )
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)

        # Indicador de status (●)
        dot = ctk.CTkLabel(
            row, text="●", width=14,
            font=ctk.CTkFont(size=8),
            text_color="#444466",
        )
        dot.pack(side="left", padx=(6, 2))

        # Nome do host
        ctk.CTkLabel(
            row, text=host,
            font=ctk.CTkFont(size=11),
            text_color=C_TEXT, anchor="w",
        ).pack(side="left", fill="x", expand=True)

        # Botão ✕ remover
        ctk.CTkButton(
            row, text="✕", width=22, height=22,
            corner_radius=0,
            fg_color="transparent",
            hover_color="#330A0A",
            font=ctk.CTkFont(size=11),
            text_color="#554444",
            command=lambda h=host: self._remove(h),
        ).pack(side="right", padx=(2, 4))

        # Botão toggle ▶/■ (start/stop individual)
        toggle_label = "▶" if is_paused else "■"
        toggle_color = "#0D2010" if is_paused else "#1A0A0A"
        toggle_hover = "#1A4020" if is_paused else "#330A0A"
        toggle_btn = ctk.CTkButton(
            row, text=toggle_label, width=22, height=22,
            corner_radius=0,
            fg_color=toggle_color,
            hover_color=toggle_hover,
            font=ctk.CTkFont(size=10),
            text_color="#888888",
            command=lambda h=host: self._toggle(h),
        )
        toggle_btn.pack(side="right", padx=(0, 2))

        self._rows[host] = {
            "frame":      row,
            "dot":        dot,
            "toggle_btn": toggle_btn,
            "paused":     is_paused,
        }

    def _remove(self, host: str):
        self.on_remove(host)
        info = self._rows.pop(host, None)
        if info:
            info["frame"].destroy()

    def _toggle(self, host: str):
        info = self._rows.get(host)
        if not info:
            return
        # on_toggle retorna True se o host estava pausado (agora vai rodar)
        now_running = self.on_toggle(host)
        info["paused"] = not now_running

        if now_running:
            # Agora rodando → mostra ■ (parar)
            info["toggle_btn"].configure(
                text="■",
                fg_color="#1A0A0A", hover_color="#330A0A",
                text_color="#886666",
            )
        else:
            # Agora pausado → mostra ▶ (iniciar)
            info["toggle_btn"].configure(
                text="▶",
                fg_color="#0D2010", hover_color="#1A4020",
                text_color="#66AA66",
            )

    # ── Atualização externa ───────────────────────────────
    def update_dot_color(self, host: str, color: str, has_loss: bool, paused: bool = False):
        info = self._rows.get(host)
        if not info:
            return
        if paused:
            dot_color = "#333355"
        elif has_loss:
            dot_color = "#CC2233"
        else:
            dot_color = color
        info["dot"].configure(text_color=dot_color)

    def remove_all(self):
        for h in list(self._rows):
            self._remove(h)
