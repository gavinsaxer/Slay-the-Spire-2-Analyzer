import json
import pandas as pd
from pathlib import Path
from rich import print

from etl.parser import parse_sts2_run


def process_all_runs(runs_dir: str, output_filepath: str) -> pd.DataFrame:
    """Parses all .run files in a directory and returns a Pandas DataFrame."""
    target_dir = Path(runs_dir)
    parsed_runs = []

    if not target_dir.is_dir():
        print(f"[bold red]Directory not found:[/] {target_dir.resolve()}")
        return pd.DataFrame()

    i=0
    for file_path in target_dir.glob("*.run"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_json = json.load(f)

            print("Processing run", i)
            i+=1
            run_obj = parse_sts2_run(raw_json)

            parsed_runs.append(run_obj.model_dump())

        except Exception as e:
            print(f"[yellow]Skipping {file_path.name}:[/] {e}")

    df = pd.DataFrame(parsed_runs)

    output_path = Path(output_filepath)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_json(output_path, orient="records", indent=2)

    print(
        f"[bold green]Success![/] Processed {len(parsed_runs)} runs. Saved to {output_filepath}"
    )
    return df


if __name__ == "__main__":
    sts2_history_path = r"C:\Users\gavin\AppData\Roaming\SlayTheSpire2\steam\76561198284172076\profile1\saves\history"

    df = process_all_runs(
        runs_dir=sts2_history_path, output_filepath="data/parsed_runs_dataset.json"
    )

    if not df.empty:
        print("\n[bold cyan]Initial Data Analysis:[/]")

        valid_runs = df[df["abandonded"] == False]

        win_rates = valid_runs.groupby("character_chosen")["victory"].mean() * 100
        print("\nWin Rate by Character (Legitimate Attempts):")
        print(win_rates)

        losses = valid_runs[valid_runs["victory"] == False]
        avg_loss_floor = losses.groupby("character_chosen")["floor_reached"].mean()
        print("\nAverage Floor Reached (True Losses):")
        print(avg_loss_floor)
