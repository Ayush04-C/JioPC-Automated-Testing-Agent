# Installation Guide

Follow these exact steps to install the `jiopc-testing-agent` on a fresh Ubuntu 24.04 + LxQt VM.

1. Update package list:
```bash
sudo apt-get update
```

2. Install system dependencies:
```bash
sudo apt-get install -y python3 python3-pip xvfb xdg-utils git
```

3. Clone the repository:
```bash
git clone https://github.com/Ayush04-C/jiopc-testing-agent.git
cd jiopc-testing-agent
```

4. Install Python dependencies:
```bash
pip3 install pyyaml psutil pyxdg playwright openai
```

5. Install Playwright browser dependencies:
```bash
python3 -m playwright install chromium
```

6. Build Debian package (Optional):
```bash
dpkg-deb --build packaging jiopc-testing-agent_0.1.0_all.deb
sudo dpkg -i jiopc-testing-agent_0.1.0_all.deb
```
