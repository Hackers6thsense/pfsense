## Overview

Oblivion is a Python-based adversary emulation tool that simulates a malicious AI's attempts to achieve its goals through various cyber-attacks. It provides an interactive "Blue Team" interface to launch, monitor, and stop these simulated attacks.

A key feature is its integration with the Mistral AI API, which allows the simulator to dynamically generate attack plans and disinformation content, providing a more realistic and unpredictable training experience.

## Features

- **Interactive CLI:** A user-friendly command-line interface for the "Blue Team" to control the simulation.
- **Dynamic Adversary Emulation:** Uses the Mistral LLM to generate attack plans based on high-level goals.
- **Multiple Attack Simulations:**
    - Distributed Denial-of-Service (DDoS)
    - SQL Injection (SQLi)
    - Brute Force Login
    - Phishing (Generates email content via AI)
    - Ransomware (Simulates file encryption)
    - Real Exploit Delivery (via Metasploit)
- **AI-Powered Disinformation:** Generates convincing fake news articles on any topic for social engineering simulations.
- **Modular & Extensible:** Designed to be easily expanded with new attack modules and capabilities.
- **Safe for Educational Use:** All "attacks" are simulations and do not perform any actual malicious actions on live systems unless explicitly authorized and configured.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

- Python 3.8 or higher
- A Mistral AI API Key

### Installation

1.  **Clone the repository (or save the script):**
    If this were a Git repository, you would clone it. For now, just save the `oblivion_ai_sim.py` script to a local directory.

2.  **Install dependencies:**
    This project uses the `requests` library. You can install it using pip.

    ```bash
    pip install requests
    ```

3.  **Set up your API Key:**
    The simulator requires a Mistral AI API key to function. Set it as an environment variable named `MISTRAL_API_KEY`.

    **On macOS/Linux:**
    ```bash
    export MISTRAL_API_KEY='YOUR_API_KEY_HERE'
    ```

    **On Windows (Command Prompt):**
    ```bash
    set MISTRAL_API_KEY=YOUR_API_KEY_HERE
    ```
    **On Windows (PowerShell):**
    ```bash
    $env:MISTRAL_API_KEY="YOUR_API_KEY_HERE"
    ```

    > **Note:** For a more permanent solution, add the export command to your shell's startup file (e.g., `.bashrc`, `.zshrc`) or set it in your system's environment variable settings.

## Usage

Once the dependencies are installed and the API key is set, run the script from your terminal:

```bash
python oblivion_ai_sim.py

You will be greeted by the Blue Team Control Interface prompt:

--- Blue Team Control Interface ---
Commands: emulate, disinfo, start, target, stop, monitor, info, exit
Blue Team>

Available Commands

    emulate: Prompts for a high-level goal (e.g., "disrupt financial markets"). The AI will use the Mistral API to devise an attack plan, which you can then approve to launch.

    disinfo: Prompts for a topic. The AI will generate a fake news article about it.

    start: Manually launch a specific attack simulation. You will be prompted for the attack type and target.

    target: Manually set a target for the AI, such as infiltrating a system or launching a campaign.

    stop: Immediately stops all active attack simulation threads.

    monitor: Shows the status of all currently running simulation threads.

    info: Displays the current status of the Oblivion AI, including its intelligence level and lists of targets.

    exit: Stops all simulations and exits the program.

## Running on Kali Linux

Oblivion is easy to deploy in a Kali Linux VM for lab or blue-team exercise use. The project provides an automated setup script that installs all dependencies and configures Metasploit RPC for real exploit delivery.

### Prerequisites

- Kali Linux (tested on latest)
- Internet connectivity (for apt and pip installs)
- Sudo privileges

### Automated Setup

1. **Run the setup script:**
    ```bash
    chmod +x setup_kali.sh
    ./setup_kali.sh
    ```

2. **Environment Variables:**

   The setup script will print recommended export lines for Metasploit RPC connection. You may add these to your `~/.bashrc`:

    ```bash
    export MSF_RPC_HOST=127.0.0.1
    export MSF_RPC_PORT=55553
    export MSF_RPC_USER=msf
    export MSF_RPC_PASS=msf
    ```

   You will also need your Mistral API key:
    ```bash
    export MISTRAL_API_KEY='YOUR_API_KEY_HERE'
    ```

3. **Start the Oblivion tool:**

   Run from the project directory:
   ```bash
   python3 -m ob1.enhanced_oblivion
   ```

   (Or use your preferred entrypoint.)

### Notes

- The setup script will attempt to start `msfrpcd` and wait up to 10 seconds for it to listen; if it fails, check your Metasploit installation.
- All Python dependencies are installed via `requirements.txt`.
- Ensure `setup_kali.sh` is executable: `chmod +x setup_kali.sh`

## Advanced Safety Controls

### Per-Technique Policy Overrides

You can restrict specific attack techniques to different target ranges with `technique_overrides` in `policy.yaml`:

```yaml
engagement_id: lab-engagement
valid_from: "2025-08-01T00:00:00+00:00"
valid_to: "2025-12-31T23:59:59+00:00"
allowed_targets:
  cidrs: ["10.0.0.0/24"]
  hostnames: ["lab.internal"]
technique_overrides:
  T1046:
    allowed_targets:
      cidrs: ["0.0.0.0/0"]
      hostnames: []
  T1190:
    allowed_targets:
      cidrs: ["10.0.0.0/24"]
      hostnames: ["staging.*"]
```

If `technique_overrides` is omitted, the top-level allowed_targets apply to all techniques.

### Policy Hot-Reload

Oblivion will automatically reload policy.yaml if you edit it while running.

### Dry-Run Mode

To simulate actions without launching attacks, use the `--dry-run` or `-n` flag:

```bash
python -m ob1 --dry-run emulate
```

- All actions are logged as "dry_run".
- The dashboard and API indicate dry-run mode.

---

## Browser Dashboard

A simple real-time dashboard is available at [http://localhost:8000/dashboard](http://localhost:8000/dashboard) when the API server is running.

- Live updates via WebSockets for status and log events.
- "Stop All Attacks" button for immediate shutdown from browser.
- Success vs Failure chart for attack results.
- Keyboard shortcuts: <kbd>s</kbd> = stop all, <kbd>q</kbd> = quit (focus window first).
- **Authentication:** Requires an API token. Pass it in the URL as `?token=YOURTOKEN` or enter it at the prompt.

Example:
```
http://localhost:8000/dashboard?token=YOURTOKEN
```

---

## Installation via pip

You can install Oblivion Red-Team directly from PyPI:

```bash
pip install oblivion-redteam
```

After installation, use the `oblivion` command-line tool:

```bash
oblivion api
oblivion dashboard
```

## Run with Docker

Oblivion comes with a ready-to-use Docker build and a docker-compose setup for running with Metasploit and Nmap.

1. Build and start everything:

```bash
docker compose up --build
```

2. The Oblivion API will be available on [http://localhost:8000](http://localhost:8000) by default.

3. The Metasploit RPC server will be accessible to the oblivion app as `msf:55553`.

You can override environment variables (API token, Metasploit creds, etc.) in `docker-compose.yml`.

---

## REST API

Oblivion can be controlled and monitored remotely via a REST API (FastAPI).  
To launch the API server, run:

```bash
python -m ob1 api
```

The server will start on `http://0.0.0.0:8000`.

### Example Usage

- **Get status:**
  ```bash
  curl http://localhost:8000/status
  ```

- **Get discovered assets:**
  ```bash
  curl http://localhost:8000/assets
  ```

- **Launch an attack:**
  ```bash
  curl -X POST http://localhost:8000/attack -H "Content-Type: application/json" \
    -d '{"technique_id": "T1046", "params": {"cidr_or_host": "10.0.0.5", "rate": 1000}}'
  ```

- **Run a multi-step scenario:**
  ```bash
  curl -X POST http://localhost:8000/scenario -H "Content-Type: application/json" \
    -d '{"steps":[{"technique_id":"T1046","params":{"cidr_or_host":"10.0.0.5","rate":1000}}]}'
  ```

- **Live log stream:**
  Open a WebSocket to `ws://localhost:8000/logs` to receive engagement log lines in real time.

## Disclaimer

This tool is intended strictly for educational and research purposes in a controlled environment. It is designed to help security professionals, students, and researchers understand and defend against potential cyber threats.

DO NOT use this tool on any system or network for which you do not have explicit, written permission. The user is responsible for their actions. The creators of this tool are not responsible for any misuse or damage caused by this program.

## Contributing

Contributions are welcome! If you have ideas for new attack modules, features, or improvements, feel free to fork the repository and submit a pull request.

    Fork the Project

    Create your Feature Branch (git checkout -b feature/AmazingFeature)

    Commit your Changes (git commit -m 'Add some AmazingFeature')

    Push to the Branch (git push origin feature/AmazingFeature)

    Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE.md file for details.