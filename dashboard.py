import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import platform

# Import your batch processor
from etl.processor import process_all_runs

st.set_page_config(page_title="StS2 Run Analyzer", layout="wide")
st.title("Slay the Spire 2 Data Analysis")


def get_local_sts2_path():
    """Finds the local StS2 history folder across different OS and Steam IDs."""
    if platform.system() == "Windows":
        base_path = Path.home() / "AppData" / "Roaming" / "SlayTheSpire2" / "steam"
    elif platform.system() == "Darwin":  # macOS
        base_path = (
            Path.home() / "Library" / "Application Support" / "SlayTheSpire2" / "steam"
        )
    else:  # Linux
        base_path = Path.home() / ".config" / "SlayTheSpire2" / "steam"

    if base_path.exists():
        for item in base_path.iterdir():
            if item.is_dir():
                history_path = item / "profile1" / "saves" / "history"
                if history_path.exists():
                    return str(history_path)
    return None


@st.cache_data
def load_data(data_source="Sample Data"):
    if data_source == "Sample Data":
        # Load your pre-parsed data as the fallback
        try:
            return pd.read_json("data/sample_runs_dataset.json")
        except FileNotFoundError:
            return pd.DataFrame()

    elif data_source == "Auto-Detect Local Runs":
        local_path = get_local_sts2_path()

        if not local_path:
            st.error("Could not locate local Slay the Spire 2 save files.")
            return pd.DataFrame()

        # Run the ETL pipeline on the fly and save it to a temporary local file
        return process_all_runs(
            runs_dir=local_path, output_filepath="data/user_local_dataset.json"
        )

df = load_data()

# 3. Sidebar Interactive Filters
st.sidebar.header("Data Source")

# Let the user choose their data
data_choice = st.sidebar.radio(
    "Select Data to Analyze:", options=["Sample Data", "Auto-Detect Local Runs"]
)

# Use a Streamlit spinner while the ETL pipeline parses their local files
with st.spinner("Loading Run Data..."):
    df = load_data(data_choice)

if df.empty:
    st.warning(
        "No data found. Please ensure the dataset exists or local saves are present."
    )
    st.stop()  # Halts the rest of the script from crashing

st.sidebar.divider()
st.sidebar.header("Filters")

# Toggle for abandoned runs
include_abandoned = st.sidebar.checkbox("Include Abandoned Runs", value=False)

# Toggle for a10 only
toggle_a10 = st.sidebar.checkbox("Only Ascension 10 Runs", value = False)

metric_choice = st.sidebar.selectbox(
    "Select Metric to Visualize",
    options=["Win Rate (%)", "Games Played", "Average Floor Reached"],
)

# Apply filters
filtered_df = df.copy()

if not include_abandoned:
    filtered_df = filtered_df[filtered_df["abandonded"] == False]

if toggle_a10:
    filtered_df = filtered_df[filtered_df["ascension_level"] == 10]

if not filtered_df.empty:

    if metric_choice == "Win Rate (%)":
        plot_data = filtered_df.groupby("character_chosen", as_index=False)[
            "victory"
        ].mean()
        plot_data["value"] = (plot_data["victory"] * 100).round(1)
        y_label = "Win Rate (%)"
        text_format = "%{text}%"

    elif metric_choice == "Games Played":
        plot_data = filtered_df.groupby("character_chosen", as_index=False).size()
        plot_data.rename(columns={"size": "value"}, inplace=True)
        y_label = "Total Games Played"
        text_format = "%{text}"

    elif metric_choice == "Average Floor Reached":
        plot_data = filtered_df.groupby("character_chosen", as_index=False)[
            "floor_reached"
        ].mean()
        plot_data["value"] = plot_data["floor_reached"].round(1)
        y_label = "Average Floor"
        text_format = "%{text}"

    fig = px.bar(
        plot_data,
        x="character_chosen",
        y="value",
        title=f"{metric_choice} by Character",
        labels={"character_chosen": "Character", "value": y_label},
        text="value",
        color="character_chosen",
    )

    fig.update_traces(texttemplate=text_format, textposition="outside")

    if metric_choice == "Win Rate (%)":
        fig.update_yaxes(range=[0, 100])
    else:
        max_val = plot_data["value"].max()
        fig.update_yaxes(range=[0, max_val * 1.15])

    st.plotly_chart(fig, width='stretch')

else:
    st.warning("No runs match the selected filters.")

st.divider()  
st.subheader("Card Pick Analysis")

available_chars = filtered_df["character_chosen"].unique()

if len(available_chars) > 0:
    selected_char = st.selectbox("Select Character to Analyze", options=available_chars)
    char_df = filtered_df[filtered_df["character_chosen"] == selected_char]

    # 2. Unnest the card_choices array
    exploded_choices = char_df.explode("card_choices").dropna(subset=["card_choices"])

    if not exploded_choices.empty:
        def extract_picked(choice_dict: dict):
            if isinstance(choice_dict, dict) and choice_dict.get("picked"):
                return choice_dict.get("picked").get("name")
            return None

        def extract_ignored(choice_dict):
            if isinstance(choice_dict, dict):
                return [card.get("name") for card in choice_dict.get("not_picked", [])]
            return []

        picked_series = exploded_choices["card_choices"].apply(extract_picked).dropna()
        not_picked_series = exploded_choices["card_choices"].apply(extract_ignored).explode().dropna()

        picked_counts = picked_series.value_counts()
        ignored_counts = not_picked_series.value_counts()

        card_stats = pd.DataFrame({
            "Picked": picked_counts,
            "Ignored": ignored_counts
        }).fillna(0)

        card_stats["Seen"] = card_stats["Picked"] + card_stats["Ignored"]
        card_stats["Pick Rate (%)"] = ((card_stats["Picked"] / card_stats["Seen"]) * 100).round(1)

        card_stats["Picked"] = card_stats["Picked"].astype(int)
        card_stats["Ignored"] = card_stats["Ignored"].astype(int)
        card_stats["Seen"] = card_stats["Seen"].astype(int)

        card_stats.index.name = "Card"
        card_stats = card_stats.reset_index()

        # Filter out cards seen less than 2 times
        valid_stats = card_stats[card_stats["Seen"] >= 2]

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Highest Pick Rate")
            if not valid_stats.empty:
                # Sort by pick rate descending, tie-break by most times seen
                top_picked = valid_stats.sort_values(by=["Pick Rate (%)", "Seen"], ascending=[False, False])


                st.dataframe(top_picked[["Card", "Pick Rate (%)", "Seen", "Picked"]].head(8), hide_index=True)
            else:
                st.write("Not enough data to calculate reliable pick rates.")

        with col2:
            st.markdown("### Lowest Pick Rate")
            if not valid_stats.empty:
                # Sort by Pick Rate ascending
                top_ignored = valid_stats.sort_values(by=["Pick Rate (%)", "Seen"], ascending=[True, False])

                
                st.dataframe(top_ignored[["Card", "Pick Rate (%)", "Seen", "Picked"]].head(8), hide_index=True)
            else:
                st.write("Not enough data to calculate reliable pick rates.")
    else:
        st.info("No runs available to analyze card choices.")

else:
    st.info("No runs available to analyze card choices.")

st.divider()
st.subheader("Campfire Selection")

if "campfire_choices" in filtered_df.columns:
    exploded_campfires = filtered_df.explode("campfire_choices").dropna(
        subset=["campfire_choices"]
    )

    if not exploded_campfires.empty:
            def extract_campfire_action(choice):
                if isinstance(choice, dict):
                    return choice.get("picked", "UNKNOWN")
                return str(choice)
                
            exploded_campfires["Action"] = exploded_campfires["campfire_choices"].apply(extract_campfire_action)

        # 3. Count occurrences
            action_counts = exploded_campfires["Action"].value_counts().reset_index()
            action_counts.columns = ["Action", "Count"]
            
            # 4. Create dynamic columns based on how many unique actions exist
            cols = st.columns(len(action_counts))
            
            # 5. Populate each column with a clean metric UI
            for index, row in action_counts.iterrows():
                with cols[index]:
                    st.metric(label=row["Action"], value=row["Count"])
            
    else:
        st.write("No campfire choices recorded.")
else:
    st.info("Campfire choices data not found.")


st.divider()
st.subheader("Ancient Choice Analysis")

if "ancient_choices" in filtered_df.columns:
    exploded_ancients = filtered_df.explode("ancient_choices").dropna(
        subset=["ancient_choices"]
    )

    if not exploded_ancients.empty:
        # 1. Extract the name AND the floor
        def extract_ancient_name(choice):
            if isinstance(choice, dict):
                return choice.get(
                    "picked", choice.get("id", choice.get("name", str(choice)))
                )
            return str(choice)

        def extract_ancient_act(choice):
            if isinstance(choice, dict):
                return "Act " + str(choice.get("act", 0))
            return 0

        exploded_ancients["Choice_Name"] = exploded_ancients["ancient_choices"].apply(
            extract_ancient_name
        )
        exploded_ancients["Act"] = exploded_ancients["ancient_choices"].apply(
            extract_ancient_act
        )

        # 3. Generate a separate graph for each Act
        for act in ["Act 1", "Act 2", "Act 3"]:
            st.markdown(f"#### {act}")

            act_df = exploded_ancients[exploded_ancients["Act"] == act]

            if not act_df.empty:
                # -- THE FIX --
                # Hardcode the exact stacking order (Left = Bottom of bar, Right = Top of bar)
                # Ensure these strings match the exact character IDs in your JSON data
                char_order = [
                    "CHARACTER.IRONCLAD",
                    "CHARACTER.SILENT",
                    "CHARACTER.REGENT",
                    "CHARACTER.NECROBINDER",
                    "CHARACTER.DEFECT",
                ]

                # Group the data to get the counts per choice and character
                ancient_counts = (
                    act_df.groupby(["Choice_Name", "character_chosen"])
                    .size()
                    .reset_index(name="Count")
                )

                # Build the chart
                fig_ancient = px.bar(
                    ancient_counts,
                    x="Choice_Name",
                    y="Count",
                    color="character_chosen",
                    # Force Plotly to always use your specific character list
                    category_orders={"character_chosen": char_order},
                    labels={
                        "Choice_Name": "Ancient Choice",
                        "Count": "Total Picks",
                        "character_chosen": "Character",
                    },
                    text="Count",
                )

                # Stack bars and push the highest total columns to the left
                fig_ancient.update_layout(
                    xaxis={"categoryorder": "total descending"},
                    barmode="stack",
                    margin=dict(t=10),
                )
                fig_ancient.update_traces(textposition="inside")

                st.plotly_chart(fig_ancient, width="stretch")
            else:
                st.write(f"No ancient choices recorded for {act}.")
