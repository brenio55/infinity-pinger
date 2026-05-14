"""
ui/host_panel.py  (v2)
Sidebar compacta, flat — lista de hosts com add/remove.
"""

import customtkinter as ctk
from typing import Callable

C_BG     = "#13151F"
C_ROW    = "#0E0F14"
C_HOVER  = "#1A1C28"
C_BORDER = "#1C1E2C"
C_ACCENT = "#00B4D8"
C_TEXT   = "#9999BB"


class HostPanel(ctk.CTkFrame):

    def __init__(
        self,
        master,
        on_add: Callable[[str], bool],
        on_remove: Callable[[str], None],
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.on_add    = on_add
        self.on_remove = on_remove
        self._rows: dict[str, ctk.CTkFrame] = {}
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

    def _add(self):
        host = self._entry.get().strip()
        if not host:
            return
        if self.on_add(host):
            self._entry.delete(0, "end")
            self._add_row(host)

    def _add_row(self, host: str):
        row = ctk.CTkFrame(
            self._list,
            fg_color=C_ROW,
            corner_radius=0,
            height=30,
        )
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)

        # Indicador de status
        self._dot = ctk.CTkLabel(
            row, text="●", width=16,
            font=ctk.CTkFont(size=8),
            text_color="#444466",
        )
        self._dot.pack(side="left", padx=(6, 2))

        ctk.CTkLabel(
            row, text=host,
            font=ctk.CTkFont(size=11),
            text_color=C_TEXT, anchor="w",
        ).pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            row, text="×", width=22, height=22,
            corner_radius=0,
            fg_color="transparent",
            hover_color="#330A0A",
            font=ctk.CTkFont(size=12),
            text_color="#554444",
            command=lambda h=host: self._remove(h),
        ).pack(side="right", padx=4)

        self._rows[host] = row

    def _remove(self, host: str):
        self.on_remove(host)
        row = self._rows.pop(host, None)
        if row:
            row.destroy()

    def update_dot_color(self, host: str, color: str, has_loss: bool):
        row = self._rows.get(host)
        if not row:
            return
        dot_color = "#CC2233" if has_loss else color
        for child in row.winfo_children():
            if isinstance(child, ctk.CTkLabel) and child.cget("text") == "●":
                child.configure(text_color=dot_color)
                break

    def remove_all(self):
        for h in list(self._rows):
            self._remove(h)
