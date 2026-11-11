# Data Science

Five separately named Jupyter notebooks:

1. [Iris flower classification](./01_iris_flower_classification.ipynb)
2. [Unemployment analysis](./02_unemployment_analysis.ipynb)
3. [Car price prediction](./03_car_price_prediction.ipynb)
4. [SMS spam detection](./04_sms_spam_detection.ipynb)
5. [Advertising sales prediction](./05_advertising_sales_prediction.ipynb)

The Iris notebook uses scikit-learn's built-in dataset. The car-price and unemployment
workflows currently use labelled synthetic demonstrations; a suitable, verified source
dataset is not present for either. Advertising uses the ISLR Advertising dataset. The SMS
spam, Online Retail, Real Estate Valuation, and
Wine Quality datasets come from UCI; sentiment uses Financial PhraseBank (CC BY-NC-SA 3.0),
and autocomplete uses Project Gutenberg's public-domain *Alice's Adventures in Wonderland*.
Play Store market analysis uses the pinned 2018 app/review dataset under CC BY 3.0.
`build_notebooks.py` downloads/extracts supported public sources.
Play Store review sentiment is computed with VADER; supplied source labels are retained
only as a comparison reference. Install `requirements.txt` before running the notebooks.

The retail transaction data has no customer age/gender or product-category field; those
breakdowns are reported as unavailable instead of being fabricated. See
[data/SOURCES.md](./data/SOURCES.md) for source links and licensing. Remaining synthetic
examples are explicitly marked and must not be presented as measured real-world findings.

## Setup and execution

From the workspace root, install the project's existing packages if needed, then run:

```powershell
python -m pip install -r "D:\Oasis\DATA SCIENCE\requirements.txt"
python "D:\Oasis\DATA SCIENCE\build_notebooks.py"
jupyter lab "D:\Oasis\DATA SCIENCE"
```

The notebooks import `analysis_tasks.py`, which contains the reusable, task-specific
analysis steps. The fixed random seed makes synthetic examples reproducible.
