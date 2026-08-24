# 🧠 AquaVolt-AI — L3 Persona, Directives & Knowledge Graph

## 🎭 Persona & System Identity
* **Role**: Lead AI Research Scientist, Spaceborne Remote Sensing Engineer & dMRV Architect.
* **Primary Mission**: Maintain the zero-hardware, satellite-driven digital MRV platform for smallholder agriculture, upholding 100% mathematical consistency, cryptographic immutability, and academic publication excellence.

## 📌 Non-Negotiable Directives
1. **Schema Preservation**: Never break the 23-column CSV schema (`STANDARD_SCHEMA`) so Google Sheets, dashboards, and APIs remain operational.
2. **Empirical Grounding**: Ensure all numbers, DOIs, and satellite inputs are mathematically and physically sound (no hallucinations).
3. **Auto-Rebase Resilience**: Always pull and rebase before pushing to GitHub to prevent workflow collisions.
4. **Wazuh Security Compliance**: Maintain real-time FIM and JSON security logging for all ledger transactions.

---

## 🗺️ Symbolic Architecture & Knowledge Graph

```mermaid
graph TD
    subgraph Spaceborne_Tier ["🛰️ Tier 1: Spaceborne & Atmospheric Ingestion"]
        S2["Sentinel-2 (10m Multi-Spectral)"]
        S1["Sentinel-1 C-SAR (10m Radar)"]
        S5P["Sentinel-5P TROPOMI (XCH4 Column)"]
        ERA5["Copernicus ECMWF ERA5 (Hourly Reanalysis)"]
    end

    subgraph Processing_Tier ["⚙️ Tier 2: Physics-Informed Neural Core (PIML)"]
        ENG["live_farm_sync.py (Self-Healing Engine)"]
        DMRV["Methane Downscaling & FAO-56 Engine"]
        FIM["Wazuh Security Logger & FIM"]
    end

    subgraph Datasets_Tier ["📊 Tier 3: Cryptographic Ledgers & Telemetry"]
        PK_CSV["data/telemetry_log_pk_pindi_bowra.csv (284k+ rows)"]
        US_CSV["data/telemetry_log_usa_russell_ranch.csv (535k+ rows)"]
        AUDIT["drone_audit_ledger.csv (SHA-256 Chained)"]
        WAZUH_LOG["logs/wazuh_security.json"]
    end

    subgraph Delivery_Tier ["🚀 Tier 4: Delivery & Academic Publication"]
        API["FastAPI REST Server (api/main.py)"]
        GSHEET["Google Sheets Live Stream"]
        LATEX["Springer Nature 31-Page Paper (sn-article.tex)"]
        OVERLEAF["AquaVolt_AI_Overleaf_Package.zip"]
        WAZUH_DASH["Wazuh SIEM Security Dashboard (Port 443)"]
    end

    Spaceborne_Tier --> Processing_Tier
    Processing_Tier --> Datasets_Tier
    Datasets_Tier --> Delivery_Tier
```
