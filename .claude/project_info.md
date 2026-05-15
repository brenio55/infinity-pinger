# InfinityPinger - AI Context

**InfinityPinger** is a desktop application designed to ping multiple network hosts concurrently and visualize the results (latencies and packet loss) over time. It is built using Python, `customtkinter` for the UI, and `matplotlib` for the charts. It is part of the **Orkestrae** ecosystem.

## Key Features
- **Concurrent Pinging**: Threads continuously ping configured hosts in the background.
- **Visual Analytics**: A dynamic matplotlib chart updates over time, highlighting packet loss and latency.
- **Exporting**: Users can export the captured session data to CSV, PNG, or PDF formats.
- **Optimization**: Data is stored efficiently using memory-efficient primitive `collections.deque` and O(1) running statistics to ensure smooth operation over long periods.

## Architecture
- `core/`: Contains the backend logic (`pinger.py` for background ping execution, `session.py` for centralized state management, `reporter.py` for exporting).
- `ui/`: Contains the frontend logic using CustomTkinter (`app.py`, `chart_panel.py`, etc.).
