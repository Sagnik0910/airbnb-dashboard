from flask import Flask, render_template, jsonify
import pandas as pd
import os

app = Flask(__name__)

DATA_FILE = "airbnb_cleaned.csv"


def find_existing_column(df, possible_names):
    """
    Return the first matching column from the dataframe
    based on a list of possible column names.
    """
    df_cols_lower = {col.lower().strip(): col for col in df.columns}

    for name in possible_names:
        key = name.lower().strip()
        if key in df_cols_lower:
            return df_cols_lower[key]

    return None


def clean_dataset():
    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError(f"{DATA_FILE} not found in project folder.")

    df = pd.read_csv(DATA_FILE)

    # Detect likely column names
    city_col = find_existing_column(df, ["City", "city"])
    room_col = find_existing_column(df, ["Room Type", "room type", "Room_Type", "room_type"])
    price_col = find_existing_column(df, ["Price", "price"])
    rating_col = find_existing_column(df, ["Rating", "rating", "Review Scores Rating", "review scores rating"])
    lat_col = find_existing_column(df, ["lat", "latitude", "Latitude", "LAT"])
    lng_col = find_existing_column(df, ["lng", "lon", "long", "longitude", "Longitude", "LNG"])

    # Standardize required columns
    if city_col is None:
        df["City"] = "Unknown"
    else:
        df["City"] = df[city_col].astype(str).fillna("Unknown").str.strip()

    if room_col is None:
        df["Room Type"] = "Unknown"
    else:
        df["Room Type"] = df[room_col].astype(str).fillna("Unknown").str.strip()

    if price_col is None:
        df["Price"] = 0
    else:
        df["Price"] = (
            df[price_col]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.replace("₹", "", regex=False)
            .str.replace("$", "", regex=False)
            .str.strip()
        )
        df["Price"] = pd.to_numeric(df["Price"], errors="coerce")

    if rating_col is None:
        df["Rating"] = None
    else:
        df["Rating"] = pd.to_numeric(df[rating_col], errors="coerce")

    if lat_col is None:
        df["lat"] = None
    else:
        df["lat"] = pd.to_numeric(df[lat_col], errors="coerce")

    if lng_col is None:
        df["lng"] = None
    else:
        df["lng"] = pd.to_numeric(df[lng_col], errors="coerce")

    # Remove rows where essential fields are missing
    df = df.dropna(subset=["Price", "Rating"])
    df = df[df["Price"] > 0]

    # Optional: keep ratings in sensible range
    df = df[(df["Rating"] >= 0) & (df["Rating"] <= 5)]

    # Reset index
    df = df.reset_index(drop=True)

    # Keep only columns needed by frontend
    final_df = df[["City", "Room Type", "Price", "Rating", "lat", "lng"]].copy()

    return final_df


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/data")
def api_data():
    try:
        df = clean_dataset()

        records = df.to_dict(orient="records")
        return jsonify(records)

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(debug=True)