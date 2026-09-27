"""
MSBA 325 - Streamlit activity
Lebanon tourism: where are the amenities, and which towns are being left behind?

Same dataset and colours as my Plotly deck (TourismPlotly_HanaWehbe.pptx).

Linked filters:
    1. Governorate (selectbox)  -> decides which districts you can pick
    2. Districts (multiselect)  -> options come from (1); picking one district
                                   switches the amenity chart from districts to towns
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Lebanon Tourism Explorer", layout="wide")

# ---------------------------------------------------------------
# Colours from the PowerPoint deck (Ocean palette)
# ---------------------------------------------------------------
MIDNIGHT = "#21295C"
DEEP_BLUE = "#065A82"
TEAL = "#1C7293"
SEAFOAM = "#5FBDB0"
SAND = "#E8DDB5"
PANEL = "#DCE6EE"
PANEL_LIGHT = "#E9EDF7"
GREY_TEXT = "#555555"
MUTED = "#C5CFDA"

# One font for the whole page: Carlito is the free web version of Calibri (the deck's font),
# so it looks the same on any computer
FONT_FAMILY = "Carlito, Calibri, sans-serif"
FONT = dict(family=FONT_FAMILY, size=15, color="#2B2B2B")

AMENITIES = {
    "Hotels": "Total number of hotels",
    "Restaurants": "Total number of restaurants",
    "Cafes": "Total number of cafes",
    "Guest houses": "Total number of guest houses",
}
AMENITY_COLORS = {"Hotels": MIDNIGHT, "Restaurants": TEAL, "Cafes": SEAFOAM, "Guest houses": SAND}

ATTRACTION_COL = "Existence of touristic attractions prone to be exploited and developed - exists"
INITIATIVE_COL = "Existence of initiatives and projects in the past five years to improve the tourism sector - exists"
HAS_ATTR, NO_ATTR = "Has attraction potential", "No attraction noted"

# Index = 3 per hotel/restaurant/cafe present + 1 for a guest house, so these bins are
# "how many of the three main kinds of place the town has"
TIERS = ["None of them", "One of the three", "Two of the three", "All three"]
TIER_BINS = [-1, 1, 4, 7, 10]
TIER_COLORS = dict(zip(TIERS, [SAND, SEAFOAM, TEAL, MIDNIGHT]))

DISTRICT_TO_GOV = {
    "Tripoli": "North", "Zgharta": "North", "Batroun": "North", "Bsharri": "North",
    "Miniyeh–Danniyeh": "North",
    "Matn": "Mount Lebanon", "Byblos": "Mount Lebanon", "Aley": "Mount Lebanon",
    "Keserwan": "Mount Lebanon", "Baabda": "Mount Lebanon",
    "Tyre": "South", "Sidon": "South",
    "Bint Jbeil": "Nabatieh", "Marjeyoun": "Nabatieh", "Hasbaya": "Nabatieh",
    "Zahlé": "Beqaa", "Western Beqaa": "Beqaa",
    "Hermel": "Baalbek-Hermel",
}
NOT_RECORDED = "District not recorded"
ALL = "All Lebanon"

# ---------------------------------------------------------------
# Page styling (banner, kicker labels and "key insight" cards like the slides)
# ---------------------------------------------------------------
st.markdown(
    f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Carlito:ital,wght@0,400;0,700;1,400;1,700&display=swap');
  /* everything in Carlito, including chart text; only the little icon glyphs keep their own font */
  .stApp, .stApp *:not([data-testid="stIconMaterial"]) {{ font-family: {FONT_FAMILY} !important; }}
  .stApp {{ font-size: 1.05rem; }}
  .block-container {{ padding-top: 2rem; max-width: 1300px; }}
  .banner {{ background:{MIDNIGHT}; color:white; padding:28px 34px 24px; border-radius:6px; margin-bottom:18px; }}
  .banner h1 {{ color:white; font-size:2.3rem; margin:0 0 4px; line-height:1.15; }}
  .banner .accent {{ color:{SEAFOAM}; }}
  .banner p {{ color:#D6DCEB; margin:6px 0 0; font-size:0.98rem; }}
  .kicker {{ color:{TEAL}; font-size:0.78rem; font-weight:700; letter-spacing:0.12em; text-transform:uppercase; margin:6px 0 2px; }}
  .chart-title {{ color:{MIDNIGHT}; font-size:1.35rem; font-weight:700; margin:0 0 2px; line-height:1.25; }}
  .showing {{ color:{GREY_TEXT}; font-size:0.9rem; margin-bottom:4px; }}
  .card {{ background:{PANEL_LIGHT}; border-left:5px solid {SEAFOAM}; border-radius:4px; padding:14px 18px; margin:6px 0 14px; color:#2B2B2B; }}
  .card .label {{ color:{TEAL}; font-size:0.75rem; font-weight:700; letter-spacing:0.12em; margin-bottom:4px; }}
  .card b {{ color:{MIDNIGHT}; }}
  .kpi {{ background:{PANEL}; border-radius:6px; padding:14px 18px; height:100%; }}
  .kpi .v {{ color:{MIDNIGHT}; font-size:2rem; font-weight:700; line-height:1.1; }}
  .kpi .l {{ color:{GREY_TEXT}; font-size:0.85rem; margin-top:4px; }}
  .kpi.hot {{ background:{MIDNIGHT}; }}
  .kpi.hot .v {{ color:{SEAFOAM}; }}
  .kpi.hot .l {{ color:#D6DCEB; }}
  .town {{ background:white; border:1px solid {PANEL}; border-radius:6px; padding:14px 18px; }}
  .town h4 {{ color:{MIDNIGHT}; margin:0 0 2px; }}
  .pill {{ display:inline-block; padding:2px 10px; border-radius:12px; font-size:0.8rem; margin:4px 6px 0 0; }}
</style>
""",
    unsafe_allow_html=True,
)


def kicker(text):
    st.markdown(f'<div class="kicker">{text}</div>', unsafe_allow_html=True)


def chart_heading(kick, title, showing):
    st.markdown(
        f'<div class="kicker">{kick}</div><div class="chart-title">{title}</div>'
        f'<div class="showing">{showing}</div>',
        unsafe_allow_html=True,
    )


def insight(text, label="KEY INSIGHT"):
    st.markdown(f'<div class="card"><div class="label">{label}</div>{text}</div>', unsafe_allow_html=True)


def style(fig, height):
    fig.update_layout(
        template="plotly_white",
        font=FONT,
        height=height,
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title=""),
        hoverlabel=dict(bgcolor="white", font=dict(family=FONT_FAMILY, color=MIDNIGHT)),
    )
    return fig


# ---------------------------------------------------------------
# Data
# ---------------------------------------------------------------
def fix_mojibake(text):
    """Some names in the CSV were saved with broken encoding, e.g. 'ZahlÃ©' instead of 'Zahlé'."""
    for wrong_codec in ("latin-1", "cp1252"):
        try:
            return text.encode(wrong_codec).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
    return text


def split_area(ref_area):
    """refArea is sometimes a district and sometimes only a governorate, so map both."""
    slug = fix_mojibake(ref_area.rstrip("/").split("/")[-1])
    name = slug.replace(",_Lebanon", "").replace("_", " ")
    if name.endswith(" Governorate"):
        gov = name.removesuffix(" Governorate")
        return gov, ("Akkar" if gov == "Akkar" else NOT_RECORDED)  # Akkar has only one district
    district = name.removesuffix(" District")
    return DISTRICT_TO_GOV[district], district


@st.cache_data
def load_data(path="DATASET_VISO.csv"):
    df = pd.read_csv(path)
    df["Town"] = df["Town"].str.strip().apply(fix_mojibake)
    df[["Governorate", "District"]] = df["refArea"].apply(lambda a: pd.Series(split_area(a)))
    for label, col in AMENITIES.items():
        df[label] = df[col]
    df["Total amenities"] = df[list(AMENITIES)].sum(axis=1)
    df["Attraction"] = df[ATTRACTION_COL].map({1: HAS_ATTR, 0: NO_ATTR})
    df["Project"] = df[INITIATIVE_COL].map({1: "Yes", 0: "No"})
    df["Tier"] = pd.cut(df["Tourism Index"], TIER_BINS, labels=TIERS)
    # attraction, but no more than one of hotel / restaurant / cafe
    df["Under-served"] = (df[ATTRACTION_COL] == 1) & (df["Tourism Index"] <= 4)
    return df


df = load_data()

# ---------------------------------------------------------------
# Banner + context
# ---------------------------------------------------------------
st.markdown(
    f"""
<div class="banner">
  <h1>Lebanon Tourism Explorer</h1>
  <p style="font-size:1.25rem;color:{SEAFOAM};margin-top:2px">Lots of towns have something worth seeing. Far fewer have anywhere to eat or sleep.</p>
  <p>Hana Wehbe · MSBA 325 · {len(df):,} towns, 2023 survey from Impact Open Data (linked.aub.edu.lb)</p>
</div>
""",
    unsafe_allow_html=True,
)

intro, how = st.columns([3, 2], gap="large")
with intro:
    st.markdown(
        """
I used the same data as in my Plotly deck. It's a 2023 survey of Lebanese towns that counts
the hotels, restaurants, cafes and guest houses in each one. It also notes whether the town has
an attraction that could be developed (a site, a view, something people would come for), and
whether any tourism project happened there in the last five years.

In the deck I stayed at country level. This time I wanted names: **which towns have something
to offer visitors, but nowhere for them to eat, drink or stay?**

Start with all of Lebanon, then pick a governorate below and narrow it down to its districts.
        """
    )
with how:
    insight(
        "I assumed the Tourism Index counted places. It doesn't. It gives <b>3 points each for having "
        "a hotel, a restaurant and a cafe, and 1 for a guest house</b> (I checked this: it matches "
        "1,136 of the 1,137 towns). So it measures <i>variety</i>, not size. Haret Hreik has 72 restaurants "
        "and 90 cafes and still only gets a 6, because there's no hotel.",
        label="SOMETHING I DIDN'T EXPECT",
    )

# ---------------------------------------------------------------
# Linked filters
# ---------------------------------------------------------------
kicker("Where do you want to look?")
f1, f2 = st.columns([1, 2])

with f1:
    governorate = st.selectbox(
        "Governorate",
        [ALL] + sorted(df["Governorate"].unique()),
        help="Pick a governorate to unlock its districts.",
    )

scope = df if governorate == ALL else df[df["Governorate"] == governorate]
district_options = sorted(scope["District"].unique(), key=lambda d: (d == NOT_RECORDED, d))

with f2:
    if governorate == ALL:
        st.multiselect("Districts", [], placeholder="Pick a governorate first", disabled=True)
        districts = district_options
    else:
        # key includes the governorate so old districts don't carry over when you switch
        districts = st.multiselect(
            f"Districts in {governorate}",
            district_options,
            default=district_options,
            key=f"districts_{governorate}",
            help="Keep a few to compare them, or just one to see its towns.",
        )

if not districts:
    st.info("Pick at least one district.")
    st.stop()

view = scope[scope["District"].isin(districts)]

if governorate == ALL:
    level, level_name = "Governorate", "governorate"
elif len(districts) > 1:
    level, level_name = "District", "district"
else:
    level, level_name = "Town", "town"

if governorate == ALL:
    place = "all of Lebanon (Beirut isn't in the data)"
elif len(districts) == 1:
    place = f"{districts[0]}, {governorate}" if districts[0] != NOT_RECORDED else f"{governorate}, towns with no district recorded"
elif len(districts) == len(district_options):
    place = f"{governorate}, all districts"
else:
    place = f"{governorate}: {', '.join(districts)}"

# ---------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------
n = len(view)
zero = int((view["Tourism Index"] == 0).sum())
attr = view[view["Attraction"] == HAS_ATTR]
underserved = view[view["Under-served"]]

k = st.columns(4)
kpis = [
    (f"{n:,}", "towns in this selection", ""),
    (f"{zero / n:.0%}", "have no hotel, restaurant, cafe or guest house", ""),
    (f"{len(attr):,}", "have an attraction that could be developed", ""),
    (f"{len(underserved):,}", "of those have one or none of hotel, restaurant, cafe", "hot"),
]
for col, (v, label, cls) in zip(k, kpis):
    col.markdown(f'<div class="kpi {cls}"><div class="v">{v}</div><div class="l">{label}</div></div>',
                 unsafe_allow_html=True)

st.write("")

# ---------------------------------------------------------------
# Chart 1 - amenity mix, drilling down governorate -> district -> town
# ---------------------------------------------------------------
left, right = st.columns(2, gap="large")

with left:
    TOP_TOWNS = 15
    grouped = view.groupby(level)[list(AMENITIES)].sum()
    grouped["total"] = grouped.sum(axis=1)
    grouped = grouped[grouped["total"] > 0].sort_values("total", ascending=False)
    if level == "Town":
        grouped = grouped.head(TOP_TOWNS)
    long = grouped.drop(columns="total").reset_index().melt(id_vars=level, var_name="Amenity", value_name="Count")

    chart_heading(
        "Chart 1 · Stacked bar",
        "A few places have almost everything",
        f"You're looking at {place}, one bar per {level_name}"
        + (f" (the {len(grouped)} best-equipped)" if level == "Town" else ""),
    )

    if long.empty:
        st.info("None of the towns here report any amenities.")
    else:
        fig1 = px.bar(
            long, y=level, x="Count", color="Amenity", orientation="h",
            category_orders={level: list(grouped.index), "Amenity": list(AMENITIES)},
            color_discrete_map=AMENITY_COLORS,
            labels={"Count": "Number of places", level: ""},
        )
        fig1.update_traces(
            marker_line_width=1, marker_line_color="white",
            hovertemplate="<b>%{y}</b><br>%{fullData.name}: %{x:,}<extra></extra>",
        )
        # Total at the end of each bar; for regions also "per town", since big regions win on totals alone
        if level == "Town":
            end_labels = [f"  {int(t):,}" for t in grouped["total"]]
        else:
            towns_per = view.groupby(level).size().reindex(grouped.index)
            end_labels = [f"  <b>{int(t):,}</b>  ·  {t / c:.1f} per town" for t, c in zip(grouped["total"], towns_per)]
        fig1.add_trace(go.Scatter(
            x=grouped["total"], y=grouped.index, mode="text", text=end_labels,
            textposition="middle right", textfont=dict(color=GREY_TEXT, size=12),
            showlegend=False, hoverinfo="skip",
        ))
        style(fig1, max(360, 34 * len(grouped) + 110)).update_layout(
            barmode="stack", bargap=0.3,
            xaxis=dict(range=[0, grouped["total"].max() * (1.2 if level == "Town" else 1.45)],
                       gridcolor="#EEF1F6", zeroline=False),
            yaxis=dict(ticksuffix="  "),
        )
        st.plotly_chart(fig1, width="stretch", config={"displayModeBar": False})

    food = view["Restaurants"] + view["Cafes"]
    if food.sum() > 0:
        top_n = max(1, round(n * 0.10))
        share = food.nlargest(top_n).sum() / food.sum()
        leader = view.loc[view["Total amenities"].idxmax()]
        per_town_note = ""
        if level != "Town" and len(grouped) > 1:
            per_town = (grouped["total"] / view.groupby(level).size().reindex(grouped.index)).sort_values()
            if per_town.index[-1] != grouped.index[0]:
                per_town_note = (
                    f"<br><br>Careful with the long bars though. {grouped.index[0]} is on top mostly because it's "
                    f"big. Per town, <b>{per_town.index[-1]}</b> actually does better "
                    f"({per_town.iloc[-1]:.1f} places per town, against {per_town[grouped.index[0]]:.1f})."
                )
        insight(
            f"Just {top_n:,} towns out of {n:,} (the top 10%) have <b>{share:.0%} of all the restaurants "
            f"and cafes</b> here, and {zero / n:.0%} of towns have none of the four at all. "
            f"<b>{leader['Town']}</b> alone has {int(leader['Total amenities'])}."
            + per_town_note
        )

# ---------------------------------------------------------------
# Chart 2 - Tourism Index distribution, towns with vs. without attraction potential
# ---------------------------------------------------------------
with right:
    chart_heading(
        "Chart 2 · 100% stacked bar",
        "Having an attraction helps, but not enough",
        f"You're looking at {place}. Each bar is 100% of its group, so the two are easy to compare. "
        "Hover to see how many towns that is.",
    )

    dist = view.groupby(["Attraction", "Tier"], observed=False).size().reset_index(name="Towns")
    dist["Group size"] = dist.groupby("Attraction")["Towns"].transform("sum")
    dist = dist[dist["Group size"] > 0]
    dist["Share"] = dist["Towns"] / dist["Group size"]
    dist["Group"] = dist["Attraction"].map({HAS_ATTR: "With an attraction", NO_ATTR: "Without an attraction"})
    dist["Group"] = dist["Group"] + dist["Group size"].map(lambda g: f"<br><span style='font-size:11px'>{g:,} towns</span>")

    fig2 = px.bar(
        dist, x="Share", y="Group", color="Tier", orientation="h",
        category_orders={"Tier": TIERS, "Group": sorted(dist["Group"].unique())},  # "With" on top
        color_discrete_map=TIER_COLORS,
        custom_data=["Towns"],
        text=dist["Share"].map(lambda s: f"{s:.0%}" if s >= 0.06 else ""),
    )
    fig2.update_traces(
        marker_line_width=1.5, marker_line_color="white",
        textposition="inside", insidetextanchor="middle", textfont=dict(size=14),
        hovertemplate="<b>%{fullData.name}</b><br>%{x:.0%} of the group (%{customdata[0]:,} towns)<extra></extra>",
    )
    for tier in TIERS[:2]:  # dark text on the two light colours
        fig2.update_traces(selector=dict(name=tier), textfont_color=MIDNIGHT)
    for tier in TIERS[2:]:
        fig2.update_traces(selector=dict(name=tier), textfont_color="white")
    style(fig2, 330).update_layout(
        barmode="stack", bargap=0.35,
        xaxis=dict(tickformat=".0%", range=[0, 1], title="", showgrid=False),
        yaxis=dict(title="", ticksuffix="  "),
        legend=dict(title="Has a hotel, restaurant or cafe?", title_side="top"),
        margin=dict(l=10, r=10, t=60, b=10),
    )
    st.plotly_chart(fig2, width="stretch", config={"displayModeBar": False})

    if len(attr):
        no_project = int((underserved["Project"] == "No").sum())
        other = view[view["Attraction"] == NO_ATTR]
        full_attr = (attr["Tier"] == TIERS[-1]).mean()
        full_other = (other["Tier"] == TIERS[-1]).mean() if len(other) else 0
        insight(
            f"Towns with an attraction are more likely to have all three ({full_attr:.0%} against "
            f"{full_other:.0%}), which makes sense. What surprised me is the other end: "
            f"<b>{len(underserved)} of the {len(attr)}</b> towns with an attraction "
            f"({len(underserved) / len(attr):.0%}) have one of the three or nothing, and <b>{no_project}</b> "
            "of those haven't had a single tourism project in five years. That's where I'd start."
        )
    else:
        insight("None of the towns here have an attraction noted in the survey.")

# ---------------------------------------------------------------
# Chart 3 - potential vs. readiness per district
# ---------------------------------------------------------------
st.write("")
dist_scope = df if governorate == ALL else scope
d = (
    dist_scope.groupby(["Governorate", "District"])
    .agg(Towns=("Town", "size"),
         Potential=(ATTRACTION_COL, "mean"),
         Index=("Tourism Index", "mean"),
         Underserved=("Under-served", "sum"))
    .reset_index()
)
d["Label"] = d.apply(lambda r: f"{r['Governorate']} (no district)" if r["District"] == NOT_RECORDED else r["District"], axis=1)
d["Selected"] = d["District"].isin(districts)
x_ref = df[ATTRACTION_COL].mean()
y_ref = df["Tourism Index"].mean()
gap = d[(d["Potential"] > x_ref) & (d["Index"] < y_ref)].sort_values("Potential", ascending=False)

chart_heading(
    "Chart 3 · Bubble chart",
    "Which districts have the potential but aren't ready for visitors?",
    ("Every district in Lebanon" if governorate == ALL else f"The districts of {governorate}. The ones you picked are dark")
    + ". Bigger bubble = more towns. The dashed lines are the national averages.",
)

fig3 = go.Figure()
for sel, color, name in [(False, MUTED, "Not selected"), (True, TEAL, "In your selection")]:
    part = d[d["Selected"] == sel]
    if part.empty:
        continue
    fig3.add_trace(go.Scatter(
        x=part["Potential"], y=part["Index"], mode="markers+text", name=name,
        text=part["Label"], textposition="top center",
        textfont=dict(size=11, color=MIDNIGHT if sel else GREY_TEXT),
        marker=dict(size=part["Towns"], sizemode="area", sizeref=2 * d["Towns"].max() / 55 ** 2, sizemin=6,
                    color=color, line=dict(color="white", width=1.5), opacity=0.9),
        customdata=part[["Towns", "Underserved"]],
        hovertemplate="<b>%{text}</b><br>%{x:.0%} of towns have an attraction<br>Average index %{y:.1f}"
                      "<br>%{customdata[0]} towns, %{customdata[1]} under-served<extra></extra>",
    ))
fig3.add_vline(x=x_ref, line_dash="dash", line_color=MUTED)
fig3.add_hline(y=y_ref, line_dash="dash", line_color=MUTED)
fig3.add_annotation(xref="paper", yref="paper", x=0.99, y=0.02, xanchor="right", yanchor="bottom", showarrow=False,
                    text="more potential, fewer amenities →", font=dict(color=TEAL, size=12))
style(fig3, 480).update_layout(
    showlegend=governorate != ALL,
    xaxis=dict(title="Share of towns with an attraction that could be developed", tickformat=".0%"),
    yaxis=dict(title="Average Tourism Index"),
)

c3, c3txt = st.columns([3, 1.3], gap="large")
with c3:
    st.plotly_chart(fig3, width="stretch")
with c3txt:
    if len(gap):
        bold = [f"<b>{x}</b>" for x in gap["Label"].head(4)]
        names = bold[0] if len(bold) == 1 else ", ".join(bold[:-1]) + " and " + bold[-1]
        insight(
            f"If I had a tourism budget, I'd spend it in the bottom-right corner. {names} "
            f"{'has' if len(gap) == 1 else 'have'} more attractions than average but fewer places for visitors."
            + ("<br><br>Byblos surprised me the most. Jbeil is one of the best-known historic towns in the "
               "country, yet the district as a whole only averages 2.2." if "Byblos" in set(gap["Label"]) else ""),
            label="HOW I READ THIS",
        )
    else:
        insight("None of these districts land in the bottom-right corner, so none of them stand out as "
                "high potential but low readiness.", label="HOW I READ THIS")

# ---------------------------------------------------------------
# Town lookup
# ---------------------------------------------------------------
st.write("")
t1, _ = st.columns([1, 1], gap="large")

with t1:
    kicker("Curious about a specific town?")
    towns = sorted(view["Town"])
    best = view.loc[view["Total amenities"].idxmax(), "Town"]
    # key per selection so it re-opens on the best-equipped town whenever the filters change
    town = st.selectbox("Town", towns, index=towns.index(best), placeholder="Type a town name",
                        label_visibility="collapsed", key=f"town_{governorate}_{'|'.join(districts)}")
    if town:
        r = view[view["Town"] == town].iloc[0]
        pills = "".join(
            f'<span class="pill" style="background:{AMENITY_COLORS[a]};color:{"white" if a != "Guest houses" else MIDNIGHT}">'
            f"{a}: {int(r[a])}</span>"
            for a in AMENITIES
        )
        st.markdown(
            f'<div class="town"><h4>{town}</h4>'
            f'<div class="showing">{r["District"]}, {r["Governorate"]}</div>'
            f'<div style="font-size:1.6rem;font-weight:700;color:{MIDNIGHT}">Tourism Index {int(r["Tourism Index"])} / 10</div>'
            f"{pills}"
            f'<div style="margin-top:8px">Attraction potential: <b>{"yes" if r["Attraction"] == HAS_ATTR else "no"}</b>'
            f' · Tourism project in last 5 years: <b>{r["Project"].lower()}</b></div></div>',
            unsafe_allow_html=True,
        )
    st.caption("It starts on the best-equipped town in your selection. Type a name to check any other one.")

# ---------------------------------------------------------------
# Notes + design justification
# ---------------------------------------------------------------
st.divider()
with st.expander("A few things to know about the data"):
    st.markdown(
        f"""
- Beirut isn't in the dataset, so "All Lebanon" here really means everywhere except the capital.
- Some towns are linked to a district, but others only to a governorate. I didn't want to guess
  where they belong, so they show up as **"{NOT_RECORDED}"**. (Akkar only has one district, so
  its towns are simply Akkar.)
- Some names came out garbled in the file, like "ZahlÃ©" instead of "Zahlé". I fixed them when loading.
- "Under-served" is my own word for a town that has an attraction but at most one of hotel,
  restaurant and cafe. In index terms, that's a score of 4 or less.
- A 0 means the survey found nothing. A small village might still have a café nobody recorded.
        """
    )

kicker("Why I built the filters this way")
j1, j2 = st.columns(2, gap="large")
with j1:
    with st.expander("Filter 1: the governorate dropdown", expanded=True):
        st.markdown(
            """
**What it helps you answer.** Which region should I look at, and how does it compare with the
rest of the country? Governorates are how people usually think about Lebanon, and it's the
level ministries and investors plan at, so it felt like the natural place to start.

**Why a dropdown.** You only look at one region at a time, and there are only eight options.
At first I used a multiselect here too, but once you could pick several governorates *and*
their districts, the district list got long and confusing. I also tried radio buttons, but
eight of them took up half the screen.

**Course idea: overview first, then zoom (giving context).** The page opens on the whole
country, so you see the big picture first (43% of towns have nothing at all) before you zoom
in. Even after you pick a region, the bubble chart still shows every other district in grey,
so you never lose track of how your region compares.
            """
        )
with j2:
    with st.expander("Filter 2: the district list (it depends on filter 1)", expanded=True):
        st.markdown(
            """
**What it helps you answer.** Inside this region, which districts, and eventually which
towns, have attractions but nothing for visitors? This is the step that takes you from a
pattern to actual names: keep just one district and Chart 1 switches to its towns.

**How it's linked.** The list only shows districts from the governorate you picked. It's
greyed out on "All Lebanon" and resets when you change governorate. How many you keep also
changes Chart 1: several districts give one bar each, and a single district shows its towns.
So you go country, then governorate, then district, then town.

**Why a multiselect.** I wanted you to be able to compare two or three neighbouring
districts side by side, and a second dropdown only allows one at a time. Checkboxes would
have been a different length for every governorate, so the page would keep jumping around.

**Course idea: reducing clutter and focusing attention.** 1,137 towns in one chart would be
impossible to read. Showing one level at a time keeps Chart 1 to fifteen bars at most. In
the bubble chart, the districts you picked are dark and the rest fade to grey, so your eye
goes straight to what you asked about.
            """
        )

st.caption("Data: Impact Open Data, Tourism-Lebanon-2023, via linked.aub.edu.lb · MSBA 325 · Hana Wehbe")
