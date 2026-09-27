# Lebanon Tourism Explorer (MSBA 325)

An interactive Streamlit page built on the 2023 town-level tourism dataset for Lebanon
(Impact Open Data, via linked.aub.edu.lb). It is the same dataset used in my Plotly assignment.

**Live app:** https://lebanon-tourism-app-xi257e2tgstpxxgg97wftz.streamlit.app/

## What it shows
- **Amenity mix** (stacked bar): hotels, restaurants, cafes and guest houses, drilling down
  from governorates → districts → individual towns.
- **Tourism Index vs. attraction potential** (stacked bar): how many towns reach each index
  level, and how many towns with attraction potential are still under-served.
- **Potential vs. readiness** (bubble chart): districts with lots of attractions but few amenities.
- A town lookup that shows any town's amenities and score.

## Linked interactions
1. **Governorate selectbox**: sets the region.
2. **District multiselect**: its options depend on the chosen governorate. Keeping one district
   switches the amenity chart to town level.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Files
- `app.py`: the Streamlit app
- `DATASET_VISO.csv`: the dataset
- `.streamlit/config.toml`: colour theme (same palette as my Plotly deck)
