"""Create one independently named notebook per Data Science/Analytics assignment."""

from __future__ import annotations

import urllib.request
import zipfile
from pathlib import Path

import nbformat

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "DATA SCIENCE" / "data"

NOTEBOOKS = [
    ("DATA SCIENCE", "01_iris_flower_classification.ipynb", "DS1", "Iris Flower Classification", "Built-in scikit-learn Iris dataset."),
    ("DATA SCIENCE", "02_unemployment_analysis.ipynb", "DS2", "Unemployment Analysis with Python", "Deterministic synthetic example; replace before making real-world claims."),
    ("DATA SCIENCE", "03_car_price_prediction.ipynb", "DS3", "Car Price Prediction", "Public Cardekho used-car listing dataset if supplied; otherwise clearly labelled synthetic fallback."),
    ("DATA SCIENCE", "04_sms_spam_detection.ipynb", "DS4", "Email/SMS Spam Detection", "UCI SMS Spam Collection, a public labelled text corpus."),
    ("DATA SCIENCE", "05_advertising_sales_prediction.ipynb", "DS5", "Sales Prediction Using Advertising Spend", "ISLR Advertising dataset (200 observations; TV, radio, newspaper, sales)."),
    ("DATA ANALYTICS/Level 1", "01_retail_sales_eda.ipynb", "DA1", "EDA on Retail Sales Data", "UCI Online Retail (2010–2011); dataset does not include age, gender, or product-category fields."),
    ("DATA ANALYTICS/Level 1", "02_customer_segmentation.ipynb", "DA2", "Customer Segmentation Analysis", "Customer-level RFM aggregated from UCI Online Retail transactions."),
    ("DATA ANALYTICS/Level 1", "03_cleaning_data.ipynb", "DA3", "Cleaning Data", "Deliberately dirtied UCI Online Retail sample; introduced defects are documented."),
    ("DATA ANALYTICS/Level 1", "04_sentiment_analysis.ipynb", "DA4", "Sentiment Analysis", "Financial PhraseBank sentences_allagree, CC BY-NC-SA 3.0; financial-news sentiment."),
    ("DATA ANALYTICS/Level 2", "01_house_price_regression.ipynb", "DA5", "Predicting House Prices with Linear Regression", "UCI Real Estate Valuation dataset; historical transactions in Sindian District, Taiwan."),
    ("DATA ANALYTICS/Level 2", "02_wine_quality_prediction.ipynb", "DA6", "Wine Quality Prediction", "UCI Wine Quality red-wine dataset."),
    ("DATA ANALYTICS/Level 2", "03_fraud_detection.ipynb", "DA7", "Fraud Detection", "Deterministic 1% synthetic fraud sample; contains no payment data."),
    ("DATA ANALYTICS/Level 2", "04_play_store_analysis.ipynb", "DA8", "Unveiling the Android App Market", "2018 Google Play app metadata and supplied review-sentiment labels; Creative Commons Attribution 3.0."),
    ("DATA ANALYTICS/Level 2", "05_autocomplete_autocorrect.ipynb", "DA9", "Autocomplete and Autocorrect Analytics", "Small deterministic text corpus; limited benchmark."),
]


def fetch_uci_zip(url: str, target_name: str, member: str) -> None:
    target = DATA_DIR / target_name
    if target.exists():
        return
    archive_path = DATA_DIR / f"{target_name}.zip"
    print(f"Downloading {target_name} from the UCI Machine Learning Repository…")
    urllib.request.urlretrieve(url, archive_path)
    with zipfile.ZipFile(archive_path) as archive:
        matched = next((name for name in archive.namelist() if name.endswith(member)), None)
        if matched is None:
            raise FileNotFoundError(f"{member} was not present in the downloaded UCI archive.")
        target.write_bytes(archive.read(matched))
    archive_path.unlink()


def extract_member(archive_path: Path, target_name: str, member: str) -> None:
    target = DATA_DIR / target_name
    if target.exists():
        return
    with zipfile.ZipFile(archive_path) as archive:
        matched = next((name for name in archive.namelist() if name.endswith(member)), None)
        if matched is None:
            raise FileNotFoundError(f"{member} was not present in {archive_path.name}.")
        target.write_bytes(archive.read(matched))


def fetch_github_file(path: str, target_name: str) -> None:
    target = DATA_DIR / target_name
    if target.exists():
        return
    revision = "f605ed273d131a8661706ef4c9335b0961d74707"
    url = (
        "https://api.github.com/repos/KamgangAnthony/"
        "The-Android-App-Market-on-Google-Play/contents/"
        f"{path}?ref={revision}"
    )
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github.raw+json",
            "User-Agent": "OASIS-Data-Notebook-Builder",
        },
    )
    print(f"Downloading {target_name} from the pinned public dataset revision…")
    with urllib.request.urlopen(request) as response:
        content = response.read()
    if not content:
        raise OSError(f"The public dataset download for {target_name} was empty.")
    target.write_bytes(content)


def create_notebooks() -> None:
    for folder, filename, code, title, source_note in NOTEBOOKS:
        path = ROOT / folder / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        notebook = nbformat.v4.new_notebook()
        notebook.cells = [
            nbformat.v4.new_markdown_cell(
                f"# {title}\n\n"
                f"**Task:** {code}  \n"
                f"**Data provenance:** {source_note}\n\n"
                "This notebook calls a clearly separated, commented analysis module so the workflow can be run "
                "and maintained consistently. Run the cells from top to bottom. Metrics and plots are calculated "
                "at runtime; no results have been hand-entered. Synthetic-data outputs are demonstrations only."
            ),
            nbformat.v4.new_markdown_cell(
                "## Reproducibility and interpretation\n\n"
                "The notebook uses a fixed random seed where sampling is involved. Review the printed data "
                "provenance before interpreting a chart. Synthetic data can test code paths, not support real "
                "business, labour-market, property, finance, or app-store conclusions."
            ),
            nbformat.v4.new_code_cell(
                "from pathlib import Path\n"
                "import sys\n"
                "working = Path.cwd().resolve()\n"
                "candidates = [working, *working.parents]\n"
                "project = next((p for p in candidates if (p / 'DATA SCIENCE' / 'analysis_tasks.py').exists()), None)\n"
                "if project is None:\n"
                "    project = next((p for p in candidates if (p / 'analysis_tasks.py').exists()), None)\n"
                "if project is None:\n"
                "    raise FileNotFoundError('Could not locate DATA SCIENCE/analysis_tasks.py. Open Jupyter from the OASIS workspace.')\n"
                "sys.path.insert(0, str(project / 'DATA SCIENCE' if (project / 'DATA SCIENCE').exists() else project))\n"
                "from analysis_tasks import run_task\n"
                f"run_task({code!r})\n"
            ),
        ]
        notebook.metadata = {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.12"},
        }
        nbformat.write(notebook, path)
        print(path.relative_to(ROOT))


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    fetch_uci_zip(
        "https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip",
        "SMSSpamCollection",
        "SMSSpamCollection",
    )
    fetch_uci_zip(
        "https://archive.ics.uci.edu/static/public/352/online+retail.zip",
        "Online Retail.xlsx",
        "Online Retail.xlsx",
    )
    fetch_uci_zip(
        "https://archive.ics.uci.edu/static/public/477/real+estate+valuation+data+set.zip",
        "Real estate valuation data set.xlsx",
        "Real estate valuation data set.xlsx",
    )
    phrasebank_zip = DATA_DIR / "FinancialPhraseBank-v1.0.zip"
    phrasebank_file = DATA_DIR / "Sentences_AllAgree.txt"
    if not phrasebank_file.exists():
        if not phrasebank_zip.exists():
            print("Downloading Financial PhraseBank dataset…")
            urllib.request.urlretrieve(
                "https://huggingface.co/datasets/takala/financial_phrasebank/resolve/main/data/FinancialPhraseBank-v1.0.zip",
                phrasebank_zip,
            )
        extract_member(phrasebank_zip, "Sentences_AllAgree.txt", "Sentences_AllAgree.txt")
    fetch_uci_zip(
        "https://archive.ics.uci.edu/static/public/186/wine+quality.zip",
        "winequality-red.csv",
        "winequality-red.csv",
    )
    fetch_github_file("datasets/apps.csv", "google_play_apps.csv")
    fetch_github_file("datasets/user_reviews.csv", "google_play_user_reviews.csv")
    fetch_github_file("license.txt", "google_play_dataset_license.txt")
    corpus = DATA_DIR / "alice_adventures.txt"
    if not corpus.exists():
        print("Downloading Project Gutenberg public-domain Alice text for the NLP exercise…")
        urllib.request.urlretrieve("https://www.gutenberg.org/cache/epub/11/pg11.txt", corpus)
    create_notebooks()


if __name__ == "__main__":
    main()
