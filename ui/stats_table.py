"""
ui/stats_table.py
Tabela de estatísticas: min / avg / max / loss% por host.
"""

import customtkinter as ctk


_HEADERS = ["Host", "Env.", "Rec.", "Perda", "Min ms", "Avg ms", "Max ms", "Status"]
_COL_WEIGHTS = [3, 1, 1, 1, 1, 1, 1, 1]


class StatsTable(ctk.CTkFrame):

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._rows: dict[str, list[ctk.CTkLabel]] = {}
        self._build_header()

    # ── Cabeçalho ─────────────────────────────────────────
    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color="#0D3B66", corner_radius=0)
        hdr.pack(fill="x")

        for col, (text, weight) in enumerate(zip(_HEADERS, _COL_WEIGHTS)):
            hdr.columnconfigure(col, weight=weight)
            ctk.CTkLabel(
                hdr, text=text,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#AADDFF",
                anchor="center",
            ).grid(row=0, column=col, sticky="ew", padx=4, pady=6)

        self._body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._body.pack(fill="both", expand=True)

    # ── Atualização ───────────────────────────────────────
    def update_data(self, snapshot: dict):
        hosts_in_snap = set(snapshot.keys())
        hosts_in_rows = set(self._rows.keys())

        # Remove hosts que saíram
        for h in hosts_in_rows - hosts_in_snap:
            self._remove_row(h)

        # Adiciona ou atualiza
        for idx, (host, data) in enumerate(snapshot.items()):
            if host not in self._rows:
                self._add_row(host, data["color"], idx)
            self._update_row(host, data)

    def _add_row(self, host: str, color: str, idx: int):
        bg = "#1E2235" if idx % 2 == 0 else "#16213E"
        row_frame = ctk.CTkFrame(self._body, fg_color=bg, corner_radius=4)
        row_frame.pack(fill="x", pady=1)

        cells = []
        for col, weight in enumerate(_COL_WEIGHTS):
            row_frame.columnconfigure(col, weight=weight)
            lbl = ctk.CTkLabel(
                row_frame, text="—",
                font=ctk.CTkFont(size=11),
                text_color="#DDDDDD",
                anchor="center",
            )
            lbl.grid(row=0, column=col, sticky="ew", padx=4, pady=5)
            cells.append(lbl)

        # Coluna 0 → nome do host com cor
        cells[0].configure(text=host, text_color=color, anchor="w")
        cells[0].grid_configure(padx=(8, 4))

        self._rows[host] = cells

    def _update_row(self, host: str, data: dict):
        cells = self._rows[host]

        def fmt(v, decimals=1):
            return f"{v:.{decimals}f}" if v is not None else "—"

        loss = data["loss_pct"]
        status = "🟢 OK" if loss == 0 else ("🔴 PERDA" if loss > 10 else "🟡 INSTÁVEL")
        loss_color = "#44FF88" if loss == 0 else ("#FF4444" if loss > 10 else "#FFB703")

        cells[1].configure(text=str(data["sent"]))
        cells[2].configure(text=str(data["received"]))
        cells[3].configure(text=f"{loss:.1f}%", text_color=loss_color)
        cells[4].configure(text=fmt(data["min_ms"]))
        cells[5].configure(text=fmt(data["avg_ms"]))
        cells[6].configure(text=fmt(data["max_ms"]))
        cells[7].configure(text=status)

    def _remove_row(self, host: str):
        cells = self._rows.pop(host, [])
        if cells:
            # Destruir o frame pai
            cells[0].master.destroy()

    def clear(self):
        for host in list(self._rows.keys()):
            self._remove_row(host)
