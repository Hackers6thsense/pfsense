# Dashboards

Oblivion provides both CLI and browser-based dashboards for live monitoring.

## CLI Rich Dashboard

- Launch with:
  ```bash
  oblivion dashboard
  ```
- Features:
  - Real-time stats (engagement, assets, playbook)
  - Color-coded status
  - Spinner for live attacks
  - Keyboard shortcuts:
    - `s` = stop all attacks
    - `q` = quit

## Browser Dashboard

- Visit [http://localhost:8000/dashboard?token=YOURTOKEN](http://localhost:8000/dashboard?token=changeme)
- Features:
  - Real-time updates via WebSockets
  - Stop All Attacks button
  - Success vs Failure pie chart
  - Keyboard shortcuts: `s` (stop), `q` (quit)
  - Live log tail

![Browser Dashboard Screenshot](assets/dashboard_screenshot.png)