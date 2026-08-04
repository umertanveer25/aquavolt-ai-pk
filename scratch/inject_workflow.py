import os
import re

latex_file = r"C:\Users\umert\aquavolt-ai-pk\paper_latex\sn-article.tex"

with open(latex_file, "r", encoding="utf-8") as f:
    content = f.read()

# We need to insert the TikZ package at the top
tikz_pkg = r"""\usepackage{tikz}
\usetikzlibrary{shapes.geometric, arrows, positioning}
"""
content = content.replace(r"\usepackage{graphicx}", r"\usepackage{graphicx}" + "\n" + tikz_pkg)

# We need to inject the Workflow Diagram (System Architecture) and its discussion into Section 3
tikz_diagram = r"""
\begin{figure}[h]
\centering
\begin{tikzpicture}[node distance=1.5cm,
    box/.style={rectangle, draw=black, thick, minimum width=3cm, minimum height=1cm, align=center},
    diamondbox/.style={diamond, draw=black, thick, minimum width=2cm, minimum height=1cm, align=center},
    arrow/.style={thick,->,>=stealth}]

    % Nodes
    \node (apis) [box] {Satellites \& APIs \\ (Sentinel-2, ECOSTRESS, Open-Meteo)};
    \node (github) [box, below=of apis] {GitHub Actions \\ (Autonomous Worker)};
    \node (sheets) [box, below=of github] {Google Sheets \\ (Cloud Database)};
    \node (partition) [diamondbox, below=of sheets] {Capacity \\ Limit?};
    \node (newsheet) [box, left=of partition, xshift=-1cm] {Create New \\ Spreadsheet};
    \node (append) [box, right=of partition, xshift=1cm] {Append Row to \\ Current Sheet};
    \node (piml) [box, right=of github, xshift=3cm] {PIML Training Loop \\ (Weekly)};
    \node (weights) [box, above=of piml] {Update MLP \\ Weights};

    % Arrows
    \draw [arrow] (apis) -- node[anchor=west] {Hourly Fetch} (github);
    \draw [arrow] (github) -- node[anchor=west] {Logs Telemetry} (sheets);
    \draw [arrow] (sheets) -- (partition);
    \draw [arrow] (partition) -- node[anchor=bottom] {Yes} (newsheet);
    \draw [arrow] (partition) -- node[anchor=bottom] {No} (append);
    
    \draw [arrow] (sheets.east) -| node[anchor=west, yshift=2cm] {Weekly 1000 Rows} (piml.south);
    \draw [arrow] (piml) -- node[anchor=west] {Gradient Descent} (weights);
    \draw [arrow] (weights.west) -- node[anchor=bottom] {Auto-Commit} (github.east);

\end{tikzpicture}
\caption{Figure 2: The AquaVolt-AI Zero-Touch Serverless Workflow Diagram. A completely autonomous CI/CD architecture replacing physical edge IoT hubs.}
\label{fig:workflow}
\end{figure}

\subsection{Detailed Analysis of Figure \ref{fig:workflow}: The Serverless Workflow}
Figure \ref{fig:workflow} visually deconstructs the core software engineering breakthrough of the AquaVolt-AI architecture. Unlike traditional IoT networks that rely on physical base stations in the field (such as Microsoft FarmBeats), this workflow operates entirely in the cloud as a "Zero-Touch" pipeline. 

The top-down data flow begins with the GitHub Actions autonomous worker, which is triggered via a YAML cron schedule. Every hour, the worker queries the three primary Satellite APIs (Sentinel-2, ECOSTRESS, and Open-Meteo), bypassing the need for physical weather stations. The data is normalized and pushed directly into a Google Sheets cloud database. This specific database choice leverages free-tier API quotas, democratizing the architecture for developing nations.

Crucially, the diamond decision-node in Figure \ref{fig:workflow} highlights the system's built-in fault tolerance. Free-tier cloud databases impose strict row limits. To prevent catastrophic data loss when the capacity is reached, the autonomous worker executes an Auto-Partitioning logic. It evaluates the sheet's capacity and dynamically spawns a new spreadsheet without human intervention, ensuring unbroken data continuity. Finally, the feedback loop on the right side of the diagram illustrates the weekly Physics-Informed Machine Learning (PIML) training cycle. The system pulls the latest telemetry, executes a gradient descent optimization pass to adjust the neural network weights, and automatically commits those weights back into the GitHub repository, allowing the model to self-evolve continuously.
"""

# Replace "Figure 2" in the old text with Figure 3 etc. since this is the new Figure 2.
# We will just inject it right after the GitHub Actions CI/CD Worker section
target_text = r"\subsection{The GitHub Actions CI/CD Worker}"

# Find where to inject
if target_text in content:
    # Inject right before the next subsection
    insert_idx = content.find(r"\subsection{Automated Database Partitioning and Fault Tolerance}")
    content = content[:insert_idx] + tikz_diagram + "\n" + content[insert_idx:]

# Fix Figure numbers in captions to accommodate the new Figure 2
content = content.replace("Figure 2: Regression", "Figure 3: Regression")
content = content.replace("Figure 3: 36-Day", "Figure 4: 36-Day")
content = content.replace("Figure 4: Fault Tolerance", "Figure 5: Fault Tolerance")

content = content.replace(r"\ref{fig:scatter}: The Regression Scatter Plot", r"\ref{fig:scatter}: The Regression Scatter Plot (Figure 3)")
content = content.replace(r"Figure 3 demonstrates that AquaVolt", r"Figure \ref{fig:timeseries} demonstrates that AquaVolt")
content = content.replace(r"Figure 4, when the telemetry dropped", r"Figure \ref{fig:gap}, when the telemetry dropped")


with open(latex_file, "w", encoding="utf-8") as f:
    f.write(content)

print("Injected Workflow Diagram and discussion!")
