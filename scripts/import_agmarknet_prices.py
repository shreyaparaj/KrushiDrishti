import argparse
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "agmarknet_price_history.csv"


def pick_first_existing_column(frame, candidates):
    for candidate in candidates:
        if candidate in frame.columns:
            return candidate
    return None


def normalize_agmarknet_export(frame):
    region_col = pick_first_existing_column(
        frame,
        ["District Name", "District", "district", "Region", "region"],
    )
    crop_col = pick_first_existing_column(
        frame,
        ["Commodity", "commodity", "Crop", "crop"],
    )
    date_col = pick_first_existing_column(
        frame,
        ["Arrival_Date", "Arrival Date", "Date", "date"],
    )
    modal_col = pick_first_existing_column(
        frame,
        ["Modal Price", "Modal_Price", "modal_price", "Price", "price"],
    )
    min_col = pick_first_existing_column(frame, ["Min Price", "Min_Price", "min_price"])
    max_col = pick_first_existing_column(frame, ["Max Price", "Max_Price", "max_price"])
    state_col = pick_first_existing_column(frame, ["State", "State Name", "state"])
    market_col = pick_first_existing_column(frame, ["Market", "Market Name", "market"])

    required = {
        "region": region_col,
        "crop": crop_col,
        "date": date_col,
        "price": modal_col,
    }
    missing = [label for label, source in required.items() if source is None]
    if missing:
        raise ValueError(f"Agmarknet file is missing required columns: {', '.join(missing)}")

    normalized = pd.DataFrame(
        {
            "State": frame[state_col].astype(str).str.strip() if state_col else "",
            "Market": frame[market_col].astype(str).str.strip() if market_col else "",
            "Region": frame[region_col].astype(str).str.strip(),
            "Crop": frame[crop_col].astype(str).str.strip(),
            "Date": pd.to_datetime(frame[date_col], errors="coerce", dayfirst=True),
            "Price": pd.to_numeric(frame[modal_col], errors="coerce"),
            "Min_Price": pd.to_numeric(frame[min_col], errors="coerce") if min_col else pd.NA,
            "Max_Price": pd.to_numeric(frame[max_col], errors="coerce") if max_col else pd.NA,
            "Cultivation_Percentage": pd.NA,
            "Rainfall": pd.NA,
            "Temperature": pd.NA,
            "Price_Risk": pd.NA,
        }
    )

    normalized = normalized.dropna(subset=["Region", "Crop", "Date", "Price"]).copy()
    normalized["Date"] = normalized["Date"].dt.strftime("%Y-%m-%d")
    return normalized.sort_values(["Region", "Crop", "Date"]).reset_index(drop=True)


def main():
    parser = argparse.ArgumentParser(
        description="Convert an Agmarknet CSV export into the normalized historical price dataset used by the ANN price predictor.",
    )
    parser.add_argument("input_csv", help="Path to the raw Agmarknet CSV export.")
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help=f"Output CSV path. Default: {DEFAULT_OUTPUT}",
    )
    args = parser.parse_args()

    input_path = Path(args.input_csv)
    output_path = Path(args.output)

    frame = pd.read_csv(input_path)
    normalized = normalize_agmarknet_export(frame)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    normalized.to_csv(output_path, index=False)

    print(f"Imported {len(normalized)} rows to {output_path}")


if __name__ == "__main__":
    main()
