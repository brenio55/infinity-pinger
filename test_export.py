import sys, time
sys.path.insert(0, '.')
from core.session import PingSession
from core.reporter import export_csv, export_png, export_pdf

session = PingSession(interval=1.0, timeout=2.0)
session.add_host('8.8.8.8')
session.add_host('1.1.1.1')
session.start()
print('Coletando dados por 5s...')
time.sleep(5)
session.stop()

snap = session.get_snapshot()
print(f'Hosts: {list(snap.keys())}')
for host, d in snap.items():
    avg = d["avg_ms"]
    loss = d["loss_pct"]
    print(f'  {host}: avg={avg:.1f}ms loss={loss:.0f}%')

csv_path = export_csv(snap)
png_path = export_png(snap)
pdf_path = export_pdf(snap)
print(f'CSV: {csv_path}')
print(f'PNG: {png_path}')
print(f'PDF: {pdf_path}')
print('Exportacoes OK!')
