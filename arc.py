#!/usr/bin/env python3

import colorsys
import os
import spacy
import pandas as pd
import plotly.graph_objects as go
from concurrent.futures import ThreadPoolExecutor, as_completed
from transformers import pipeline
from scipy.signal import savgol_filter
from tqdm import tqdm


# ==========================================
# STEP 1 & 2: INGESTION & SCORING
# ==========================================
def parse_sentences(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        raw_text = f.read()

    nlp = spacy.load("en_core_web_sm")
    nlp.max_length = 2000000
    doc = nlp(raw_text)

    sentences = []
    for sent in doc.sents:
        clean_text = sent.text.strip().replace("\n", " ")
        if len(clean_text.split()) > 3:
            sentences.append(clean_text)
    return sentences

def score_sentiment(sentences):
    sentiment_model = pipeline(
        "sentiment-analysis",
        model="distilbert-base-uncased-finetuned-sst-2-english",
        truncation=True,
    )

    scores = []
    for sentence in tqdm(sentences, leave=False):
        result = sentiment_model(sentence)[0]
        confidence = result["score"]
        if result["label"] == "POSITIVE":
            scores.append(confidence)
        else:
            scores.append(-confidence)
    return scores

# ==========================================
# STEP 3: SMOOTHING & DATA PROCESSING
# ==========================================
def safe_savgol(data, window):
    """Safely applies a Savitzky-Golay filter, preventing crashes on short texts."""
    w = min(window, len(data) - (len(data) % 2 == 0))
    if w < 3:
        return data  # Too short to smooth meaningfully
    p = min(3, w - 1)
    return savgol_filter(data, window_length=w, polyorder=p)

def process_single_file(text_file, output_dir):
    print(f"Processing: {os.path.basename(text_file)}")
    
    base_name = os.path.splitext(os.path.basename(text_file))[0]
    title_name = base_name.replace("_", " ").title()
    sentences = parse_sentences(text_file)
    
    if not sentences:
        print(f"Skipping {title_name} (No sentences)")
        return None

    scores = score_sentiment(sentences)
    
    df = pd.DataFrame({
        "Sentence_Index": range(len(sentences)),
        "Text": sentences,
        "Raw_Score": scores,
    })

    # --- 1. Original Metrics (Raw Volatility) ---
    df["Rolling_20"] = df["Raw_Score"].rolling(window=20, center=True).mean()
    df["Rolling_100"] = df["Raw_Score"].rolling(window=100, center=True).mean()
    df["SavGol_51"] = safe_savgol(df["Raw_Score"], 51)
    df["SavGol_201"] = safe_savgol(df["Raw_Score"], 201)

    # --- 2. Additive Metrics (Cumulative Fortune) ---
    df["Cumulative_Score"] = df["Raw_Score"].cumsum()
    df["Cumul_SavGol_51"] = safe_savgol(df["Cumulative_Score"], 51)
    df["Cumul_SavGol_201"] = safe_savgol(df["Cumulative_Score"], 201)
    df["Cumul_Rolling_100"] = df["Cumulative_Score"].rolling(window=100, center=True).mean()
    
    # Alias the 201 window as the Macro Arc for the combined graph
    df["Macro_Arc"] = df["Cumul_SavGol_201"]
    
    # --- 3. Generate Both Graphs ---
    original_output = os.path.join(output_dir, f"{base_name}_original.html")
    plot_original_arc(df, original_output, title_name)

    cumulative_output = os.path.join(output_dir, f"{base_name}_cumulative.html")
    plot_cumulative_arc(df, cumulative_output, title_name)
    
    # Return metadata to the main thread for the combined master graph
    final_score = df["Cumulative_Score"].iloc[-1]
    return {
        "title": title_name,
        "df": df,
        "final_score": final_score
    }

# ==========================================
# STEP 4: VISUALIZATION
# ==========================================
def plot_original_arc(df, output_file, title):
    """Plots the original raw-score narrative arc graph."""
    fig = go.Figure()

    # 1. Raw Data (Scatter)
    fig.add_trace(go.Scatter(
        x=df["Sentence_Index"], y=df["Raw_Score"], mode="markers",
        name="Raw Sentence (Scatter)", marker=dict(size=4, color="gray", opacity=0.2),
        text=df["Text"], hoverinfo="text+y"
    ))

    # 2. Rolling 20
    fig.add_trace(go.Scatter(
        x=df["Sentence_Index"], y=df["Rolling_20"], mode="lines",
        name="Rolling Average (20)", line=dict(color="blue", width=2), visible=False
    ))

    # 3. Rolling 100 (Default visible)
    fig.add_trace(go.Scatter(
        x=df["Sentence_Index"], y=df["Rolling_100"], mode="lines",
        name="Rolling Average (100)", line=dict(color="purple", width=3), visible=True
    ))

    # 4. SavGol 51
    fig.add_trace(go.Scatter(
        x=df["Sentence_Index"], y=df["SavGol_51"], mode="lines",
        name="SciPy SavGol (51)", line=dict(color="green", width=2), visible=False
    ))

    # 5. SavGol 201
    fig.add_trace(go.Scatter(
        x=df["Sentence_Index"], y=df["SavGol_201"], mode="lines",
        name="SciPy SavGol (201)", line=dict(color="red", width=4), visible=False
    ))

    fig.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)

    fig.update_layout(
        updatemenus=[dict(
            active=1,
            buttons=[
                dict(label="1. None (Raw Volatility)", method="update", args=[{"visible": [True, False, False, False, False]}, {"title": f"{title}: Raw Volatility Only"}]),
                dict(label="2. Rolling Average (100 - Act Level)", method="update", args=[{"visible": [True, False, True, False, False]}, {"title": f"{title}: Rolling Average (Window=100)"}]),
                dict(label="3. Rolling Average (20 - Scene Level)", method="update", args=[{"visible": [True, True, False, False, False]}, {"title": f"{title}: Rolling Average (Window=20)"}]),
                dict(label="4. SciPy SavGol (201 - Macro Arc)", method="update", args=[{"visible": [True, False, False, False, True]}, {"title": f"{title}: Savitzky-Golay Filter (Macro)"}]),
                dict(label="5. Compare All Trends", method="update", args=[{"visible": [True, True, True, True, True]}, {"title": f"{title}: All Smoothing Strategies"}])
            ],
            direction="down", pad={"r": 10, "t": 10}, showactive=True, x=0.1, xanchor="left", y=1.15, yanchor="top"
        )],
        title=f"{title}: The Shape of Subversion (Original)",
        xaxis_title="Narrative Time (Sentence Index)",
        yaxis_title="Sentiment Valence (-1.0 Tragic to +1.0 Comedic)",
        yaxis=dict(range=[-1.1, 1.1]),
        template="plotly_white", hovermode="x unified"
    )

    fig.write_html(output_file)

def plot_cumulative_arc(df, output_file, title):
    """Plots the additive cumulative narrative arc graph."""
    fig = go.Figure()

    # 1. Raw Cumulative Trajectory
    fig.add_trace(go.Scatter(
        x=df["Sentence_Index"], y=df["Cumulative_Score"], mode="lines",
        name="Raw Cumulative Trajectory", line=dict(color="gray", width=1, dash="dot"),
        opacity=0.5, text=df["Text"], hoverinfo="text+y", visible=True
    ))

    # 2. Rolling 100
    fig.add_trace(go.Scatter(
        x=df["Sentence_Index"], y=df["Cumul_Rolling_100"], mode="lines",
        name="Cumulative Rolling (100)", line=dict(color="purple", width=3), visible=False
    ))

    # 3. SavGol 51
    fig.add_trace(go.Scatter(
        x=df["Sentence_Index"], y=df["Cumul_SavGol_51"], mode="lines",
        name="SciPy SavGol (51)", line=dict(color="blue", width=2), visible=False
    ))

    # 4. SavGol 201 (Default visible)
    fig.add_trace(go.Scatter(
        x=df["Sentence_Index"], y=df["Cumul_SavGol_201"], mode="lines",
        name="SciPy SavGol (201 - Shape of Story)", line=dict(color="red", width=4), visible=True
    ))

    fig.add_hline(y=0, line_dash="solid", line_color="black", opacity=0.8)

    fig.update_layout(
        updatemenus=[dict(
            active=0,
            buttons=[
                dict(label="1. Macro Story Shape (SavGol 201)", method="update", args=[{"visible": [True, False, False, True]}, {"title": f"{title}: The Vonnegut Shape"}]),
                dict(label="2. Act-Level Trajectory (Rolling 100)", method="update", args=[{"visible": [True, True, False, False]}, {"title": f"{title}: Act-Level Fortune"}]),
                dict(label="3. Scene-Level Flow (SavGol 51)", method="update", args=[{"visible": [True, False, True, False]}, {"title": f"{title}: Scene-Level Fortune"}]),
                dict(label="4. Raw Cumulative Only", method="update", args=[{"visible": [True, False, False, False]}, {"title": f"{title}: Raw Additive Walk"}]),
                dict(label="5. Compare All", method="update", args=[{"visible": [True, True, True, True]}, {"title": f"{title}: All Smoothing Strategies"}])
            ],
            direction="down", pad={"r": 10, "t": 10}, showactive=True, x=0.1, xanchor="left", y=1.15, yanchor="top"
        )],
        title=f"{title}: The Vonnegut Shape (Cumulative)", 
        xaxis_title="Narrative Time (Sentence Index)", 
        yaxis_title="Net Cumulative Fortune",
        template="plotly_white", hovermode="x unified"
    )

    fig.write_html(output_file)

def generate_color(index, total):
    """Generates a gradient from Green (Positive) to Red (Tragic) based on sorted rank"""
    hue = 0.33 - (0.33 * (index / max(1, total - 1))) # 0.33 is green, 0.0 is red
    r, g, b = colorsys.hsv_to_rgb(hue, 0.8, 0.8)
    return f"rgb({int(r*255)}, {int(g*255)}, {int(b*255)})"

def plot_combined_arc(results, output_file):
    """Plots the master graph containing the macro arcs of all processed texts."""
    print(f"\nGenerating Master Interactive Graph at {output_file}...")
    
    # Sort results by final cumulative score (Highest/Comedies first, Lowest/Tragedies last)
    results.sort(key=lambda x: x["final_score"], reverse=True)

    fig = go.Figure()

    for i, res in enumerate(results):
        df = res["df"]
        title = res["title"]
        final_score = res["final_score"]
        
        # Color coding: Green for Comedies, Red for Tragedies, Yellow/Orange for in-between
        line_color = generate_color(i, len(results))

        fig.add_trace(
            go.Scatter(
                x=df["Sentence_Index"],
                y=df["Macro_Arc"],
                mode="lines",
                name=f"{title} (Final: {final_score:.1f})",
                line=dict(color=line_color, width=3),
                opacity=0.8,
                customdata=df["Text"],
                hovertemplate=
                "<b>" + title + "</b><br>" +
                "Line Index: %{x}<br>" +
                "Fortune: %{y:.1f}<br>" +
                "<i>\"%{customdata}\"</i><extra></extra>"
            )
        )

    fig.add_hline(y=0, line_dash="solid", line_color="black", opacity=0.8)

    fig.update_layout(
        title="The Complete Shakespearean Fortune Map (Sorted by Final Sentiment)",
        xaxis_title="Narrative Time (Sentence Index)",
        yaxis_title="Net Cumulative Fortune",
        template="plotly_dark", # Dark mode makes the neon gradient pop!
        hovermode="closest",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=1.01, title_text="Plays (Highest to Lowest)"),
        margin=dict(r=200) # Give space for the legend
    )

    fig.write_html(output_file)
    print("Success! Master graph saved.")

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Process multiple texts to generate individual and combined cumulative arc graphs.")
    parser.add_argument("text_files", nargs="+", help="One or more text files to process")
    parser.add_argument("--output_dir", default="html_output", help="Directory for all generated HTML files")
    parser.add_argument("--max-workers", type=int, default=5)
    args = parser.parse_args()

    # Ensure the directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    processed_results = []

    print(f"Starting batch processing of {len(args.text_files)} files...")
    print(f"Outputting dual graphs and combined index.html to: '{args.output_dir}/'")
    
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = [executor.submit(process_single_file, tf, args.output_dir) for tf in args.text_files]
        
        for future in as_completed(futures):
            res = future.result()
            if res:
                processed_results.append(res)

    if processed_results:
        # Generate the master 'index.html' holding everything
        index_path = os.path.join(args.output_dir, "index.html")
        plot_combined_arc(processed_results, index_path)
    else:
        print("No valid data was processed.")
