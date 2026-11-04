# Model decisions

This document records what was measured while finishing the project, and what changed as a result. Every number can be reproduced with the commands below, run from `backend/`.

```bash
python -m ml.audit_fertilizer_dataset
python -m ml.train_yield
```

## Fertilizer: why the classifier was replaced

The hackathon prototype recommended fertilizer with a Random Forest trained on a public Kaggle dataset. Cross-validation shows the labels can't be learned from the inputs:

| Features | Random Forest | Gradient boosting | Chance (7 classes) |
| --- | --- | --- | --- |
| N, P, K, crop (as in the prototype) | 14.2% | 14.8% | 14.3% |
| All columns in the dataset | 14.7% | 14.7% | 14.3% |

More tuning can't fix this, because the labels are effectively independent of the features. The prototype's recommendation was close to a random pick.

### Alternatives considered

| Option | Why it was not used |
| --- | --- |
| [AgriNet](https://data.mendeley.com/datasets/c7tr9j78td/1) (Mendeley) | Real Soil Health Card values, but one district, rice only, with targets computed from STCR equations. A model would only imitate that formula. |
| [IEEE DataPort soil fertility data](https://ieee-dataport.org/node/14134) | Requires a paid subscription. |
| [Kaggle fertilizer prediction](https://www.kaggle.com/datasets/gdabhishek/fertilizer-prediction) | Its origin and contents could not be verified. |

### What replaced it

[`app/fertilizer.py`](../backend/app/fertilizer.py) is a small rule engine in which every value is traceable:

- **Soil ratings** use the ICAR-IISS bands: N 280/560, P 10/25, K 120/280 kg/ha.
- **Quantities** convert a reference dose to urea, DAP and MOP using each product's nutrient content, scaled to the field size.
- **Reference doses** exist only where a source could be cited. Rice and maize have one. Other crops return `no_verified_dose` instead of a made-up number.
- **Doses are not adjusted by soil rating.** A ±25% adjustment is often quoted, but no source confirming it was found, so soil ratings produce a suggestion to ask the lab and the dose stays unchanged.

To add a crop, add a cited entry to `REFERENCE_DOSES`.

The water tips are general guidance, not cited values: the app calls a season low below 200 mm of rain and high above 1,000 mm.

## Yield: an honest evaluation

### Problems found in the prototype

| Problem | Effect | Fix |
| --- | --- | --- |
| Random train/test split, with R² across all crops | The reported R² of 0.95 mostly reflected sugarcane's much larger yields, not forecasting skill. | Temporal split, a baseline, and metrics with sugarcane excluded. |
| `Area` used as a feature | It was a district-wide total, on a different scale from one farmer's field. | Removed. |
| N, P and K averages used as features | They were per-crop averages, so they added no information beyond the crop itself. | Removed. |
| Weather windows misread the season labels | "Winter" rice, the main monsoon crop, was given December to February weather: 38 mm of rain in Cuttack instead of about 1,350 mm. | Monthly NASA POWER data aggregated over each season's growing months. |
| Pipeline read a derived file | Training depended on a file carrying the wrong weather, with no script left to rebuild it. | Training reads the raw production data directly; the row set is unchanged. |
| Stale history | Rice in Cuttack was last reported as "Kharif" in 2003-04, so a forecast would rest on 20-year-old data. | Forecasts need a record from 2014 onward, and the app suggests seasons that have one. |

### Results

Trained on seasons before 2016 and tested on 2016 onward (7,841 training rows, 1,768 test rows). The baseline is the mean of the previous three seasons for the same district, crop and season.

| | R² | MAE (t/ha) | Median error |
| --- | --- | --- | --- |
| Model, all crops | 0.908 | 0.892 | 20.7% |
| Baseline, all crops | 0.907 | 0.891 | 19.5% |
| Model, excluding sugarcane | 0.724 | 0.294 | 20.9% |
| Baseline, excluding sugarcane | 0.753 | 0.271 | 19.6% |

The feature set was chosen by comparing a few options on this same test period, so the model's scores may be slightly optimistic. That only strengthens the conclusion below.

**The model does not beat the baseline.** Correctly aligned weather did not change that. Season-level weather averaged over a whole district seems to add little beyond a district's recent yields.

The model stays in the app because it lets users try different weather values, and the baseline is shown beside each forecast so the comparison stays visible. Field-level data, or weather at finer time scales, would be the next thing to try.

## Known limitations

- Rating bands and doses come from published sources, but no agronomist has reviewed them.
- Forecasts are district averages, not predictions for one field.
- The yield data ends in 2019-20.
- The Hindi and Odia text has not been reviewed by a native-speaking agricultural expert.
