import os
import re
import json

TEX_PATH = r"C:\Users\umert\.gemini\antigravity\scratch\aquavolt-ai-pk\paper_latex\sn-article.tex"
with open(TEX_PATH, "r", encoding="utf-8") as f:
    tex = f.read()

audit_details = {}

# 1. Section structure check
sections = re.findall(r'\\section\*?\{([^}]+)\}', tex)
subsections = re.findall(r'\\subsection\*?\{([^}]+)\}', tex)
subsubsections = re.findall(r'\\subsubsection\*?\{([^}]+)\}', tex)

print(f"Total Sections: {len(sections)}")
print(f"Total Subsections: {len(subsections)}")
print(f"Total Subsubsections: {len(subsubsections)}")
audit_details["sections"] = sections
audit_details["subsections_count"] = len(subsections)
audit_details["subsubsections_count"] = len(subsubsections)

# 2. Check presence of core sections
core_secs = ["Introduction", "Related Work", "Materials and Methods", "Experimental Results", "Discussion", "Conclusion"]
found_core = {}
for cs in core_secs:
    found_core[cs] = any(cs.lower() in s.lower() for s in sections)
print("Core sections found:", found_core)
audit_details["core_sections_found"] = found_core

# 3. Check physical mechanisms and key concepts
mechanisms = [
    "Alternate Wetting and Drying",
    "AWD",
    "Richards",
    "van Genuchten",
    "Penman-Monteith",
    "FAO-56",
    "dual crop coefficient",
    "U-Net",
    "PIML",
    "ReLoBRaLo",
    "MRV",
    "mass conservation",
    "telemetry",
    "LoRaWAN",
    "TinyML",
    "redox",
    "methanogenic",
    "twitchell island",
    "capay clay"
]

found_mech = {}
for m in mechanisms:
    count = len(re.findall(re.escape(m), tex, re.IGNORECASE))
    found_mech[m] = count
print("Key mechanisms mention counts:", found_mech)
audit_details["mechanisms_counts"] = found_mech

# 4. Check specific numbers mentioned in text vs memory hub
key_values = {
    "RMSE 0.30": "0.30" in tex or "0.3000" in tex,
    "MAE 0.2688": "0.2688" in tex or "0.27" in tex,
    "NSE -5.04": "-5.04" in tex,
    "d-index 0.4629": "0.4629" in tex or "0.463" in tex,
    "Scan correlation 0.8641": "0.8641" in tex,
    "AmeriFlux ET 0.8812": "0.8812" in tex,
    "AmeriFlux CH4 -0.5777": "-0.5777" in tex,
    "Trend +8.20 ppb/yr": "8.20" in tex or "8.2" in tex,
    "Baseline mean 1883.16": "1883.16" in tex,
    "Monitoring mean 1912.59": "1912.59" in tex,
    "Cohen's d 1.9581": "1.9581" in tex,
    "t-test -9.0493": "-9.0493" in tex,
    "Mann-Whitney 154.0": "154.0" in tex or "154" in tex,
    "ANOVA F 20.5395": "20.5395" in tex
}
print("\nEmpirical key value consistency in TeX:")
for k, v in key_values.items():
    print(f"  {k}: {'FOUND' if v else 'MISSING'}")
audit_details["key_values_check"] = key_values

# Save audit details
with open(r"C:\Users\umert\.gemini\antigravity\scratch\aquavolt-ai-pk\.agents\auditor_victory_1\audit_deep_tex.json", "w") as f:
    json.dump(audit_details, f, indent=2)
print("\nDeep TeX audit saved to audit_deep_tex.json")
