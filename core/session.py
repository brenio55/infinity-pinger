"""
core/session.py
Gerenciador central de sessão: controla múltiplos HostPinger,
mantém estado global e notifica a UI via callbacks.
"""

import threading
from typing import Callable, Optional
from .pinger import HostPinger, PingResult


# Paleta de cores para os hosts no gráfico
HOST_COLORS = [
    "#00B4D8",  # ciano
    "#F72585",  # rosa
    "#4CC9F0",  # azul claro
    "#F4A261",  # laranja
    "#7209B7",  # roxo
    "#2DC653",  # verde
    "#FFB703",  # amarelo
    "#EF233C",  # vermelho
    "#8338EC",  # violeta
    "#3A86FF",  # azul brilhante
]


class PingSession:
    """
    Sessão de ping: gerencia uma lista de hosts,
    cria/destrói HostPingers e provê snapshot consolidado
    para renderização.
    """

    def __init__(
        self,
        interval: float = 1.0,
        timeout: float = 2.0,
        on_update: Optional[Callable[[], None]] = None,
    ):
        self.interval = interval
        self.timeout = timeout
        self.on_update = on_update   # chamado após cada resultado

        self._lock = threading.Lock()
        self._pingers: dict[str, HostPinger] = {}   # host → pinger
        self._colors: dict[str, str] = {}            # host → cor
        self._running = False

    # ── Controle da sessão ────────────────────────────────
    @property
    def is_running(self) -> bool:
        return self._running

    def start(self):
        """Inicia todos os pingers cadastrados."""
        with self._lock:
            self._running = True
            for pinger in self._pingers.values():
                if not pinger.is_alive():
                    pinger.start()

    def stop(self):
        """Para todos os pingers e aguarda encerramento."""
        with self._lock:
            self._running = False
            for pinger in self._pingers.values():
                pinger.stop()

    def clear_history(self):
        """Limpa o histórico de todos os hosts sem parar os pingers."""
        with self._lock:
            for pinger in self._pingers.values():
                pinger.history.clear()
                pinger._sent = 0
                pinger._received = 0
                pinger._latencies.clear()

    # ── Gerenciamento de hosts ────────────────────────────
    def add_host(self, host: str) -> bool:
        """Adiciona host. Retorna False se já existir."""
        host = host.strip()
        if not host:
            return False
        with self._lock:
            if host in self._pingers:
                return False

            color_idx = len(self._pingers) % len(HOST_COLORS)
            color = HOST_COLORS[color_idx]
            self._colors[host] = color

            pinger = HostPinger(
                host=host,
                interval=self.interval,
                timeout=self.timeout,
                on_result=self._on_ping_result,
            )
            self._pingers[host] = pinger

            if self._running:
                pinger.start()
            return True

    def remove_host(self, host: str):
        """Remove e para o pinger de um host."""
        with self._lock:
            pinger = self._pingers.pop(host, None)
            self._colors.pop(host, None)
        if pinger:
            pinger.stop()

    @property
    def hosts(self) -> list[str]:
        with self._lock:
            return list(self._pingers.keys())

    def get_color(self, host: str) -> str:
        return self._colors.get(host, "#FFFFFF")

    # ── Snapshot de dados para a UI ───────────────────────
    def get_snapshot(self) -> dict:
        """
        Retorna um dict com todos os dados necessários para
        renderizar gráficos e tabela. Thread-safe via cópia.
        """
        snapshot = {}
        with self._lock:
            for host, pinger in self._pingers.items():
                history = pinger.get_history_snapshot()
                timestamps = [r.timestamp for r in history]
                latencies  = [r.latency_ms if r.success else None for r in history]
                snapshot[host] = {
                    "color":     self._colors[host],
                    "timestamps": timestamps,
                    "latencies":  latencies,
                    "sent":      pinger.sent,
                    "received":  pinger.received,
                    "loss_pct":  pinger.loss_pct,
                    "min_ms":    pinger.min_ms,
                    "avg_ms":    pinger.avg_ms,
                    "max_ms":    pinger.max_ms,
                }
        return snapshot

    # ── Callback interno ──────────────────────────────────
    def _on_ping_result(self, result: PingResult):
        if self.on_update:
            self.on_update()
