import re

with open('paper_latex/generate_full_manuscript.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix `aquavolt_telemetry.db`
text = text.replace("`aquavolt_telemetry.db`", r"\texttt{aquavolt\_telemetry.db}")
text = text.replace("`PROVENANCE.json`", r"\texttt{PROVENANCE.json}")
text = text.replace(r"\text{Clay_fraction}", r"\text{Clay\_fraction}")
text = text.replace(r"\text{Clay\_fraction}_m", r"\text{Clay}_{m}")
text = text.replace("(+8.20\,ppb/yr)", r"(+8.20 ppb/year)")
text = text.replace(r"\text{tCO}_2\text{e/year}", r"\text{tCO}_2\text{e}/\text{year}")
text = text.replace(r"\text{tCO}_2\text{e}", r"\text{tCO}_2\text{e}")
text = text.replace(r"\text{tCO}_2\text{e/yr}", r"\text{tCO}_2\text{e}/\text{yr}")
text = text.replace(r"\text{tCO}_2\text{e/year}", r"\text{tCO}_2\text{e}/\text{year}")

# Fix Appendix C itemize/enumerate
appendix_c_old = r'''\section{Complete 25-Sensor Plugin Specification \& Telemetry Schema}\label{app:sensor_catalog}
The SQLite database schema (\texttt{aquavolt\_telemetry.db}) and Google Sheets ledger log 29 synchronized attributes per sector-hour:
\begin{itemize}
    \item \texttt{id}: Monotonically increasing primary key integer.
    \item \texttt{timestamp}: ISO 8601 UTC string (\texttt{YYYY-MM-DDTHH:MM:SSZ}).
    \item \texttt{latitude}, \texttt{longitude}: WGS84 coordinates ($38.548^\circ\text{N}, -121.878^\circ\text{W}$).
    \item \texttt{sector\_row}, \texttt{sector\_col}: Discrete grid index ($0 \le r, c \le 15$).
    \item \texttt{ndvi}, \texttt{ndwi}, \texttt{ndwi\_real}, \texttt{savi}, \texttt{lai}, \texttt{fcover}: Optical vegetation indices.
    \item \texttt{lst}, \texttt{lst\_modis}, \texttt{lst\_source}: Spaceborne thermal radiometry channels.
    \item \texttt{Kc}, \texttt{Ks}, \texttt{Dr}, \texttt{TAW}, \texttt{RAW}: PIML crop coefficient and root-zone water balance parameters.
    \item \texttt{ETc}, \texttt{water\_need}: Predicted actual evapotranspiration and irrigation requirement ($\text{mm/day}$).
    \item \texttt{air\_temp}, \texttt{humidity}, \texttt{solar\_rad}, \texttt{precip}, \texttt{soil\_temp}, \texttt{soil\_moisture}: In-situ and reanalysis meteorology.
    \item \texttt{scene\_id}, \texttt{field\_name}, \texttt{methane\_anomaly}, \texttt{sar\_rvi}, \texttt{gravity\_anomaly}: Multi-modal dMRV indicators.
\end{itemize}'''

appendix_c_new = r'''\section{Complete 25-Sensor Plugin Specification \& Telemetry Schema}\label{app:sensor_catalog}
The SQLite database schema (\texttt{aquavolt\_telemetry.db}) and Google Sheets ledger log 29 synchronized attributes per sector-hour:
\begin{enumerate}
    \item \texttt{id}: Monotonically increasing primary key integer.
    \item \texttt{timestamp}: ISO 8601 UTC string (\texttt{YYYY-MM-DDTHH:MM:SSZ}).
    \item \texttt{latitude}, \texttt{longitude}: WGS84 coordinates ($38.548^\circ\text{N}, -121.878^\circ\text{W}$).
    \item \texttt{sector\_row}, \texttt{sector\_col}: Discrete grid index ($0 \le r, c \le 15$).
    \item \texttt{ndvi}, \texttt{ndwi}, \texttt{ndwi\_real}, \texttt{savi}, \texttt{lai}, \texttt{fcover}: Optical vegetation indices.
    \item \texttt{lst}, \texttt{lst\_modis}, \texttt{lst\_source}: Spaceborne thermal radiometry channels.
    \item \texttt{Kc}, \texttt{Ks}, \texttt{Dr}, \texttt{TAW}, \texttt{RAW}: PIML crop coefficient and root-zone water balance parameters.
    \item \texttt{ETc}, \texttt{water\_need}: Predicted actual evapotranspiration and irrigation requirement ($\text{mm/day}$).
    \item \texttt{air\_temp}, \texttt{humidity}, \texttt{solar\_rad}, \texttt{precip}, \texttt{soil\_temp}, \texttt{soil\_moisture}: In-situ and reanalysis meteorology.
    \item \texttt{scene\_id}, \texttt{field\_name}, \texttt{methane\_anomaly}, \texttt{sar\_rvi}, \texttt{gravity\_anomaly}: Multi-modal dMRV indicators.
\end{enumerate}'''

if appendix_c_old in text:
    text = text.replace(appendix_c_old, appendix_c_new)

with open('paper_latex/generate_full_manuscript.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated generate_full_manuscript.py with proper escaping.")
