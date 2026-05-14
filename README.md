# InfinityPinger

Clone funcional do **PingPlotter** escrito em Python puro.  
Pinga múltiplos hosts simultaneamente, exibe latência em tempo real com gráficos e exporta relatórios.

---

## Funcionalidades

| Feature | Status |
|---|---|
| Ping em múltiplos hosts (paralelo) | ✅ |
| Gráfico de latência em tempo real | ✅ |
| Gráfico de perda de pacotes | ✅ |
| Tabela de estatísticas (min/avg/max/loss) | ✅ |
| Exportar CSV | ✅ |
| Exportar gráfico PNG | ✅ |
| Exportar relatório PDF | ✅ |
| Configurações (intervalo/timeout) | ✅ |
| Zoom/Pan no gráfico | ✅ |

---

## Requisitos

- Python 3.10+
- Windows (suporte Linux/macOS planejado)

```bash
pip install -r requirements.txt
```

## Executar

```bash
python main.py
```

## Estrutura

```
infinityPinger/
├── main.py
├── requirements.txt
├── core/
│   ├── pinger.py     # HostPinger (thread por host)
│   ├── session.py    # PingSession (gerenciador)
│   └── reporter.py   # Exportação CSV/PNG/PDF
├── ui/
│   ├── app.py        # Janela principal
│   ├── host_panel.py # Sidebar de hosts
│   ├── chart_panel.py# Gráfico matplotlib
│   ├── stats_table.py# Tabela de estatísticas
│   └── dialogs.py    # Diálogos
└── reports/          # Relatórios gerados
```

## Versão

`v0.1.0` — Versão inicial com todas as funcionalidades básicas.
