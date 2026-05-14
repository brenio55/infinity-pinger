"""
core/pinger.py
Thread worker responsável por pingar um único host continuamente.
"""

import threading
import subprocess
import re
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional, Callable


# ─────────────────────────────────────────────
# Estrutura de resultado de um único ping
# ─────────────────────────────────────────────
@dataclass
class PingResult:
    host: str
    timestamp: float
    latency_ms: Optional[float]   # None = timeout / perda de pacote
    success: bool


# ─────────────────────────────────────────────
# Worker de ping por host
# ─────────────────────────────────────────────
class HostPinger(threading.Thread):
    """
    Thread que pinga um host em intervalos regulares e mantém
    um histórico circular de resultados.
    """

    MAX_HISTORY = 3600   # 1h a 1s de intervalo

    def __init__(
        self,
        host: str,
        interval: float = 1.0,
        timeout: float = 2.0,
        on_result: Optional[Callable[[PingResult], None]] = None,
    ):
        super().__init__(daemon=True)
        self.host = host
        self.interval = interval
        self.timeout = timeout
        self.on_result = on_result

        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        # Histórico: deque de PingResult
        self.history: deque[PingResult] = deque(maxlen=self.MAX_HISTORY)

        # Estatísticas acumuladas
        self._sent = 0
        self._received = 0
        self._latencies: list[float] = []

    # ── Propriedades de estatística ──────────────────────
    @property
    def sent(self) -> int:
        return self._sent

    @property
    def received(self) -> int:
        return self._received

    @property
    def loss_pct(self) -> float:
        if self._sent == 0:
            return 0.0
        return 100.0 * (self._sent - self._received) / self._sent

    @property
    def min_ms(self) -> Optional[float]:
        return min(self._latencies) if self._latencies else None

    @property
    def avg_ms(self) -> Optional[float]:
        return sum(self._latencies) / len(self._latencies) if self._latencies else None

    @property
    def max_ms(self) -> Optional[float]:
        return max(self._latencies) if self._latencies else None

    # ── Ciclo principal ───────────────────────────────────
    def run(self):
        while not self._stop_event.is_set():
            result = self._do_ping()
            with self._lock:
                self.history.append(result)
                self._sent += 1
                if result.success and result.latency_ms is not None:
                    self._received += 1
                    self._latencies.append(result.latency_ms)

            if self.on_result:
                self.on_result(result)

            self._stop_event.wait(self.interval)

    def stop(self):
        self._stop_event.set()

    # ── Execução do ping via subprocess ───────────────────
    def _do_ping(self) -> PingResult:
        ts = time.time()
        try:
            # Windows: ping -n 1 -w <timeout_ms> <host>
            timeout_ms = int(self.timeout * 1000)
            cmd = ["ping", "-n", "1", "-w", str(timeout_ms), self.host]

            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout + 2,
                creationflags=subprocess.CREATE_NO_WINDOW,  # sem janela no Windows
            )
            output = proc.stdout + proc.stderr
            latency = self._parse_latency_windows(output)

            if latency is not None:
                return PingResult(self.host, ts, latency, True)
            else:
                return PingResult(self.host, ts, None, False)

        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return PingResult(self.host, ts, None, False)

    @staticmethod
    def _parse_latency_windows(output: str) -> Optional[float]:
        """Extrai a latência em ms da saída do ping do Windows."""
        # Padrão: "tempo=15ms" ou "time=15ms" ou "time<1ms"
        match = re.search(r"[Tt]empo[=<](\d+)ms|[Tt]ime[=<](\d+)ms", output)
        if match:
            val = match.group(1) or match.group(2)
            return float(val)
        # Padrão "time<1ms" → retorna 0.5
        if re.search(r"[Tt]empo<1ms|[Tt]ime<1ms", output):
            return 0.5
        return None

    # ── Snapshot thread-safe do histórico ────────────────
    def get_history_snapshot(self) -> list[PingResult]:
        with self._lock:
            return list(self.history)
