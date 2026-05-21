# Yeast-GEM (Yeast9) Resources

## Model Download
- **SBML File (Raw):** [yeast-GEM.xml](https://raw.githubusercontent.com/SysBioChalmers/yeast-GEM/main/model/yeast-GEM.xml)
- **GitHub Repository:** [SysBioChalmers/yeast-GEM](https://github.com/SysBioChalmers/yeast-GEM)

## Initial Flux Constraints (Standard Aerobic Glucose Growth)
| Reaction ID | Name | Lower Bound | Upper Bound |
| :--- | :--- | :--- | :--- |
| `r_1714` | D-glucose exchange | -10.0 | 0.0 |
| `r_1992` | Oxygen exchange | -1000.0 | 0.0 |
| `r_1654` | Ammonium exchange | -1000.0 | 1000.0 |
| `r_2005` | Phosphate exchange | -1000.0 | 1000.0 |
| `r_2060` | Sulfate exchange | -1000.0 | 1000.0 |
| `r_4046` | ATP maintenance | 0.7 | 1000.0 |
| `r_2111` | Biomass production | 0.0 | 1000.0 |

*Note: Reaction IDs may vary slightly between versions, verify with the model file.*

- **Goebl Lab (IU) - SCF Complex Regulation:** Focus on CDC34/CDC53 mediated degradation of Sic1/Gcn4 and its metabolic burden.

## Pathway Kinetics & Gcn4 Bottlenecks (2026-03-23)
- **Pathway: Pentose Phosphate / Xylose Fermentation**
  - **XYL1 (Xylose Reductase):** k_cat ~ 40 - 60 s⁻¹ (C. shehatae/P. stipitis in S. cerevisiae)
  - **XYL2 (Xylitol Dehydrogenase):** k_cat ~ 20 s⁻¹
  - **XKS1 (Xylulokinase):** k_cat ~ 150 - 200 s⁻¹
- **Gcn4-mediated Bottlenecks (SCF Regulation):**
  - Rapid degradation of Gcn4 by SCF complex limits the transcriptional response for amino acid biosynthesis.
  - Primary Bottlenecks: **HIS** (Histidine), **ILE** (Isoleucine), **LEU** (Leucine), and **VAL** (Valine) biosynthesis pathways.
