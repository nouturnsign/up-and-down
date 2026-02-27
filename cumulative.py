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
# STEP 3: AGGREGATION & ADDITIVE SMOOTHING
# ==========================================
def process_data(sentences, scores):
    print("Structuring and calculating cumulative data...")
    df = pd.DataFrame(
        {
            "Sentence_Index": range(len(sentences)),
            "Text": sentences,
            "Raw_Score": scores,
        }
    )

    # The Additive Magic: Calculate the running total of sentiment
    df["Cumulative_Score"] = df["Raw_Score"].cumsum()

    # Smooth the cumulative score to reveal the macro "Shape of the Story"
    # We use Savitzky-Golay on the cumulative line to get a beautiful, flowing curve
    df["Cumul_SavGol_51"] = savgol_filter(df["Cumulative_Score"], window_length=51, polyorder=3)
    df["Cumul_SavGol_201"] = savgol_filter(df["Cumulative_Score"], window_length=201, polyorder=3)
    
    # A rolling average of the cumulative score to represent Acts
    df["Cumul_Rolling_100"] = df["Cumulative_Score"].rolling(window=100, center=True).mean()

    return df


# ==========================================
# STEP 4: INTERACTIVE VISUALIZATION (Plotly)
# ==========================================
def plot_interactive_arc(df, output_file="additive_arc.html", title="Cumulative Narrative Arc"):
    print("Generating interactive cumulative visualization...")

    fig = go.Figure()

    # 1. The Background: Raw Cumulative Trajectory
    # Looks somewhat like a stock market chart, tracking the exact point-by-point fortune
    fig.add_trace(
        go.Scatter(
            x=df["Sentence_Index"],
            y=df["Cumulative_Score"],
            mode="lines",
            name="Raw Cumulative Trajectory",
            line=dict(color="gray", width=1, dash="dot"),
            opacity=0.5,
            text=df["Text"],  # Shows the actual Shakespeare line on hover
            hoverinfo="text+y",
            visible=True,
        )
    )

    # 2. Smooth Trendlines
    # Rolling 100 on Cumulative
    fig.add_trace(
        go.Scatter(
            x=df["Sentence_Index"],
            y=df["Cumul_Rolling_100"],
            mode="lines",
            name="Cumulative Rolling (100)",
            line=dict(color="purple", width=3),
            visible=False,
        )
    )

    # Savitzky-Golay 51 (Scene level flow)
    fig.add_trace(
        go.Scatter(
            x=df["Sentence_Index"],
            y=df["Cumul_SavGol_51"],
            mode="lines",
            name="SciPy SavGol (51)",
            line=dict(color="blue", width=2),
            visible=False,
        )
    )

    # Savitzky-Golay 201 (The Macro Vonnegut Arc)
    fig.add_trace(
        go.Scatter(
            x=df["Sentence_Index"],
            y=df["Cumul_SavGol_201"],
            mode="lines",
            name="SciPy SavGol (201 - Shape of Story)",
            line=dict(color="red", width=4),
            visible=True, # Default to showing this beautifully smooth macro line
        )
    )

    # Add a baseline at 0 (Starting point / Neutral Fortune)
    fig.add_hline(y=0, line_dash="solid", line_color="black", opacity=0.8)

    # 3. Interactive Dropdown Menus
    fig.update_layout(
        updatemenus=[
            dict(
                active=0,
                buttons=list(
                    [
                        dict(
                            label="1. Macro Story Shape (SavGol 201)",
                            method="update",
                            args=[
                                {"visible": [True, False, False, True]},
                                {"title": f"{title}: The Vonnegut Shape"},
                            ],
                        ),
                        dict(
                            label="2. Act-Level Trajectory (Rolling 100)",
                            method="update",
                            args=[
                                {"visible": [True, True, False, False]},
                                {"title": f"{title}: Act-Level Fortune"},
                            ],
                        ),
                        dict(
                            label="3. Scene-Level Flow (SavGol 51)",
                            method="update",
                            args=[
                                {"visible": [True, False, True, False]},
                                {"title": f"{title}: Scene-Level Fortune"},
                            ],
                        ),
                        dict(
                            label="4. Raw Cumulative Only",
                            method="update",
                            args=[
                                {"visible": [True, False, False, False]},
                                {"title": f"{title}: Raw Additive Walk"},
                            ],
                        ),
                        dict(
                            label="5. Compare All",
                            method="update",
                            args=[
                                {"visible": [True, True, True, True]},
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

    # Note: Y-axis is intentionally left un-ranged because cumulative scores 
    # will drift drastically high or low depending on the length and tone of the play.
    fig.update_layout(
        title=f"{title}: The Vonnegut Shape",
        xaxis_title="Narrative Time (Sentence Index)",
        yaxis_title="Net Cumulative Fortune (Emotional Bank Account)",
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
    output_file = os.path.join(output_dir, f"{base_name}_cumulative_arc.html")
    title_name = base_name.replace("_", " ").title()

    sentences = parse_sentences(text_file)
    if not sentences:
        return f"WARNING: No valid sentences found in '{text_file}'. Skipping..."

    scores = score_sentiment(sentences)
    df = process_data(sentences, scores)

    plot_interactive_arc(
        df,
        output_file=output_file,
        title=f"{title_name}",
    )

    return f"Finished processing '{text_file}'"

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(
        description="Process text files to generate cumulative (additive) sentiment arcs."
    )
    parser.add_argument(
        "text_files", nargs="+", help="One or more text files to process"
    )
    parser.add_argument(
        "--output_dir", default="html_cumulative", help="Directory to save the generated HTML arcs"
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
