"""
AquaVolt-AI: Wazuh SIEM Security & Audit Logger
================================================
Generates RFC 5424 / Wazuh JSON-formatted security event streams for:
  1. API Authentication attempts & Token Verification
  2. dMRV Telemetry Ingestion Events
  3. Methane Physical Anomaly / Spoofing Detections
  4. Verra VM0042 Carbon Credit Issuance Logs
  5. File Integrity & Drone Cryptographic Attestations
"""

import os
import json
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(ROOT_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)
SECURITY_LOG_FILE = os.path.join(LOGS_DIR, "wazuh_security.json")

class WazuhSecurityLogger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(WazuhSecurityLogger, cls).__new__(cls)
            cls._instance._setup_logger()
        return cls._instance

    def _setup_logger(self):
        self.logger = logging.getLogger("AquaVolt_Wazuh_SIEM")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
        
        # 10 MB rotating file handler, up to 5 backups
        handler = RotatingFileHandler(
            SECURITY_LOG_FILE,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8"
        )
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log_event(self, event_type: str, severity: str, status: str, details: dict, client_ip: str = "127.0.0.1", user_agent: str = "AquaVolt-System"):
        """
        Logs a structured security event parsed directly by Wazuh JSON decoders.
        """
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "app_name": "aquavolt-ai-pk",
            "facility": "dMRV-Core",
            "event_type": event_type,
            "severity": severity,  # INFO, WARNING, CRITICAL
            "status": status,      # SUCCESS, DENIED, ANOMALY_DETECTED
            "client_ip": client_ip,
            "user_agent": user_agent,
            "details": details
        }
        self.logger.info(json.dumps(payload))

# Global Singleton instance
wazuh_audit = WazuhSecurityLogger()

if __name__ == "__main__":
    wazuh_audit.log_event(
        event_type="SYSTEM_STARTUP",
        severity="INFO",
        status="SUCCESS",
        details={"message": "Wazuh SIEM Security Module Initialized", "version": "2.1.0"}
    )
    print(f"[OK] Successfully wrote test security event to: {SECURITY_LOG_FILE}")
