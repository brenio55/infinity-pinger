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
# Worker de ping por host
# ─────────────────────────────────────────────
class HostPinger(threading.Thread):
    """
    Thread que pinga um host em intervalos regulares e mantém
    um histórico circular de resultados.
    """

    MAX_HISTORY = 86400  # 24h a 1s de intervalo

    def __init__(
        self,
        host: str,
        interval: float = 1.0,
        timeout: float = 2.0,
        on_result: Optional[Callable[[tuple], None]] = None,
    ):
        super().__init__(daemon=True)
        self.host = host
        self.interval = interval
        self.timeout = timeout
        self.on_result = on_result

        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        # Histórico (separado para otimização de memória)
        self.timestamps: deque[float] = deque(maxlen=self.MAX_HISTORY)
        self.latencies: deque[Optional[float]] = deque(maxlen=self.MAX_HISTORY)

        # Estatísticas acumuladas
        self._sent = 0
        self._received = 0
        self._min_ms: Optional[float] = None
        self._max_ms: Optional[float] = None
        self._sum_ms: float = 0.0

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
        return self._min_ms

    @property
    def avg_ms(self) -> Optional[float]:
        return (self._sum_ms / self._received) if self._received > 0 else None

    @property
    def max_ms(self) -> Optional[float]:
        return self._max_ms

    # ── Ciclo principal ───────────────────────────────────
    def run(self):
        while not self._stop_event.is_set():
            ts, latency, success = self._do_ping()
            with self._lock:
                self.timestamps.append(ts)
                self.latencies.append(latency)
                self._sent += 1
                if success and latency is not None:
                    self._received += 1
                    self._sum_ms += latency
                    if self._min_ms is None or latency < self._min_ms:
                        self._min_ms = latency
                    if self._max_ms is None or latency > self._max_ms:
                        self._max_ms = latency

            if self.on_result:
                self.on_result((ts, latency, success))

            self._stop_event.wait(self.interval)

    def stop(self):
        self._stop_event.set()

    # ── Execução do ping via subprocess ───────────────────
    def _do_ping(self) -> tuple[float, Optional[float], bool]:
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
                return (ts, latency, True)
            else:
                return (ts, None, False)

        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return (ts, None, False)

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
    def get_history_snapshot(self) -> tuple[list[float], list[Optional[float]]]:
        with self._lock:
            return list(self.timestamps), list(self.latencies)
