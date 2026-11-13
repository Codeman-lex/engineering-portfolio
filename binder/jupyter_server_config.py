from pathlib import Path

root = Path.home() / "projects"
c.ServerProxy.servers = {
    name: {
        "command": [
            "streamlit", "run", str(root / name / "app.py"),
            "--server.address", "127.0.0.1", "--server.port", "{port}",
            "--server.headless", "true", "--browser.gatherUsageStats", "false",
        ],
        "timeout": 120,
    }
    for name in ("sentinel-ai", "veritas", "aegis")
}
