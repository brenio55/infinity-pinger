# InfinityPinger Architecture

## Overview
InfinityPinger is composed of two main layers: the `core` logic (handling background ping operations and data collection) and the `ui` layer (handling visualization and user interaction).

## Directory Structure

### `core/`
The core engine for the application.
- **`pinger.py`**: Contains `HostPinger`, a `threading.Thread` worker. It runs a continuous ping loop using the system `ping` command (optimized for Windows). It maintains two circular buffers (`deque`) for timestamps and latencies, and computes O(1) running statistics (min, max, avg) to minimize CPU overhead.
- **`session.py`**: Contains `PingSession`, a manager that controls multiple `HostPinger` threads, aggregates their data, and provides a centralized snapshot for the UI.
- **`reporter.py`**: Handles exporting ping session data to various formats like CSV, PNG, and PDF (using `matplotlib` and `reportlab`).

### `ui/`
The graphical user interface built with `customtkinter` and embedded `matplotlib` charts.
- **`app.py`**: The main application window (`App`). It sets up the layout, toolbar, sidebar, and status bar. It orchestrates the flow of data from `PingSession` to the UI components.
- **`chart_panel.py`**: A specialized panel containing a dynamic `matplotlib` plot. It efficiently redraws lines, packet loss overlays (LOZ spans), and a shared timeline based on the selected time window.
- **`host_panel.py`**: The sidebar component allowing users to add, remove, and pause hosts.
- **`stats_table.py`**: Component for showing raw statistics.
- **`dialogs.py`**: Modals for application settings and exporting data.

### Root Files
- **`main.py`**: Entry point. It initializes and runs the `App` main loop.
- **`requirements.txt`**: Python dependencies (`customtkinter`, `matplotlib`, `icmplib`, etc.).
- **`InfinityPinger.spec`**: PyInstaller specification for building the standalone executable.
