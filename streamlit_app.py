import pandas as pd
import streamlit as st
import plotly.express as px


CSV_FILE = "cleaned_data.csv"
PLACES = "Beviljade platser totalt"

st.set_page_config(layout="wide")

st.title("YH-utbildningar")


# Load the data from a CSV file.
@st.cache_data
def load_data():
    data = pd.read_csv(CSV_FILE)
    return data

cleaned_dataset = load_data()


# Sidebar with filters
st.sidebar.header("Filter")
years = st.sidebar.multiselect("År", sorted(cleaned_dataset["År"].unique()))
if years:
    st.header(f"År {', '.join(map(str, years))}")
else:
    st.header("År 2023-2025")

counties = st.sidebar.multiselect("Län", sorted(cleaned_dataset["Län"].unique()))

filtered_by_year = cleaned_dataset
filtered_by_county = cleaned_dataset

# filtered = cleaned_dataset
if years:
    filtered_by_year = filtered_by_year[filtered_by_year["År"].isin(years)]
if counties:
    filtered_by_county = filtered_by_county[filtered_by_county["Län"].isin(counties)]

# Both filters applied, used for everything else
filtered = filtered_by_year
if counties:
    filtered = filtered[filtered["Län"].isin(counties)]

if filtered.empty:
    st.warning("Inga rader matchar filtren")
    st.stop()


# Applications per field of study
field_of_study_counts = filtered["Utbildningsområde"].value_counts().reset_index()
field_of_study_counts.columns = ["Utbildningsområde", "Antal"]

field_of_study_chart = px.bar(
    field_of_study_counts,
    x="Utbildningsområde",
    y="Antal",
    title="Ansökningar per utbildningsområde"
)
st.plotly_chart(field_of_study_chart)


# Applications per county
county_counts = filtered_by_year["Län"].value_counts().reset_index()
county_counts.columns = ["Län", "Antal"]

county_chart = px.bar(
    county_counts,
    x="Antal",
    y="Län",
    orientation="h",
    title="Ansökningar per län"
)
county_chart.update_yaxes(categoryorder="total ascending")
county_chart.update_layout(height=600)


# Applications per municipality
selected_amount = st.slider(
    "Antal kommuner",
    min_value=5,
    max_value=50,
    value=10
)

municipality_counts = filtered_by_year["Kommun"].value_counts().head(selected_amount).reset_index()
municipality_counts.columns = ["Kommun", "Antal"]

municipality_chart = px.bar(
    municipality_counts,
    x="Antal",
    y="Kommun",
    orientation="h",
    title=f"Topp {selected_amount} kommuner"
)
municipality_chart.update_yaxes(categoryorder="total ascending")
municipality_chart.update_layout(height=max(400, 28 * selected_amount + 100))

counties, municipalities = st.columns(2)
counties.plotly_chart(county_chart, width="stretch")
municipalities.plotly_chart(municipality_chart, width="stretch")


# Granted places per year
places_per_field = filtered.groupby("Utbildningsområde")[PLACES].sum().reset_index()

places_chart = px.bar(
    places_per_field,
    x=PLACES,
    y="Utbildningsområde",
    title="Beviljade platser per utbildningsområde"
)

places_chart.update_yaxes(categoryorder="total ascending")
st.plotly_chart(places_chart, width="stretch")


# Approval rate
approval_rate_counts = filtered[filtered["Beslut"].isin(["Beviljad", "Avslag"])]

if approval_rate_counts.empty:
    st.info("Inga beslut med Beviljad eller Avslag i urvalet")
else:
    approval_rate = (
        approval_rate_counts["Beslut"].eq("Beviljad").mean() * 100
    )

    total_applications = len(approval_rate_counts)

    approved_count = (approval_rate_counts["Beslut"] == "Beviljad").sum()
    rejected_count = (approval_rate_counts["Beslut"] == "Avslag").sum()

    column1, column2 = st.columns([1, 3])

    approval_rate_data = pd.DataFrame({
        "Beslut": ["Beviljad", "Avslag"],
        "Andel": [approval_rate, 100 - approval_rate]
    })

    approval_rate_chart = px.pie(
        approval_rate_data, names="Beslut", values="Andel", title="Andel beviljade och avslag"
    )

    column1.metric("Totalt antal ansökningar", f"{total_applications:,}".replace(",", " "))
    column1.metric("Beviljade", f"{approved_count:,}".replace(",", " "))
    column1.metric("Avslag", f"{rejected_count:,}".replace(",", " "))
    column1.metric("Andel beviljade", f"{approval_rate:.1f}%")

    column2.plotly_chart(approval_rate_chart)


# Applications per year, split by field of study
year_field_counts = (
    filtered_by_county.groupby(["År", "Utbildningsområde"])
    .size()
    .reset_index(name="Antal")
)


# The share of each field of study by year, in percent
year_field_counts["Andel (%)"] = (
    year_field_counts["Antal"]
    / year_field_counts.groupby("År")["Antal"].transform("sum")
    * 100
).round(1)


# Fields of study sorted from most to fewest applications
field_order = filtered_by_county["Utbildningsområde"].value_counts().index.tolist()

year_chart = px.bar(
    year_field_counts,
    x="År",
    y="Antal",
    color="Utbildningsområde",
    hover_data=["Andel (%)"],
    title="Ansökningar per år, fördelat på utbildningsområde",
    category_orders={"Utbildningsområde": field_order}
)

year_chart.update_xaxes(type="category")
st.plotly_chart(year_chart)


# A DataFrame with the most relevant columns
st.subheader("Data")
table = filtered[["År", "Utbildningsområde", "Utbildningsnamn", "Beslut", "Län", "Kommun", PLACES]]
st.dataframe(table.sort_values(PLACES, ascending=False), hide_index=True)
