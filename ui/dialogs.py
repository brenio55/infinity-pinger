"""
ui/dialogs.py  (v2)
Dialogos planos e compactos.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading

C_BG    = "#0E0F14"
C_PANEL = "#13151F"
C_BORD  = "#1C1E2C"
C_ACCT  = "#00B4D8"


def _lbl(master, text, size=11, color="#8888AA", **kw):
    return ctk.CTkLabel(master, text=text, font=ctk.CTkFont(size=size),
                        text_color=color, **kw)


def _btn(master, text, cmd, width=120, color="#1A1C28", hover="#22253A"):
    return ctk.CTkButton(
        master, text=text, command=cmd,
        width=width, height=28, corner_radius=0,
        fg_color=color, hover_color=hover,
        font=ctk.CTkFont(size=11),
    )


class SettingsDialog(ctk.CTkToplevel):

    def __init__(self, master, current_interval, current_timeout, on_apply):
        super().__init__(master)
        self.title("Configuracoes")
        self.geometry("320x180")
        self.resizable(False, False)
        self.grab_set()
        self.configure(fg_color=C_BG)
        self._on_apply = on_apply
        self._build(current_interval, current_timeout)

    def _build(self, interval, timeout):
        # Titulo
        ctk.CTkFrame(self, height=36, fg_color=C_PANEL, corner_radius=0
                     ).pack(fill="x")
        _lbl(self, "  Configuracoes", size=12, color=C_ACCT
             ).place(x=0, y=8)

        body = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        body.pack(fill="both", expand=True, padx=16, pady=12)

        for row_i, (label, default) in enumerate([
            ("Intervalo (s):", interval),
            ("Timeout  (s):", timeout),
        ]):
            body.rowconfigure(row_i, weight=1)
            _lbl(body, label, size=11, anchor="w").grid(
                row=row_i, column=0, sticky="w", pady=4
            )
            var = ctk.StringVar(value=str(default))
            e = ctk.CTkEntry(
                body, textvariable=var,
                width=80, height=26, corner_radius=0,
                border_color=C_BORD, fg_color=C_PANEL,
                font=ctk.CTkFont(size=11),
            )
            e.grid(row=row_i, column=1, sticky="w", padx=(8, 0), pady=4)
            if row_i == 0:
                self._iv = var
            else:
                self._tv = var

        # Botoes
        brow = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        brow.pack(fill="x", padx=16, pady=(0, 12))
        _btn(brow, "Cancelar", self.destroy, width=100).pack(side="left")
        _btn(brow, "Aplicar", self._apply, width=100,
             color="#0A3040", hover="#0D4A60").pack(side="right")

    def _apply(self):
        try:
            iv = float(self._iv.get())
            tv = float(self._tv.get())
            assert 0.1 <= iv <= 60 and 0.5 <= tv <= 30
        except Exception:
            messagebox.showerror("Erro", "Valores invalidos.")
            return
        self._on_apply(iv, tv)
        self.destroy()


class ExportDialog(ctk.CTkToplevel):

    def __init__(self, master, snapshot, export_csv_fn, export_png_fn, export_pdf_fn):
        super().__init__(master)
        self.title("Exportar")
        self.geometry("300x210")
        self.resizable(False, False)
        self.grab_set()
        self.configure(fg_color=C_BG)

        self._snap = snapshot
        self._fns  = {
            "CSV": (export_csv_fn, "csv", [("CSV", "*.csv")]),
            "PNG": (export_png_fn, "png", [("PNG", "*.png")]),
            "PDF": (export_pdf_fn, "pdf", [("PDF", "*.pdf")]),
        }
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, height=36, fg_color=C_PANEL, corner_radius=0)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        _lbl(hdr, "  Exportar Relatorio", size=12, color=C_ACCT
             ).pack(side="left", padx=8, pady=8)

        body = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        body.pack(fill="both", expand=True, padx=16, pady=12)

        labels = {
            "CSV": ("  Dados CSV", "#0D3320", "#1A5532"),
            "PNG": ("  Grafico PNG", "#0D2040", "#1A3A60"),
            "PDF": ("  Relatorio PDF", "#300A0A", "#4A1515"),
        }
        for fmt, (txt, c, h) in labels.items():
            _btn(body, txt, lambda f=fmt: self._export(f),
                 width=260, color=c, hover=h
                 ).pack(fill="x", pady=3)

        _btn(body, "Fechar", self.destroy, width=260
             ).pack(fill="x", pady=(8, 0))

    def _export(self, fmt: str):
        fn, ext, filetypes = self._fns[fmt]
        path = filedialog.asksaveasfilename(
            defaultextension=f".{ext}", filetypes=filetypes
        )
        if not path:
            return
        self.destroy()

        def run():
            try:
                out = fn(self._snap, path)
                messagebox.showinfo("Exportado", f"Salvo em:\n{out}")
            except Exception as e:
                messagebox.showerror("Erro", str(e))

        threading.Thread(target=run, daemon=True).start()
