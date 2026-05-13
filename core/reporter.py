"""
core/reporter.py
Exportação de relatórios: CSV, PNG e PDF.
"""

import csv
import io
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use("Agg")   # backend sem GUI para geração offline
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
)
from reportlab.lib.enums import TA_CENTER


# ── Diretório padrão de relatórios ────────────────────────
REPORTS_DIR = Path(__file__).parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


def _ts_label() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


# ─────────────────────────────────────────────────────────
# CSV
# ─────────────────────────────────────────────────────────
def export_csv(snapshot: dict, filepath: Optional[str] = None) -> str:
    if not filepath:
        filepath = str(REPORTS_DIR / f"ping_report_{_ts_label()}.csv")

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["host", "timestamp", "datetime", "latency_ms", "success"])

        for host, data in snapshot.items():
            ts_list  = data["timestamps"]
            lat_list = data["latencies"]
            for ts, lat in zip(ts_list, lat_list):
                dt_str  = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
                success = lat is not None
                lat_val = f"{lat:.1f}" if lat is not None else ""
                writer.writerow([host, f"{ts:.3f}", dt_str, lat_val, success])

    return filepath


# ─────────────────────────────────────────────────────────
# PNG — gráfico de latência
# ─────────────────────────────────────────────────────────
def _build_figure(snapshot: dict, figsize=(14, 6)) -> Figure:
    """Cria figure matplotlib com os dados do snapshot."""
    import matplotlib.dates as mdates
    from datetime import datetime as dt

    fig, (ax_lat, ax_loss) = plt.subplots(
        2, 1, figsize=figsize,
        gridspec_kw={"height_ratios": [3, 1]},
        facecolor="#1A1A2E",
    )

    for ax in (ax_lat, ax_loss):
        ax.set_facecolor("#16213E")
        ax.tick_params(colors="#AAAAAA")
        ax.spines[:].set_color("#333355")
        ax.yaxis.label.set_color("#CCCCCC")
        ax.xaxis.label.set_color("#CCCCCC")
        ax.title.set_color("#EEEEEE")

    ax_lat.set_title("Latência por Host", fontsize=12, pad=8)
    ax_lat.set_ylabel("ms")
    ax_lat.grid(True, color="#222244", linewidth=0.5)

    ax_loss.set_title("Perda de Pacotes (%)", fontsize=10, pad=4)
    ax_loss.set_ylabel("%")
    ax_loss.set_ylim(0, 105)
    ax_loss.grid(True, color="#222244", linewidth=0.5)

    hosts = list(snapshot.keys())
    loss_values = []
    loss_colors = []

    for host, data in snapshot.items():
        color = data["color"]
        ts_list  = data["timestamps"]
        lat_list = data["latencies"]

        if not ts_list:
            loss_values.append(0)
            loss_colors.append(color)
            continue

        datetimes = [dt.fromtimestamp(t) for t in ts_list]
        # Substitui timeout por NaN para não conectar linhas
        lats = [l if l is not None else float("nan") for l in lat_list]

        ax_lat.plot(
            datetimes, lats,
            color=color, linewidth=1.4,
            label=host, marker="o", markersize=2, markevery=5,
        )

        # Barras de timeout em vermelho claro
        timeouts = [dt.fromtimestamp(ts_list[i]) for i, l in enumerate(lat_list) if l is None]
        for td in timeouts:
            ax_lat.axvline(td, color="#FF4466", alpha=0.3, linewidth=0.8)

        loss_values.append(data["loss_pct"])
        loss_colors.append(color)

    # Barras de loss por host
    if hosts:
        bars = ax_loss.bar(hosts, loss_values, color=loss_colors, alpha=0.8, width=0.5)
        for bar, val in zip(bars, loss_values):
            if val > 0:
                ax_loss.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 1,
                    f"{val:.1f}%",
                    ha="center", va="bottom",
                    fontsize=8, color="#EEEEEE"
                )

    # Formatar eixo X como hora
    for ax in (ax_lat,):
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
        fig.autofmt_xdate(rotation=30, ha="right")

    if hosts:
        ax_lat.legend(
            loc="upper left", fontsize=8,
            facecolor="#1A1A2E", edgecolor="#333355",
            labelcolor="#EEEEEE"
        )

    fig.tight_layout(pad=1.5)
    return fig


def export_png(snapshot: dict, filepath: Optional[str] = None) -> str:
    if not filepath:
        filepath = str(REPORTS_DIR / f"ping_graph_{_ts_label()}.png")

    fig = _build_figure(snapshot)
    fig.savefig(filepath, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return filepath


# ─────────────────────────────────────────────────────────
# PDF
# ─────────────────────────────────────────────────────────
def export_pdf(snapshot: dict, filepath: Optional[str] = None) -> str:
    if not filepath:
        filepath = str(REPORTS_DIR / f"ping_report_{_ts_label()}.pdf")

    # 1. Gerar imagem do gráfico em memória
    fig = _build_figure(snapshot, figsize=(14, 5))
    img_buf = io.BytesIO()
    fig.savefig(img_buf, format="PNG", dpi=120, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    img_buf.seek(0)

    # 2. Montar PDF
    doc = SimpleDocTemplate(
        filepath,
        pagesize=landscape(A4),
        rightMargin=1.5 * cm, leftMargin=1.5 * cm,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title", parent=styles["Title"],
        fontSize=16, textColor=colors.HexColor("#00B4D8"),
        alignment=TA_CENTER,
    )
    sub_style = ParagraphStyle(
        "Sub", parent=styles["Normal"],
        fontSize=9, textColor=colors.grey,
        alignment=TA_CENTER,
    )
    normal = styles["Normal"]

    story = []
    story.append(Paragraph("InfinityPinger — Relatório de Ping", title_style))
    story.append(Paragraph(
        f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        sub_style
    ))
    story.append(Spacer(1, 0.5 * cm))

    # Gráfico
    rl_img = RLImage(img_buf, width=24 * cm, height=9 * cm)
    story.append(rl_img)
    story.append(Spacer(1, 0.5 * cm))

    # Tabela de estatísticas
    table_data = [["Host", "Enviados", "Recebidos", "Perda %",
                   "Min (ms)", "Avg (ms)", "Max (ms)"]]
    for host, d in snapshot.items():
        def fmt(v): return f"{v:.1f}" if v is not None else "—"
        table_data.append([
            host,
            str(d["sent"]),
            str(d["received"]),
            f"{d['loss_pct']:.1f}%",
            fmt(d["min_ms"]),
            fmt(d["avg_ms"]),
            fmt(d["max_ms"]),
        ])

    col_widths = [6*cm, 2.5*cm, 2.5*cm, 2.5*cm, 3*cm, 3*cm, 3*cm]
    tbl = Table(table_data, colWidths=col_widths)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0D3B66")),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTSIZE",   (0, 0), (-1, 0), 10),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor("#1A1A2E"), colors.HexColor("#16213E")]),
        ("TEXTCOLOR",  (0, 1), (-1, -1), colors.HexColor("#DDDDDD")),
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#333355")),
        ("FONTSIZE",   (0, 1), (-1, -1), 9),
        ("ROWHEIGHT",  (0, 0), (-1, -1), 0.7 * cm),
    ]))
    story.append(tbl)

    doc.build(story)
    return filepath
