"""
ui/dialogs.py
Diálogos: configurações e exportação de relatório.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import os


class SettingsDialog(ctk.CTkToplevel):
    """Configurações: intervalo e timeout."""

    def __init__(self, master, current_interval: float, current_timeout: float,
                 on_apply):
        super().__init__(master)
        self.title("Configurações")
        self.resizable(False, False)
        self.grab_set()  # modal
        self._on_apply = on_apply

        # Centraliza
        self.geometry("340x220")
        self._build(current_interval, current_timeout)

    def _build(self, interval, timeout):
        pad = {"padx": 20, "pady": 8}

        ctk.CTkLabel(self, text="⚙  Configurações",
                     font=ctk.CTkFont(size=14, weight="bold")
                     ).pack(**pad)

        # Intervalo
        row1 = ctk.CTkFrame(self, fg_color="transparent")
        row1.pack(fill="x", **pad)
        ctk.CTkLabel(row1, text="Intervalo de ping (s):", width=180, anchor="w").pack(side="left")
        self._interval_var = ctk.StringVar(value=str(interval))
        ctk.CTkEntry(row1, textvariable=self._interval_var, width=80).pack(side="left")

        # Timeout
        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.pack(fill="x", **pad)
        ctk.CTkLabel(row2, text="Timeout (s):", width=180, anchor="w").pack(side="left")
        self._timeout_var = ctk.StringVar(value=str(timeout))
        ctk.CTkEntry(row2, textvariable=self._timeout_var, width=80).pack(side="left")

        # Nota
        ctk.CTkLabel(
            self,
            text="⚠ Alterações aplicadas na próxima sessão.",
            font=ctk.CTkFont(size=10), text_color="#888888",
        ).pack(pady=(0, 8))

        # Botões
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=8)
        ctk.CTkButton(btn_row, text="Cancelar", width=100,
                      fg_color="#2A2A3E", hover_color="#3A3A4E",
                      command=self.destroy).pack(side="left", padx=8)
        ctk.CTkButton(btn_row, text="Aplicar", width=100,
                      fg_color="#00B4D8", hover_color="#0096B7",
                      command=self._apply).pack(side="left", padx=8)

    def _apply(self):
        try:
            interval = float(self._interval_var.get())
            timeout  = float(self._timeout_var.get())
            assert 0.1 <= interval <= 60
            assert 0.5 <= timeout  <= 30
        except (ValueError, AssertionError):
            messagebox.showerror("Erro", "Valores inválidos.\nIntervalo: 0.1–60s | Timeout: 0.5–30s")
            return
        self._on_apply(interval, timeout)
        self.destroy()


class ExportDialog(ctk.CTkToplevel):
    """Diálogo de exportação de relatório."""

    def __init__(self, master, snapshot: dict,
                 export_csv_fn, export_png_fn, export_pdf_fn):
        super().__init__(master)
        self.title("Exportar Relatório")
        self.resizable(False, False)
        self.grab_set()
        self.geometry("380x280")

        self._snapshot = snapshot
        self._csv = export_csv_fn
        self._png = export_png_fn
        self._pdf = export_pdf_fn

        self._build()

    def _build(self):
        pad = {"padx": 24, "pady": 10}

        ctk.CTkLabel(self, text="📊  Exportar Relatório",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(**pad)
        ctk.CTkLabel(
            self,
            text="Escolha o formato de exportação:",
            font=ctk.CTkFont(size=11), text_color="#AAAAAA",
        ).pack(padx=24, pady=(0, 8))

        btn_cfg = {"width": 300, "height": 40, "corner_radius": 8}

        ctk.CTkButton(
            self, text="📄  Exportar CSV", **btn_cfg,
            fg_color="#1B4332", hover_color="#2D6A4F",
            command=lambda: self._export(self._csv, "CSV", "csv",
                                         [("CSV", "*.csv")]),
        ).pack(pady=4)

        ctk.CTkButton(
            self, text="🖼  Exportar Gráfico (PNG)", **btn_cfg,
            fg_color="#0D3B66", hover_color="#1A5F8A",
            command=lambda: self._export(self._png, "PNG", "png",
                                         [("PNG", "*.png")]),
        ).pack(pady=4)

        ctk.CTkButton(
            self, text="📑  Exportar Relatório PDF", **btn_cfg,
            fg_color="#3D0C11", hover_color="#6A1020",
            command=lambda: self._export(self._pdf, "PDF", "pdf",
                                         [("PDF", "*.pdf")]),
        ).pack(pady=4)

        ctk.CTkButton(
            self, text="Fechar", width=120,
            fg_color="#2A2A3E", hover_color="#3A3A4E",
            command=self.destroy,
        ).pack(pady=12)

    def _export(self, fn, label: str, ext: str, filetypes):
        filepath = filedialog.asksaveasfilename(
            defaultextension=f".{ext}",
            filetypes=filetypes,
            title=f"Salvar {label}",
        )
        if not filepath:
            return
        self.destroy()

        def run():
            try:
                result = fn(self._snapshot, filepath)
                messagebox.showinfo(
                    "Exportado com sucesso!",
                    f"Arquivo salvo em:\n{result}"
                )
            except Exception as e:
                messagebox.showerror("Erro ao exportar", str(e))

        threading.Thread(target=run, daemon=True).start()
