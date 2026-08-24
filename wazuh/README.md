# 🛡️ AquaVolt-AI — Wazuh SIEM & Cybersecurity Integration

This directory contains the production configuration and custom detection rules for integrating **Wazuh SIEM / XDR** with AquaVolt-AI's digital MRV platform.

---

### 📂 Directory Structure

* **`agent_ossec.conf`**: Wazuh Agent configuration with real-time File Integrity Monitoring (FIM) on `data/`, `database/`, and `api/`.
* **`rules/aquavolt_rules.xml`**: Custom Wazuh SIEM detection rules for data tampering, API brute forcing, and sensor spoofing.
* **`docker-compose.wazuh.yml`**: 1-click Docker deployment for Wazuh Manager & Dashboard.

---

### 🚀 Quickstart

1. **Start the Wazuh SIEM Stack**:
   ```bash
   docker compose -f wazuh/docker-compose.wazuh.yml up -d
   ```
2. **Access the Wazuh Security Dashboard**:
   * URL: `https://localhost:443`
   * View live alerts, MITRE ATT&CK mappings, and VM0042 data integrity audit trails.
