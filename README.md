# Up and Down

Narrative arc analysis. `download.sh` is provided as a helper, with defaults for
Shakespeare play analysis.

## Setup

Make sure to have `ffmpeg` installed. Tested with Python 3.12. Then,
`pip install -r requirements.txt`.

## Run

```sh
./download.sh && ./split.py # for Shakespeare plays
./arc.py                    # for rolling average and cumulative
```

Then, simply view any `.html` file in your browser.
