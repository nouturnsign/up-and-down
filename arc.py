#!/usr/bin/env python3

import os
import spacy
import pandas as pd
import plotly.graph_objects as go
from concurrent.futures import ThreadPoolExecutor, as_completed
from transformers import pipeline
from scipy.signal import savgol_filter
from tqdm import tqdm


# ==========================================
# STEP 1: INGESTION & STRUCTURING (spaCy)
# ==========================================
def parse_sentences(filepath):
    print(f"Loading text from {filepath}...")
    with open(filepath, "r", encoding="utf-8") as f:
        raw_text = f.read()

    # Load spaCy's small English model
    print("Parsing text into sentences with spaCy...")
    nlp = spacy.load("en_core_web_sm")

    # Increase max length just in case the file is large
    nlp.max_length = 2000000
    doc = nlp(raw_text)

    # Filter out empty lines, stage directions that are too short, or artifacts
    sentences = []
    for sent in doc.sents:
        clean_text = sent.text.strip().replace("\n", " ")
        # Only keep sentences with more than 3 words to avoid noisy 1-word shouts
        if len(clean_text.split()) > 3:
            sentences.append(clean_text)

    print(f"Extracted {len(sentences)} valid sentences.")
    return sentences


# ==========================================
# STEP 2: CONTEXTUAL SCORING (Transformers)
# ==========================================
def score_sentiment(sentences):
    print("Loading Hugging Face sentiment model (DistilBERT)...")
    # Using a fast, standard sentiment model. Truncation ensures long sentences don't crash it.
    sentiment_model = pipeline(
        "sentiment-analysis",
        model="distilbert-base-uncased-finetuned-sst-2-english",
        truncation=True,
    )

    print("Scoring sentences (this may take a minute or two on CPU)...")
    scores = []

    # We use tqdm to show a progress bar
    for sentence in tqdm(sentences):
        result = sentiment_model(sentence)[0]
        label = result["label"]
        confidence = result["score"]

        # Convert to bipolar scale: POSITIVE = +score, NEGATIVE = -score
        if label == "POSITIVE":
            scores.append(confidence)
        else:
            scores.append(-confidence)

    return scores


# ==========================================
# STEP 3: AGGREGATION & SMOOTHING (pandas/SciPy)
# ==========================================
def process_data(sentences, scores):
    print("Structuring and smoothing data...")
    df = pd.DataFrame(
        {
            "Sentence_Index": range(len(sentences)),
            "Text": sentences,
            "Raw_Score": scores,
        }
    )

    # Strategy A: Rolling Averages (Pandas)
    # Center=True ensures the line aligns with the text, preventing "phase lag"
    df["Rolling_20"] = df["Raw_Score"].rolling(window=20, center=True).mean()
    df["Rolling_100"] = df["Raw_Score"].rolling(window=100, center=True).mean()

    # Strategy B: Savitzky-Golay Filter (SciPy)
    # Fits a polynomial curve to windows of data.
    # Window length must be odd. Polyorder defines the curve flexibility.
    df["SavGol_51"] = savgol_filter(df["Raw_Score"], window_length=51, polyorder=3)
    df["SavGol_201"] = savgol_filter(df["Raw_Score"], window_length=201, polyorder=3)

    return df


# ==========================================
# STEP 4: INTERACTIVE VISUALIZATION (Plotly)
# ==========================================
def plot_interactive_arc(df, output_file="narrative_arc.html", title="Narrative Arc"):
    print("Generating interactive visualization...")

    fig = go.Figure()

    # 1. The Background: Raw Jagged Data
    # Plotted as faint scatter dots. We put text in the hoverinfo!
    fig.add_trace(
        go.Scatter(
            x=df["Sentence_Index"],
            y=df["Raw_Score"],
            mode="markers",
            name="Raw Sentence (Scatter)",
            marker=dict(size=4, color="gray", opacity=0.2),
            text=df["Text"],  # Shows the actual Shakespeare line on hover
            hoverinfo="text+y",
        )
    )

    # 2. The Trendlines (We load them all, but manage visibility with buttons later)
    # Rolling 20 (Scene level)
    fig.add_trace(
        go.Scatter(
            x=df["Sentence_Index"],
            y=df["Rolling_20"],
            mode="lines",
            name="Rolling Average (20)",
            line=dict(color="blue", width=2),
            visible=False,
        )
    )

    # Rolling 100 (Act level)
    fig.add_trace(
        go.Scatter(
            x=df["Sentence_Index"],
            y=df["Rolling_100"],
            mode="lines",
            name="Rolling Average (100)",
            line=dict(color="purple", width=3),
            visible=True,
        )
    )

    # Savitzky-Golay 51 (Smooth Scene level)
    fig.add_trace(
        go.Scatter(
            x=df["Sentence_Index"],
            y=df["SavGol_51"],
            mode="lines",
            name="SciPy SavGol (51)",
            line=dict(color="green", width=2),
            visible=False,
        )
    )

    # Savitzky-Golay 201 (Macro Narrative Arc)
    fig.add_trace(
        go.Scatter(
            x=df["Sentence_Index"],
            y=df["SavGol_201"],
            mode="lines",
            name="SciPy SavGol (201)",
            line=dict(color="red", width=4),
            visible=False,
        )
    )

    # Add a baseline at 0 (Neutral sentiment)
    fig.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)

    # 3. Interactive Dropdown Menus
    # This toggles which trendline is visible on top of the raw scatter
    fig.update_layout(
        updatemenus=[
            dict(
                active=1,  # Default to the second button (Rolling 100)
                buttons=list(
                    [
                        dict(
                            label="1. None (Raw Volatility)",
                            method="update",
                            args=[
                                {"visible": [True, False, False, False, False]},
                                {"title": f"{title}: Raw Volatility Only"},
                            ],
                        ),
                        dict(
                            label="2. Rolling Average (100 - Act Level)",
                            method="update",
                            args=[
                                {"visible": [True, False, True, False, False]},
                                {"title": f"{title}: Rolling Average (Window=100)"},
                            ],
                        ),
                        dict(
                            label="3. Rolling Average (20 - Scene Level)",
                            method="update",
                            args=[
                                {"visible": [True, True, False, False, False]},
                                {"title": f"{title}: Rolling Average (Window=20)"},
                            ],
                        ),
                        dict(
                            label="4. SciPy SavGol (201 - Macro Arc)",
                            method="update",
                            args=[
                                {"visible": [True, False, False, False, True]},
                                {"title": f"{title}: Savitzky-Golay Filter (Macro)"},
                            ],
                        ),
                        dict(
                            label="5. Compare All Trends",
                            method="update",
                            args=[
                                {"visible": [True, True, True, True, True]},
                                {"title": f"{title}: All Smoothing Strategies"},
                            ],
                        ),
                    ]
                ),
                direction="down",
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.1,
                xanchor="left",
                y=1.15,
                yanchor="top",
            ),
        ]
    )

    # Formatting the chart
    fig.update_layout(
        title=title,
        xaxis_title="Narrative Time (Sentence Index)",
        yaxis_title="Sentiment Valence (-1.0 Tragic to +1.0 Comedic)",
        yaxis=dict(range=[-1.1, 1.1]),
        template="plotly_white",
        hovermode="x unified",
    )

    # Save to a self-contained HTML file
    fig.write_html(output_file)
    print(f"\nSuccess! Interactive graph saved to {output_file}.")
    print("Open this file in any web browser to view your data.")


def process_text_file(text_file, output_dir):
    print(f"\n{'=' * 50}\nProcessing: {text_file}\n{'=' * 50}")

    if not os.path.exists(text_file):
        return f"ERROR: Cannot find '{text_file}'. Skipping..."

    base_name = os.path.splitext(os.path.basename(text_file))[0]
    output_file = os.path.join(output_dir, f"{base_name}_arc.html")
    title_name = base_name.replace("_", " ").title()

    sentences = parse_sentences(text_file)
    if not sentences:
        return f"WARNING: No valid sentences found in '{text_file}'. Skipping..."

    scores = score_sentiment(sentences)
    df = process_data(sentences, scores)

    plot_interactive_arc(
        df,
        output_file=output_file,
        title=f"{title_name}: The Shape of Subversion",
    )

    return f"Finished processing '{text_file}'"

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(
        description="Process text files to generate narrative sentiment arcs."
    )
    parser.add_argument(
        "text_files", nargs="+", help="One or more text files to process"
    )
    parser.add_argument(
        "--output_dir", default="html", help="Directory to save the generated HTML arcs"
    )
    parser.add_argument(
        "--max-workers", type=int, default=5
    )
    args = parser.parse_args()

    # Ensure the output directory exists before processing
    os.makedirs(args.output_dir, exist_ok=True)

    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = [
            executor.submit(process_text_file, text_file, args.output_dir)
            for text_file in args.text_files
        ]

        for future in as_completed(futures):
            print(future.result())
