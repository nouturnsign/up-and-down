# Up and Down

Shakespeare narrative arc analysis via sentiment analysis.

## Methodology

This document outlines the end-to-end data analysis methodology used to
quantify, transform, and visualize the narrative arcs of 38 Shakespearean plays.
The pipeline blends Natural Language Processing (NLP), machine learning
sentiment analysis, and signal processing to mathematically map the "fortune" of
a narrative over time.

### Phase 1: Ingestion and Text Structuring

The first step of the pipeline focuses on cleaning and parsing the raw text of
the plays into a structured format suitable for algorithmic analysis.

Algorithm/Tool: `spaCy` (using the `en_core_web_sm` model).

Process: 1. The raw text of each play is loaded into memory. 2. The text is
passed through the `spaCy` NLP pipeline to perform sentence tokenization. 3.
Data Cleaning: Sentences are stripped of newline characters. A filtering
mechanism is applied to drop any sentence containing three or fewer words. This
crucial step removes noisy data such as short stage directions (e.g., "Exit
Hamlet."), character monikers, or isolated exclamations, ensuring the sentiment
analysis is performed on complete, context-rich thoughts.

### Phase 2: Contextual Sentiment Scoring

Once the text is structured into sequential sentences, the pipeline scores the
emotional valence (positivity or negativity) of each line.

Algorithm/Tool: Hugging Face transformers (using
`distilbert-base-uncased-finetuned-sst-2-english`).

Process:

1. Each sentence is passed through the DistilBERT model, which has been
   fine-tuned on the Stanford Sentiment Treebank (SST-2) dataset.
2. The model outputs a classification (POSITIVE or NEGATIVE) and a confidence
   score.
3. Bipolar Transformation: The confidence scores are mathematically mapped to a
   continuous bipolar scale from -1.0 to 1.0. POSITIVE labels are converted to
   positive floats, while NEGATIVE labels are multiplied by -1 to become
   negative floats. This creates the Raw Score for each sentence in
   chronological order.

### Phase 3: Mathematical Transformation & Smoothing

Raw sentiment scores of a play are highly volatile, bouncing wildly between
positive and negative from sentence to sentence. To extract meaningful narrative
shapes, the pipeline uses signal processing techniques, outputting two distinct
metrics.

#### A. The "Original" Metric (Raw Volatility)

This analyzes the localized emotional state of the play at any given moment.

- Rolling Averages (`pandas`): Moving averages with windows of 20 (approximate
  scene-level mood) and 100 (approximate act-level mood) are applied. The
  `center=True` parameter is used to prevent phase-shifting (time lag) in the
  visualization.
- Savitzky-Golay Filter (`scipy.signal.savgol_filter`): A digital filter is
  applied (windows of 51 and 201, polynomial order of 3) to smooth the data by
  fitting successive sub-sets of adjacent data points with a low-degree
  polynomial. This preserves the shape and height of emotional peaks better than
  standard rolling averages.

#### B. The "Cumulative" Metric (Additive Fortune)

This treats the narrative as a continuous "random walk" or stock market chart,
tracking the net accumulation of positive or negative fortune.

- Cumulative Sum: The pipeline takes the running tally of the Raw Scores. A play
  with more positive lines will drift upwards over time (Comedy), while a play
  saturated with negative lines will plunge (Tragedy).
- Macro-Arc Smoothing: The cumulative data is then smoothed using a massive
  Savitzky-Golay filter (window length up to 201, or adjusted dynamically for
  shorter texts). This resulting line represents the core Macro Arc of the
  story.

### Phase 4: Visualization and Aggregation

The numerical data is mapped into interactive visual artifacts using
`plotly.graph_objects`.

Individual Graphs: For each play, two interactive HTML files are generated: an
\_original.html (showing volatility) and a \_cumulative.html (showing the
additive fortune). These graphs include toggleable layers and embed the raw text
directly into the hover data.

Master Aggregation:

1. The pipeline records the final cumulative score (the "ultimate fortune") of
   every processed play.
2. The plays are sorted in descending order from the highest positive score to
   the lowest negative score.
3. A unified master.html graph is generated plotting the Macro Arcs of all 38
   plays together.
4. Color Mapping: A dynamic HSV-to-RGB color gradient is applied based on the
   sorted rank. The most positive plays are mapped to green, mid-tier plays to
   yellow/orange, and the most tragic to deep red.

### Phase 5: Dashboard Presentation (The Wrapper)

Because Plotly outputs heavy, self-contained HTML files, rendering them
simultaneously would crash a standard browser.

Architecture: A React Single Page Application (SPA), built with Vite and
Tailwind CSS, serves as the dashboard.

## Developer Setup

First, clone this repository and change into this directory.

```sh
git clone https://github.com/nouturnsign/up-and-down.git
cd up-and-down
```

Make sure you have at least Python 3.12 and at least Node.js 25 installed. The
exact version is pinned in `.nvmrc` and can be set via `nvm use`.

Then, setup environment and install Python dependencies.

```sh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Then, install Node dependencies.

```sh
npm install
```

Then, build and view.

```sh
./download.sh                    # download complete Shakespeare works
./split.py                       # separate the plays
./arc.py shakespeare_plays/*.txt # generate the plots
npm run dev                      # run development server to view
```

Note that `./arc.py` provides additional options for customization. See
`./arc.py --help` if this step fails.
