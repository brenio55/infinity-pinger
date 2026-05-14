"""
ui/host_panel.py
Painel lateral: lista de hosts, adicionar, remover.
"""

import customtkinter as ctk
from typing import Callable


class HostPanel(ctk.CTkFrame):
    """
    Sidebar esquerda:
    - Campo de texto para digitar um host
    - Botão Adicionar
    - Lista de hosts com botão de remoção por item
    """

    def __init__(
        self,
        master,
        on_add: Callable[[str], bool],
        on_remove: Callable[[str], None],
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.on_add = on_add
        self.on_remove = on_remove
        self._host_rows: dict[str, ctk.CTkFrame] = {}

        self._build()

    def _build(self):
        # ── Título ───────────────────────────────────────
        ctk.CTkLabel(
            self, text="🖥  Hosts", font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        ).pack(fill="x", padx=12, pady=(12, 4))

        ctk.CTkFrame(self, height=1, fg_color="#2A2A3E").pack(fill="x", padx=8, pady=4)

        # ── Input + botão add ─────────────────────────────
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.pack(fill="x", padx=8, pady=4)

        self._entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="host / IP",
            font=ctk.CTkFont(size=12),
        )
        self._entry.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self._entry.bind("<Return>", lambda _: self._add_host())

        ctk.CTkButton(
            input_frame, text="+", width=32,
            command=self._add_host,
            fg_color="#00B4D8", hover_color="#0096B7",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left")

        ctk.CTkFrame(self, height=1, fg_color="#2A2A3E").pack(fill="x", padx=8, pady=6)

        # ── Área de scroll com a lista ────────────────────
        self._list_frame = ctk.CTkScrollableFrame(
            self, label_text="", fg_color="transparent"
        )
        self._list_frame.pack(fill="both", expand=True, padx=4, pady=(0, 8))

    def _add_host(self):
        host = self._entry.get().strip()
        if not host:
            return
        success = self.on_add(host)
        if success:
            self._entry.delete(0, "end")
            self._add_row(host)

    def _add_row(self, host: str):
        row = ctk.CTkFrame(
            self._list_frame,
            fg_color="#1E2235",
            corner_radius=8,
        )
        row.pack(fill="x", pady=3, padx=2)

        # Indicador colorido (será atualizado externamente)
        dot = ctk.CTkLabel(row, text="●", width=20, font=ctk.CTkFont(size=10))
        dot.pack(side="left", padx=(6, 2))

        label = ctk.CTkLabel(
            row, text=host,
            font=ctk.CTkFont(size=11),
            anchor="w",
        )
        label.pack(side="left", fill="x", expand=True, padx=4)

        remove_btn = ctk.CTkButton(
            row, text="✕", width=26, height=22,
            fg_color="#2A2A3E", hover_color="#CC3333",
            font=ctk.CTkFont(size=10),
            command=lambda h=host: self._remove_host(h),
        )
        remove_btn.pack(side="right", padx=6, pady=4)

        self._host_rows[host] = row

    def _remove_host(self, host: str):
        self.on_remove(host)
        row = self._host_rows.pop(host, None)
        if row:
            row.destroy()

    def update_dot_color(self, host: str, color: str, has_loss: bool):
        """Atualiza a cor do indicador de status do host."""
        row = self._host_rows.get(host)
        if not row:
            return
        for child in row.winfo_children():
            if isinstance(child, ctk.CTkLabel) and child.cget("text") == "●":
                dot_color = "#FF4444" if has_loss else color
                child.configure(text_color=dot_color)
                break

    def remove_all(self):
        for host in list(self._host_rows.keys()):
            self._remove_host(host)
