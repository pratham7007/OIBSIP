"""Reproducible, task-specific analysis functions used by the companion notebooks."""

from __future__ import annotations

import re
import string
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LinearRegression, LogisticRegression, SGDClassifier
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix, f1_score,
    mean_absolute_error, mean_squared_error, precision_score, recall_score,
    roc_auc_score, roc_curve, r2_score,
)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

SEED = 42
ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "outputs"
OUT_DIR.mkdir(exist_ok=True)
ONLINE_RETAIL_PATH = DATA_DIR / "Online Retail.xlsx"
PHRASEBANK_PATH = DATA_DIR / "Sentences_AllAgree.txt"
REAL_ESTATE_PATH = DATA_DIR / "Real estate valuation data set.xlsx"
sns.set_theme(style="whitegrid")


def load_online_retail() -> pd.DataFrame:
    if not ONLINE_RETAIL_PATH.exists():
        raise FileNotFoundError(
            f"Download UCI Online Retail with build_notebooks.py; expected {ONLINE_RETAIL_PATH}."
        )
    return pd.read_excel(ONLINE_RETAIL_PATH, engine="openpyxl")


def report(df: pd.DataFrame) -> None:
    print("Shape:", df.shape)
    print("\nDtypes:\n", df.dtypes)
    print("\nNulls:\n", df.isna().sum())
    print("\nDescriptive statistics:\n", df.describe(include="all").T)


def score_classifier(name: str, model, x_train, x_test, y_train, y_test) -> dict:
    model.fit(x_train, y_train)
    predicted = model.predict(x_test)
    print(f"\n{name}: accuracy={accuracy_score(y_test, predicted):.3f}, macro-F1={f1_score(y_test, predicted, average='macro'):.3f}")
    print(classification_report(y_test, predicted, zero_division=0))
    print("Confusion matrix:\n", confusion_matrix(y_test, predicted))
    return {"name": name, "model": model, "prediction": predicted,
            "accuracy": accuracy_score(y_test, predicted),
            "f1": f1_score(y_test, predicted, average="macro")}


def score_regressor(name: str, model, x_train, x_test, y_train, y_test) -> dict:
    model.fit(x_train, y_train)
    predicted = model.predict(x_test)
    rmse = mean_squared_error(y_test, predicted) ** 0.5
    result = {"name": name, "model": model, "prediction": predicted,
              "mae": mean_absolute_error(y_test, predicted), "rmse": rmse,
              "r2": r2_score(y_test, predicted)}
    print(f"{name}: MAE={result['mae']:.3f}, RMSE={rmse:.3f}, R²={result['r2']:.3f}")
    return result


def iris_classification() -> None:
    bunch = load_iris(as_frame=True)
    df = bunch.frame.rename(columns=dict(zip(bunch.feature_names, ["sepal_length", "sepal_width", "petal_length", "petal_width"])))
    df["species"] = df["target"].map(dict(enumerate(bunch.target_names)))
    report(df.drop(columns="target"))
    sns.pairplot(df, vars=["sepal_length", "sepal_width", "petal_length", "petal_width"], hue="species", corner=True)
    plt.show()
    df.drop(columns="target").boxplot(by="species", figsize=(11, 6), rot=20)
    plt.suptitle("Iris feature distributions by species")
    plt.tight_layout()
    plt.show()
    x_train, x_test, y_train, y_test = train_test_split(
        bunch.data, bunch.target, test_size=0.2, random_state=SEED, stratify=bunch.target)
    models = [
        score_classifier("Logistic Regression", Pipeline([("scale", StandardScaler()), ("model", LogisticRegression(max_iter=1000))]), x_train, x_test, y_train, y_test),
        score_classifier("K-Nearest Neighbours", Pipeline([("scale", StandardScaler()), ("model", KNeighborsClassifier(n_neighbors=5))]), x_train, x_test, y_train, y_test),
    ]
    print("Best held-out macro-F1:", max(models, key=lambda row: row["f1"])["name"])
    print("Petal length and petal width are visually the most discriminative features in this dataset.")


def unemployment_analysis() -> None:
    print("DATA PROVENANCE: Synthetic, deterministic demonstration data; not a report of measured Indian unemployment.")
    rng = np.random.default_rng(SEED)
    dates = pd.date_range("2018-01-01", "2022-12-01", freq="MS")
    states = ["Delhi", "Haryana", "Maharashtra", "Rajasthan", "Tamil Nadu", "Uttar Pradesh", "West Bengal"]
    bases = dict(zip(states, [7.0, 8.5, 6.4, 9.0, 5.2, 8.0, 6.1]))
    rows = []
    for state in states:
        for date in dates:
            covid_shock = (15 if date.year == 2020 and date.month in (4, 5) else 5 if date.year == 2020 else 0)
            rate = max(1, bases[state] + 1.4*np.sin(date.month/12*2*np.pi) + covid_shock + rng.normal(0, .6))
            rows.append((state, date, rate, 100-rate-rng.uniform(5, 12), rate+rng.uniform(8, 15)))
    df = pd.DataFrame(rows, columns=["Region", "Date", "Estimated Unemployment Rate (%)", "Estimated Employed", "Labour Participation Rate (%)"])
    df["Date"] = pd.to_datetime(df["Date"])
    report(df)
    monthly = df.groupby(["Date", "Region"])["Estimated Unemployment Rate (%)"].mean().reset_index()
    sns.lineplot(data=monthly[monthly.Region.isin(states[:3])], x="Date", y="Estimated Unemployment Rate (%)", hue="Region")
    plt.title("Illustrative monthly unemployment rates (synthetic)")
    plt.show()
    top = df.groupby("Region")["Estimated Unemployment Rate (%)"].mean().nlargest(10).sort_values()
    top.plot.barh(title="Regions with highest average rate (synthetic)")
    plt.xlabel("Rate (%)")
    plt.show()
    sns.heatmap(df.select_dtypes("number").corr(), annot=True, cmap="vlag", center=0)
    plt.title("Synthetic variable correlations")
    plt.show()
    df["period"] = np.where(df.Date < "2020-03-01", "pre-COVID", "post-COVID")
    print(df.groupby("period")["Estimated Unemployment Rate (%)"].mean())
    print("Interpretation is limited to this simulated example; replace only with a documented, openly licensed source for empirical conclusions.")


def car_price_prediction() -> None:
    print("DATA PROVENANCE: Synthetic, reproducible vehicle sample for pipeline demonstration; not a market valuation.")
    rng = np.random.default_rng(SEED)
    n = 450
    year = rng.integers(2008, 2024, n)
    names = rng.choice(["Maruti Swift", "Hyundai i20", "Honda City", "Tata Nexon", "Toyota Etios"], n)
    fuel = rng.choice(["Petrol", "Diesel", "CNG"], n, p=[.58, .34, .08])
    transmission = rng.choice(["Manual", "Automatic"], n, p=[.75, .25])
    mileage = rng.normal(48_000, 22_000, n).clip(1000, 160_000)
    brand = [name.split()[0].title() for name in names]
    age = 2024-year
    price = np.maximum(70_000, 1_100_000 - age*53_000 - mileage*2.7 + (fuel == "Diesel")*90_000 + (transmission == "Automatic")*65_000 + rng.normal(0, 80_000, n))
    df = pd.DataFrame({"name": names, "year": year, "mileage_km": mileage, "fuel": fuel, "transmission": transmission, "selling_price": price})
    df["fuel"] = df["fuel"].str.strip().str.title()
    df["transmission"] = df["transmission"].str.strip().str.title()
    df = df.drop_duplicates().dropna()
    df["car_age"] = 2024-df["year"]
    df["brand"] = df["name"].str.split().str[0].str.title()
    report(df)
    sns.histplot(df["selling_price"], kde=True)
    plt.title("Synthetic selling-price distribution")
    plt.show()
    sns.boxplot(data=df, x="fuel", y="selling_price")
    plt.show()
    sns.scatterplot(data=df, x="car_age", y="selling_price", hue="transmission")
    plt.show()
    numeric = df.select_dtypes("number")
    sns.heatmap(numeric.corr(), annot=True, cmap="vlag", center=0)
    plt.show()
    x = pd.get_dummies(df[["car_age", "mileage_km", "fuel", "transmission", "brand"]], drop_first=True)
    y = df.selling_price
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=.2, random_state=SEED)
    results = [
        score_regressor("Linear Regression", LinearRegression(), x_train, x_test, y_train, y_test),
        score_regressor("Random Forest", RandomForestRegressor(n_estimators=150, min_samples_leaf=2, random_state=SEED), x_train, x_test, y_train, y_test),
    ]
    best = max(results, key=lambda row: row["r2"])
    if hasattr(best["model"], "feature_importances_"):
        pd.Series(best["model"].feature_importances_, index=x.columns).nlargest(10).sort_values().plot.barh(title="Most influential encoded features")
    else:
        pd.Series(best["model"].coef_, index=x.columns).abs().nlargest(10).sort_values().plot.barh(title="Largest absolute coefficients")
    plt.show()


def spam_detection() -> None:
    print("TF-IDF weights words by term frequency in a message and inverse document frequency across messages.")
    data = DATA_DIR / "SMSSpamCollection"
    if not data.exists():
        raise FileNotFoundError(f"Dataset not found at {data}. See DATA SCIENCE/README.md to download the UCI SMS Spam Collection.")
    df = pd.read_csv(data, sep="\t", header=None, names=["label", "text"], encoding="utf-8")
    report(df)
    print(df.label.value_counts(normalize=True).mul(100).round(2).astype(str) + "%")
    sns.countplot(data=df, x="label")
    plt.title("SMS spam dataset class distribution")
    plt.show()
    # Strip punctuation before TF-IDF; vectorizer handles tokenisation and stop words.
    df["clean_text"] = df.text.str.lower().str.translate(str.maketrans("", "", string.punctuation))
    x_train, x_test, y_train, y_test = train_test_split(df.clean_text, df.label, test_size=.2, random_state=SEED, stratify=df.label)
    vectorizer = TfidfVectorizer(stop_words="english", min_df=2, ngram_range=(1, 2))
    x_train_vec, x_test_vec = vectorizer.fit_transform(x_train), vectorizer.transform(x_test)
    results = [
        score_classifier("Multinomial Naive Bayes", MultinomialNB(), x_train_vec, x_test_vec, y_train, y_test),
        score_classifier("Logistic Regression", LogisticRegression(max_iter=1000), x_train_vec, x_test_vec, y_train, y_test),
    ]
    best = max(results, key=lambda row: row["f1"])
    mistakes = pd.DataFrame({"text": x_test, "actual": y_test, "predicted": best["prediction"]})
    print("Misclassified examples:\n", mistakes[mistakes.actual != mistakes.predicted].head(5).to_string(index=False))
    print("Spam recall matters because missed spam still reaches a user's inbox; precision is also important to avoid hiding legitimate messages.")


def sales_prediction() -> None:
    path = DATA_DIR / "Advertising.csv"
    if not path.exists():
        raise FileNotFoundError(f"Download ISLR Advertising.csv; expected {path}.")
    print("DATA PROVENANCE: ISLR Advertising teaching dataset; observational relationships do not prove causal effects.")
    df = pd.read_csv(path).rename(columns=lambda name: name.strip().title())
    df = df.rename(columns={"Tv": "TV"})
    df = df.drop(columns=["Unnamed: 0"], errors="ignore")
    report(df)
    sns.pairplot(df)
    plt.show()
    for channel in ("TV", "Radio", "Newspaper"):
        sns.scatterplot(data=df, x=channel, y="Sales")
        plt.title(f"Sales vs {channel} spend")
        plt.show()
    sns.heatmap(df.corr(), annot=True, cmap="vlag", center=0)
    plt.show()
    x_train, x_test, y_train, y_test = train_test_split(df.drop(columns="Sales"), df.Sales, test_size=.2, random_state=SEED)
    results = [
        score_regressor("Linear Regression", LinearRegression(), x_train, x_test, y_train, y_test),
        score_regressor("Random Forest", RandomForestRegressor(n_estimators=150, min_samples_leaf=3, random_state=SEED), x_train, x_test, y_train, y_test),
    ]
    best = max(results, key=lambda row: row["r2"])
    residuals = y_test-best["prediction"]
    sns.scatterplot(x=best["prediction"], y=residuals)
    plt.axhline(0, color="red")
    plt.title(f"{best['name']} residual check")
    plt.xlabel("Predicted sales")
    plt.ylabel("Residual")
    plt.show()
    print("Linear coefficients:\n", pd.Series(results[0]["model"].coef_, index=x_train.columns).sort_values(ascending=False))
    strongest = pd.Series(results[0]["model"].coef_, index=x_train.columns).abs().idxmax()
    print(f"Largest absolute linear coefficient per spend unit: {strongest}. Compare channel scales before interpreting impact; observational data do not establish causal lift.")


def retail_eda() -> None:
    print("DATA PROVENANCE: UCI Online Retail transactions, December 2010–December 2011.")
    df = load_online_retail()
    report(df)
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")
    df["InvoiceNo"] = df["InvoiceNo"].astype("string")
    df = df.dropna(subset=["InvoiceDate", "Description", "CustomerID"])
    df = df.loc[
        ~df["InvoiceNo"].str.startswith("C", na=False)
        & (df["Quantity"] > 0)
        & (df["UnitPrice"] > 0)
    ].copy()
    df["Revenue"] = df["Quantity"] * df["UnitPrice"]
    df["Product"] = df["Description"].astype("string").str.strip()
    report(df)
    numeric = df[["Quantity", "UnitPrice", "Revenue"]]
    stats = numeric.agg(["mean", "median", "std"]).T
    stats["mode"] = numeric.mode().iloc[0]
    print("Descriptive statistics:\n", stats)
    monthly=df.set_index("InvoiceDate").resample("ME").Revenue.sum()
    quarterly=df.set_index("InvoiceDate").resample("QE").Revenue.sum()
    monthly.plot(title="Monthly revenue (GBP)"); plt.show()
    print(f"Observation: peak month was {monthly.idxmax():%B %Y} (£{monthly.max():,.0f}); this is historical sample activity.")
    quarterly.plot(title="Quarterly revenue (GBP)"); plt.show()
    peak_quarter = quarterly.idxmax()
    print(f"Observation: peak quarter was {peak_quarter.year} Q{peak_quarter.quarter} (£{quarterly.max():,.0f}).")
    df.assign(Weekday=df["InvoiceDate"].dt.day_name()).groupby("Weekday").Revenue.sum().reindex(
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    ).dropna().plot.bar(title="Revenue by weekday (Saturday absent in source)")
    plt.show()
    country_revenue = df.groupby("Country").Revenue.sum()
    country_revenue.nlargest(10).sort_values().plot.barh(title="Top 10 countries by revenue (GBP)")
    plt.show()
    print("Observation: the dataset records Country, but not individual age or gender; customer demographics cannot be computed from this source.")
    print("Observation: the dataset has item descriptions and stock codes, but no product-category field; category revenue cannot be inferred reliably.")
    df.groupby("Product").Revenue.sum().nlargest(10).sort_values().plot.barh(title="Top 10 products by revenue (GBP)")
    plt.show()
    sns.heatmap(numeric.corr(),annot=True,cmap="vlag",center=0); plt.show()
    print("Actionable recommendations: test replenishment for the top revenue items; evaluate seasonal stock using the monthly series; investigate country concentration before expanding. These are exploratory leads, not causal findings.")


def customer_segmentation() -> None:
    print("DATA PROVENANCE: Customer RFM features computed from UCI Online Retail transactions.")
    transactions=load_online_retail()
    transactions["InvoiceDate"]=pd.to_datetime(transactions["InvoiceDate"],errors="coerce")
    transactions["Quantity"]=pd.to_numeric(transactions["Quantity"],errors="coerce")
    transactions["UnitPrice"]=pd.to_numeric(transactions["UnitPrice"],errors="coerce")
    transactions["InvoiceNo"]=transactions["InvoiceNo"].astype("string")
    transactions=transactions.dropna(subset=["CustomerID","InvoiceDate","InvoiceNo"])
    transactions=transactions.loc[
        ~transactions["InvoiceNo"].str.startswith("C",na=False)
        & (transactions["Quantity"]>0)
        & (transactions["UnitPrice"]>0)
    ].copy()
    transactions["Revenue"]=transactions["Quantity"]*transactions["UnitPrice"]
    snapshot=transactions["InvoiceDate"].max().normalize()+pd.Timedelta(days=1)
    df=transactions.groupby("CustomerID").agg(
        Recency=("InvoiceDate",lambda values:(snapshot-values.max().normalize()).days),
        Frequency=("InvoiceNo","nunique"),
        Monetary=("Revenue","sum"),
    ).reset_index()
    df["AveragePurchaseValue"] = df["Monetary"] / df["Frequency"]
    df["HistoricalSpendProxy"] = df["Monetary"]
    report(df)
    print("Per-customer averages (GBP except invoice frequency):\n",
          df[["AveragePurchaseValue", "Frequency", "HistoricalSpendProxy"]].mean().round(2))
    print("Historical spend is only a same-period proxy, not predictive customer lifetime value.")
    features=df[["Recency","Frequency","Monetary"]]
    scaled=StandardScaler().fit_transform(features)
    from sklearn.cluster import KMeans
    inertias=[]
    k_values=np.arange(1,9)
    for k in k_values:
        inertias.append(KMeans(n_clusters=k,n_init=10,random_state=SEED).fit(scaled).inertia_)
    normalized_x=(k_values-k_values.min())/(k_values.max()-k_values.min())
    inertia_values=np.asarray(inertias)
    normalized_y=(inertia_values-inertia_values.min())/(inertia_values.max()-inertia_values.min())
    start=np.array([normalized_x[0],normalized_y[0]])
    end=np.array([normalized_x[-1],normalized_y[-1]])
    distances=np.abs(
        (end[0]-start[0])*(start[1]-normalized_y)
        -(start[0]-normalized_x)*(end[1]-start[1])
    )/np.hypot(*(end-start))
    selected_k=int(k_values[1:-1][np.argmax(distances[1:-1])])
    plt.plot(k_values,inertias,marker="o")
    plt.axvline(selected_k,color="red",linestyle="--",label=f"Selected k={selected_k}")
    plt.title("Elbow method"); plt.xlabel("k"); plt.ylabel("Inertia"); plt.legend(); plt.show()
    print(f"Selected k={selected_k} using the maximum-distance elbow heuristic on standardized RFM features.")
    model=KMeans(n_clusters=selected_k,n_init=10,random_state=SEED)
    df["Cluster"]=model.fit_predict(scaled)
    fig,axes=plt.subplots(1,2,figsize=(12,5))
    sns.scatterplot(data=df,x="Recency",y="Monetary",hue="Cluster",palette="tab10",ax=axes[0])
    sns.scatterplot(data=df,x="Frequency",y="Monetary",hue="Cluster",palette="tab10",ax=axes[1])
    plt.show()
    profile=df.groupby("Cluster")[["Recency","Frequency","Monetary"]].mean().round(1)
    print("Cluster profiles:\n",profile)
    df.Cluster.value_counts().sort_index().plot.bar(title="Customers per segment"); plt.show()
    for cluster,row in profile.iterrows():
        segment="loyal/high-value" if row.Monetary>profile.Monetary.median() and row.Frequency>profile.Frequency.median() else "needs re-engagement" if row.Recency>profile.Recency.median() else "steady/occasional"
        print(f"Cluster {cluster}: {segment}; tailor a test offer, then evaluate incremental lift.")


def clean_data() -> None:
    print("DATA PROVENANCE: 5,000-row sample from UCI Online Retail; deliberate corruption is applied reproducibly for this cleaning exercise.")
    source=load_online_retail()
    raw=source.sample(n=min(5000,len(source)),random_state=SEED).reset_index(drop=True)
    raw=raw.rename(columns={"InvoiceNo":"invoice_id","StockCode":"product_id","Description":"description",
        "Quantity":"quantity","InvoiceDate":"invoice_date","UnitPrice":"unit_price","CustomerID":"customer_id"})
    # Introduce visible, documented defects to a copy of public source rows.
    dirty=raw.copy()
    dirty["invoice_id"]=dirty["invoice_id"].astype("string")
    dirty["description"]=dirty["description"].astype("string")
    dirty["invoice_date"]=dirty["invoice_date"].astype("string")
    dirty["unit_price"]=dirty["unit_price"].astype("string")
    dirty.loc[dirty.index[:20],"description"]=dirty.loc[dirty.index[:20],"description"].str.lower().str.strip()
    dirty.loc[dirty.index[20:30],"invoice_date"]="not-a-date"
    dirty.loc[dirty.index[30:40],"unit_price"]="unknown"
    dirty.loc[dirty.index[40:55],"customer_id"]=np.nan
    dirty=pd.concat([dirty,dirty.iloc[:25]],ignore_index=True)
    expected_types={"invoice_id":"string","product_id":"string","description":"string",
        "quantity":"int64","invoice_date":"datetime64[ns]","unit_price":"float64","customer_id":"string"}
    expected_types["quantity"] = "int64" if pd.api.types.is_integer_dtype(raw["quantity"]) else "float64"
    def dtype_accuracy(frame):
        return sum(str(frame[column].dtype)==dtype for column,dtype in expected_types.items())
    numeric_raw=dirty.copy()
    numeric_raw["quantity"]=pd.to_numeric(numeric_raw["quantity"],errors="coerce")
    numeric_raw["unit_price"]=pd.to_numeric(numeric_raw["unit_price"],errors="coerce")
    quality={
        "nulls_by_column":dirty.isna().sum(),
        "duplicate_rows":int(dirty.duplicated().sum()),
        "invalid_dates":int(pd.to_datetime(dirty["invoice_date"],errors="coerce").isna().sum()),
        "invalid_unit_prices":int(pd.to_numeric(dirty["unit_price"],errors="coerce").isna().sum()),
        "negative_quantities":int((numeric_raw["quantity"]<0).sum()),
        "dtype_accuracy":dtype_accuracy(dirty),
    }
    print("Before-cleaning quality report:\nNulls by column:\n",quality["nulls_by_column"])
    print("Exact duplicates:",quality["duplicate_rows"],"| invalid dates:",quality["invalid_dates"],
          "| invalid unit prices:",quality["invalid_unit_prices"],"| dtype accuracy:",
          f'{quality["dtype_accuracy"]}/{len(expected_types)}')
    df=dirty.drop_duplicates().copy()
    df["invoice_id"]=df["invoice_id"].astype("string")
    df["product_id"]=df["product_id"].astype("string").str.strip()
    df["description"]=df["description"].astype("string").str.strip().str.replace(r"\s+"," ",regex=True)
    df["customer_id"]=df["customer_id"].astype("string").str.replace(r"\.0$","",regex=True)
    df["invoice_date"]=pd.to_datetime(df["invoice_date"],errors="coerce")
    df["quantity"]=pd.to_numeric(df["quantity"],errors="coerce")
    df["unit_price"]=pd.to_numeric(df["unit_price"],errors="coerce")
    # An invoice with no parseable date cannot be placed in time-series analyses.
    invalid_date_rows=int(df["invoice_date"].isna().sum())
    df=df.dropna(subset=["invoice_date"])
    # Missing customer IDs are not imputed: an invented ID would corrupt RFM/customer counts.
    missing_customers=int(df["customer_id"].isna().sum())
    df["description"]=df["description"].fillna("Unknown product")
    df["quantity"]=df["quantity"].fillna(df["quantity"].median())
    df["unit_price"]=df["unit_price"].fillna(df["unit_price"].median())
    outlier_counts={}
    for column in ("quantity","unit_price"):
        q1,q3=df[column].quantile([.25,.75]); iqr=q3-q1
        outlier_counts[column]=int(((df[column]<q1-1.5*iqr)|(df[column]>q3+1.5*iqr)).sum())
    # Negative quantities and unusual prices can represent returns/bulk purchases; flag,
    # retain, and require business review instead of silently deleting valid transactions.
    expected_types["invoice_date"]="datetime64[ns]"
    expected_types["customer_id"]="string"
    after_nulls=int(df.isna().sum().sum())
    after_duplicate_count=int(df.duplicated().sum())
    summary=pd.DataFrame({
        "before":[len(dirty),int(dirty.isna().sum().sum()),quality["duplicate_rows"],f'{quality["dtype_accuracy"]}/{len(expected_types)}'],
        "after":[len(df),after_nulls,after_duplicate_count,f'{dtype_accuracy(df)}/{len(expected_types)}'],
    },index=["rows","null_cells","duplicate_rows","dtype_accuracy"])
    print("Cleaning decisions: remove exact duplicates; parse dates and discard the 10 deliberately invalid-date rows; retain customer IDs as nullable strings rather than inventing IDs; normalize whitespace; median-impute the 10 deliberately invalid unit prices; retain legitimate returns and IQR-flag unusual values for review.")
    print("Dropped for invalid dates:",invalid_date_rows,"; missing customer IDs retained:",missing_customers)
    print("IQR outliers retained for review:",outlier_counts)
    print("Before vs after summary:\n",summary)
    print("Final data types:\n",df.dtypes)
    path=OUT_DIR/"cleaned_online_retail_sample.csv"
    df.to_csv(path,index=False)
    print("Saved cleaned sample:",path)
    print(df.head().to_string(index=False))


def sentiment_analysis() -> None:
    if not PHRASEBANK_PATH.exists():
        raise FileNotFoundError(f"Download Financial PhraseBank using build_notebooks.py; expected {PHRASEBANK_PATH}.")
    rows=[]
    for line in PHRASEBANK_PATH.read_text(encoding="latin-1").splitlines():
        if "@" in line:
            text,label=line.rsplit("@",1)
            rows.append((label.strip().lower(),text.strip()))
    df=pd.DataFrame(rows,columns=["sentiment","text"]).drop_duplicates()
    print("DATA PROVENANCE: Financial PhraseBank Sentences_AllAgree; financial news, investor-perspective labels; CC BY-NC-SA 3.0.")
    report(df)
    print("Class distribution:\n",df["sentiment"].value_counts())
    df.sentiment.value_counts().plot.bar(title="Sentiment distribution"); plt.show()
    x_train,x_test,y_train,y_test=train_test_split(df.text,df.sentiment,test_size=.2,random_state=SEED,stratify=df.sentiment)
    vectorizer=TfidfVectorizer(lowercase=True,stop_words="english",strip_accents="unicode",
                               token_pattern=r"(?u)\b\w\w+\b",ngram_range=(1,2))
    a,b=vectorizer.fit_transform(x_train),vectorizer.transform(x_test)
    results=[score_classifier("Multinomial NB",MultinomialNB(),a,b,y_train,y_test),
             score_classifier("Logistic regression",LogisticRegression(max_iter=500),a,b,y_train,y_test)]
    best=max(results,key=lambda r:r["f1"])
    print(f"Best model by held-out macro-F1: {best['name']} (macro-F1={best['f1']:.3f}).")
    mistakes=pd.DataFrame({"text":x_test,"actual":y_test,"predicted":best["prediction"]})
    mistakes=mistakes[mistakes.actual!=mistakes.predicted].head(5).copy()
    if mistakes.empty:
        print("Error analysis: no misclassifications in this held-out sample.")
    else:
        mistakes["review_note"]=mistakes["text"].apply(
            lambda text: "Check negation or contrast; word-level features can miss context."
            if re.search(r"\b(not|no|never|despite|although|but)\b",text.lower())
            else "Check implicit financial context and subjective label boundaries."
        )
        print("Misclassified examples with review notes:\n",mistakes.to_string(index=False))
    try:
        from wordcloud import WordCloud
        fig,axes=plt.subplots(1,3,figsize=(14,4))
        for axis,label in zip(axes,("positive","negative","neutral")):
            corpus=" ".join(df.loc[df.sentiment==label,"text"])
            axis.imshow(WordCloud(width=500,height=300,background_color="white",collocations=False).generate(corpus))
            axis.set_title(label); axis.axis("off")
        plt.show()
    except ImportError:
        print("Optional wordcloud package unavailable; top-word plots are used instead.")
        for label in df.sentiment.unique():
            words=" ".join(df.loc[df.sentiment==label,"text"]).lower()
            pd.Series(re.findall(r"[a-z]+",words)).value_counts().head(10).sort_values().plot.barh(title=f"Top words: {label}")
            plt.show()
    print("TF-IDF weights terms by local frequency and corpus-wide rarity. This model can support triage of financial news, but the finance-domain labels may not generalize to product reviews or social media.")


def house_prices() -> None:
    if not REAL_ESTATE_PATH.exists():
        raise FileNotFoundError(f"Download UCI Real Estate Valuation using build_notebooks.py; expected {REAL_ESTATE_PATH}.")
    print("DATA PROVENANCE: UCI Real Estate Valuation; historical Sindian District (Taiwan) transaction data.")
    df=pd.read_excel(REAL_ESTATE_PATH,engine="openpyxl")
    df=df.rename(columns={
        "X1 transaction date":"transaction_date",
        "X2 house age":"house_age_years",
        "X3 distance to the nearest MRT station":"distance_mrt_m",
        "X4 number of convenience stores":"convenience_stores",
        "X5 latitude":"latitude",
        "X6 longitude":"longitude",
        "Y house price of unit area":"price_per_ping_10k_twd",
    })
    df=df.drop(columns=["No"],errors="ignore")
    report(df)
    print("Target unit: 10,000 New Taiwan dollars per ping; this historical dataset is not a current sale-price estimate.")
    sns.histplot(df["price_per_ping_10k_twd"],kde=True); plt.title("Historical price per unit area"); plt.show()
    numeric=df.select_dtypes("number")
    sns.heatmap(numeric.corr(),annot=True,cmap="vlag",center=0); plt.title("Feature correlation"); plt.show()
    print("Feature rationale: house age, proximity to transit, convenience-store count, and coordinates may relate to local price per unit area.")
    df["location_zone"]=pd.cut(df["longitude"],bins=3,labels=["west","central","east"])
    x=pd.get_dummies(df.drop(columns="price_per_ping_10k_twd"),columns=["location_zone"],drop_first=True,dtype=float)
    y=df["price_per_ping_10k_twd"]
    x_train,x_test,y_train,y_test=train_test_split(x,y,test_size=.2,random_state=SEED)
    result=score_regressor("Linear Regression",LinearRegression(),x_train,x_test,y_train,y_test)
    print("Linear Regression MSE:", result["rmse"] ** 2)
    score_regressor("Ridge",__import__("sklearn.linear_model",fromlist=["Ridge"]).Ridge(alpha=1.0),x_train,x_test,y_train,y_test)
    pred=result["prediction"]; plt.scatter(y_test,pred,alpha=.6); lim=[min(y_test.min(),pred.min()),max(y_test.max(),pred.max())]; plt.plot(lim,lim,"r--"); plt.title("Actual vs predicted"); plt.show()
    sns.scatterplot(x=pred,y=y_test-pred); plt.axhline(0,color="red"); plt.title("Residuals"); plt.show()
    print("Largest coefficients:\n",pd.Series(result["model"].coef_,index=x.columns).sort_values(key=abs,ascending=False).head(8))


def wine_quality() -> None:
    data=DATA_DIR/"winequality-red.csv"
    if not data.exists():
        raise FileNotFoundError(f"Download UCI Wine Quality data to {data}; see DATA ANALYTICS/README.md.")
    df=pd.read_csv(data,sep=";")
    report(df)
    feature_columns=[column for column in df.select_dtypes("number").columns if column!="quality"]
    figure,axes=plt.subplots(4,3,figsize=(14,12))
    for axis,column in zip(axes.flat,feature_columns):
        sns.histplot(data=df,x=column,kde=True,ax=axis)
        axis.set_title(f"Distribution: {column}")
    for axis in axes.flat[len(feature_columns):]:
        axis.set_visible(False)
    figure.tight_layout(); plt.show()
    df.quality.value_counts().sort_index().plot.bar(title="Wine quality class counts"); plt.show()
    print("Quality score proportions (%):\n",df.quality.value_counts(normalize=True).sort_index().mul(100).round(1))
    print("Class imbalance: quality scores near the dataset's centre are more common; accuracy can conceal poor minority-class recall.")
    df["quality_group"]=pd.cut(df.quality,bins=[0,5,6,10],labels=["low","medium","high"])
    x_train,x_test,y_train,y_test=train_test_split(df.drop(columns=["quality","quality_group"]),df.quality_group,test_size=.2,random_state=SEED,stratify=df.quality_group)
    results=[]
    for name,estimator in [
      ("Random Forest",RandomForestClassifier(n_estimators=200,class_weight="balanced",random_state=SEED)),
      ("SGD",Pipeline([("scale",StandardScaler()),("model",SGDClassifier(class_weight="balanced",random_state=SEED,max_iter=2000,tol=1e-3))])),
      ("SVC",Pipeline([("scale",StandardScaler()),("model",SVC(class_weight="balanced"))])),
    ]: results.append(score_classifier(name,estimator,x_train,x_test,y_train,y_test))
    print(pd.DataFrame([{"model":r["name"],"accuracy":r["accuracy"],"macro_f1":r["f1"]} for r in results]).sort_values("macro_f1",ascending=False))
    importances=results[0]["model"].feature_importances_
    pd.Series(importances,index=x_train.columns).nlargest(8).sort_values().plot.barh(title="Tree feature importance"); plt.show()
    print("Select a model using per-class recall, macro-F1, calibration, and deployment cost—not accuracy alone.")


def fraud_detection() -> None:
    print("DATA PROVENANCE: Synthetic imbalanced transactions (1% fraud); no real financial records.")
    rng=np.random.default_rng(SEED); n=6000
    fraud=rng.binomial(1,.01,n)
    amount=np.where(fraud==1,rng.lognormal(5,1,n),rng.lognormal(3.2,1.1,n))
    hour=rng.integers(0,24,n); unusual=rng.normal(fraud*1.1,1,n)
    df=pd.DataFrame({"amount":amount,"hour":hour,"deviation":unusual,"fraud":fraud})
    print("Fraud share (%):",df.fraud.mean()*100)
    sns.boxplot(data=df,x="fraud",y="amount"); plt.yscale("log"); plt.title("Amount by class (log scale)"); plt.show()
    df.assign(time_band=pd.cut(df.hour,[-1,5,11,17,23],labels=["night","morning","afternoon","evening"])).groupby("time_band",observed=True).fraud.mean().plot.bar(title="Fraud rate by time band"); plt.show()
    print("Accuracy is misleading: a model predicting every record non-fraud reaches 99% accuracy here while catching zero fraud.")
    x_train,x_test,y_train,y_test=train_test_split(df.drop(columns="fraud"),df.fraud,test_size=.25,random_state=SEED,stratify=df.fraud)
    from sklearn.tree import DecisionTreeClassifier
    models=[("Logistic Regression",Pipeline([("scale",StandardScaler()),("model",LogisticRegression(class_weight="balanced",max_iter=1000))])),
            ("Decision Tree",DecisionTreeClassifier(class_weight="balanced",max_depth=5,random_state=SEED))]
    results=[]
    for name,model in models:
        model.fit(x_train,y_train); prob=model.predict_proba(x_test)[:,1]; pred=(prob>=.5).astype(int)
        print(name,{"precision":precision_score(y_test,pred,zero_division=0),"recall":recall_score(y_test,pred),"f1":f1_score(y_test,pred),"roc_auc":roc_auc_score(y_test,prob)})
        results.append((name,prob,model))
    logistic = results[0][2].named_steps["model"]
    print("Logistic-regression coefficients:\n", pd.Series(logistic.coef_[0], index=x_train.columns).sort_values(key=abs, ascending=False))
    for name,prob,_ in results:
        fpr,tpr,_=roc_curve(y_test,prob); plt.plot(fpr,tpr,label=name)
    plt.plot([0,1],[0,1],"k--"); plt.legend(); plt.title("ROC curves"); plt.show()
    print("Recall reduces missed fraud; precision controls investigation load. A deployment needs a cost-sensitive threshold and streaming/batch capacity tests.")
    print("At 1M transactions/hour, use partitioned streaming ingestion, online feature computation, model serving, queue-based review, and drift/latency monitoring.")


def play_store() -> None:
    app_path=DATA_DIR/"google_play_apps.csv"
    review_path=DATA_DIR/"google_play_user_reviews.csv"
    if not app_path.exists() or not review_path.exists():
        raise FileNotFoundError(
            "Download the licensed Play Store datasets using build_notebooks.py; "
            f"expected {app_path} and {review_path}."
        )
    print("DATA PROVENANCE: Google Play app metadata and user-review sentiment dataset; collected in 2018.")
    apps=pd.read_csv(app_path)
    reviews=pd.read_csv(review_path)
    print("Raw app data:")
    report(apps)
    apps["Category"]=apps["Category"].astype("string").str.strip()
    valid_categories=apps["Category"].str.fullmatch(r"[A-Z_]+",na=False)
    invalid_category_rows=int((~valid_categories).sum())
    apps=apps.loc[valid_categories].copy()
    apps["Rating"]=pd.to_numeric(apps["Rating"],errors="coerce")
    apps["Reviews"]=pd.to_numeric(apps["Reviews"],errors="coerce")
    installs=apps["Installs"].astype("string").str.replace(r"[^0-9]","",regex=True)
    apps["InstallCountFloor"]=pd.to_numeric(installs,errors="coerce")
    prices=apps["Price"].astype("string").str.replace(r"[^0-9.]","",regex=True)
    apps["Price"]=pd.to_numeric(prices,errors="coerce")
    size_text=apps["Size"].astype("string").str.strip()
    size_values=pd.to_numeric(size_text.str.extract(r"^([\d.]+)")[0],errors="coerce")
    size_units=size_text.str.extract(r"([KMG])",flags=re.IGNORECASE)[0].str.upper()
    size_factor=size_units.map({"K":1/1024,"M":1.0,"G":1024.0}).fillna(1.0)
    apps["Size_MB"]=size_values*size_factor
    apps["Type"]=apps["Type"].astype("string").str.strip().str.title()
    apps["Last Updated Parsed"]=pd.to_datetime(apps["Last Updated"],errors="coerce")
    invalid_rows=int((~apps["Type"].isin(["Free","Paid"])|apps["InstallCountFloor"].isna()
                      |apps["Price"].isna()).sum())
    apps=apps.loc[apps["Type"].isin(["Free","Paid"])&apps["InstallCountFloor"].notna()
                  &apps["Price"].notna()].copy()
    invalid_ratings=int((apps["Rating"].notna()&~apps["Rating"].between(1,5)).sum())
    apps=apps.loc[apps["Rating"].isna()|apps["Rating"].between(1,5)].copy()
    apps=apps.sort_values("Last Updated Parsed",kind="stable",na_position="first")
    duplicate_rows=int(apps.duplicated(subset="App",keep="last").sum())
    apps=apps.drop_duplicates(subset="App",keep="last").copy()
    apps["InstallCountFloor"]=apps["InstallCountFloor"].astype("int64")
    apps["RevenueFloorProxy"]=apps["Price"]*apps["InstallCountFloor"]
    print(f"Invalid category rows excluded: {invalid_category_rows}")
    print(f"Invalid type/install/price rows excluded: {invalid_rows}; invalid ratings excluded: {invalid_ratings}.")
    print(f"Duplicate app rows removed: {duplicate_rows}; unique app records retained: {len(apps):,}.")
    print("Missing values after cleaning:\n",apps[["Rating","Size_MB"]].isna().sum())
    category_counts=apps.Category.value_counts()
    category_counts.sort_values().plot.barh(title="Apps by category"); plt.show()
    rating_data=apps["Rating"].dropna()
    sns.histplot(rating_data,bins=20,kde=True)
    plt.title("App rating distribution (1–5)"); plt.xlabel("Rating"); plt.show()
    (apps.groupby("Category").Rating.mean().dropna().sort_values()
     .plot.barh(title="Average app rating by category"))
    plt.xlabel("Average rating (1–5)"); plt.show()
    size_install=apps.dropna(subset=["Size_MB","InstallCountFloor"]).query(
        "Size_MB > 0 and InstallCountFloor > 0")
    sns.scatterplot(data=size_install,x="Size_MB",y="InstallCountFloor",hue="Type",alpha=.6)
    plt.yscale("log"); plt.title("App size vs install-count bucket"); plt.show()
    size_install_rho=size_install[["Size_MB","InstallCountFloor"]].corr(method="spearman").iloc[0,1]
    print(f"Size/install monotonic association (Spearman rho={size_install_rho:.3f}, n={len(size_install):,}); bucketed installs do not establish causality.")
    apps.Type.value_counts().plot.pie(autopct="%1.0f%%",title="Free vs paid apps"); plt.ylabel(""); plt.show()
    paid=apps.loc[(apps["Type"]=="Paid")&(apps["Price"]>0),"Price"]
    sns.histplot(paid,bins=20)
    plt.title("Listed price distribution for paid apps"); plt.xlabel("Listed price (USD)"); plt.show()
    apps.groupby("Category").RevenueFloorProxy.sum(min_count=1).sort_values().tail(10).plot.barh(
        title="Top categories by listed price × install-floor proxy")
    plt.xlabel("Illustrative USD lower-bound proxy (not observed revenue)"); plt.show()

    reviews=reviews.dropna(subset=["Review","Sentiment Category"]).copy()
    reviews["source_sentiment"]=reviews["Sentiment Category"].astype("string").str.strip().str.lower()
    reviews=reviews.loc[reviews["source_sentiment"].isin(["positive","negative","neutral"])]
    category_map=apps[["App","Category"]].drop_duplicates("App")
    reviews=reviews.merge(category_map,on="App",how="inner",validate="many_to_one")
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    analyzer=SentimentIntensityAnalyzer()
    reviews["vader_compound"]=reviews["Review"].astype(str).map(
        lambda text: analyzer.polarity_scores(text)["compound"])
    reviews["sentiment"]=np.select(
        [reviews["vader_compound"]>=.05,reviews["vader_compound"]<=-.05],
        ["positive","negative"],default="neutral")
    print(f"Reviews with text and source sentiment labels, matched to a cleaned app category: {len(reviews):,}.")
    print("VADER assigns positive/neutral/negative labels using compound-score cutoffs of +0.05/-0.05.")
    print("Agreement with the source-provided labels (reference only; not an independent gold-standard test):",
          f'{(reviews["sentiment"]==reviews["source_sentiment"]).mean():.3f}')
    reviews.sentiment.value_counts().reindex(["positive","neutral","negative"]).plot.bar(
        title="VADER review sentiment labels")
    plt.ylabel("Review count"); plt.show()
    top_categories=reviews.Category.value_counts().head(10).index
    sentiment_by_category=pd.crosstab(
        reviews.loc[reviews.Category.isin(top_categories),"Category"],
        reviews.loc[reviews.Category.isin(top_categories),"sentiment"],
        normalize="index",
    ).reindex(columns=["positive","neutral","negative"],fill_value=0)
    sentiment_by_category.plot.bar(stacked=True,color=["#168f86","#a8b7c2","#ed725b"])
    plt.ylabel("Share of labeled reviews"); plt.title("VADER sentiment mix in 10 most-reviewed categories")
    plt.legend(title="VADER label"); plt.tight_layout(); plt.show()
    print("Limitations: 2018 snapshot, install counts are buckets, revenue proxy is not observed revenue, and reviews may not represent all users.")
    saturation_category=category_counts.idxmax()
    saturation_share=category_counts.max()/category_counts.sum()*100
    average_ratings=apps.groupby("Category").Rating.agg(["mean","count"]).dropna().sort_values("mean")
    positive_share=sentiment_by_category["positive"]
    eligible=positive_share.loc[reviews.Category.value_counts().reindex(positive_share.index).fillna(0)>=20]
    sentiment_category=eligible.idxmax() if not eligible.empty else "insufficient review coverage"
    print(f"Insight 1: {saturation_category} is the most represented category ({saturation_share:.1f}% of cleaned apps); a new app would need a clear differentiator.")
    if not average_ratings.empty:
        highest_rating=average_ratings.iloc[-1]
        print(f"Insight 2: {average_ratings.index[-1]} has the highest mean rating ({highest_rating['mean']:.2f}, n={int(highest_rating['count'])}); validate with rating volume and variance.")
    if sentiment_category!="insufficient review coverage":
        print(f"Insight 3: {sentiment_category} has the highest VADER-positive share among categories with at least 20 matched reviews ({positive_share[sentiment_category]:.1%}); investigate its review themes.")
    else:
        print("Insight 3: No category had enough matched reviews for a stable sentiment comparison.")
    print("Recommendations: differentiate rather than enter the most saturated category by default; inspect low-rating and negative-review themes; treat install-floor revenue as a screening proxy, not a forecast.")


def levenshtein(a: str, b: str) -> int:
    previous=list(range(len(b)+1))
    for i,ca in enumerate(a,1):
        current=[i]
        for j,cb in enumerate(b,1):
            current.append(min(current[-1]+1,previous[j]+1,previous[j-1]+(ca!=cb)))
        previous=current
    return previous[-1]


def autocomplete_analysis() -> None:
    corpus_path = DATA_DIR / "alice_adventures.txt"
    if corpus_path.exists():
        corpus = corpus_path.read_text(encoding="utf-8", errors="replace")
        print("DATA PROVENANCE: Project Gutenberg public-domain text, Alice's Adventures in Wonderland.")
    else:
        corpus=("the quick brown fox jumps over the lazy dog. " * 120 + "a good morning starts with a warm cup of tea. " * 80 +
           "data science helps people understand patterns in data. " * 100 + "the weather is sunny and the day is bright. " * 90)
        print("DATA PROVENANCE: Small synthetic fallback corpus; no real-world language claims.")
    raw_tokens=re.findall(r"[a-z]+",corpus.lower())
    stop_words={"a","an","and","are","as","at","be","by","for","from","in","is","it","of","on","or","that","the","to","was","with"}
    tokens=[token for token in raw_tokens if token not in stop_words]
    from collections import Counter,defaultdict
    split_at=max(1,int(len(tokens)*.8))
    training_tokens=tokens[:split_at]
    evaluation_tokens=tokens[split_at:]
    unigram=Counter(training_tokens); bigram=defaultdict(Counter)
    for left,right in zip(training_tokens,training_tokens[1:]): bigram[left][right]+=1
    print(f"Corpus tokens: {len(tokens):,}; chronological training/evaluation split: {len(training_tokens):,}/{len(evaluation_tokens):,}.")
    prefix_cases=[("ali","alice"),("rab","rabbit"),("won","wonder"),("que","queen"),("cur","curious"),
                  ("lit","little"),("whi","white"),("tur","turtle"),("hat","hatter"),("gar","garden")]
    print("Top 3 completions by character prefix (training corpus):")
    completion_predictions = []
    for prefix, expected in prefix_cases:
        candidates=Counter({word:count for word,count in unigram.items() if word.startswith(prefix)})
        top = [word for word, _ in candidates.most_common(3)]
        completion_predictions.append((prefix, expected, top))
        print(prefix,top)
    completion_hits=sum(expected in top for _, expected, top in completion_predictions)
    predicted_count=sum(len(top) for _, _, top in completion_predictions)
    print(f"Prefix completion precision@3={completion_hits/predicted_count:.3f}; "
          f"recall@3={completion_hits/len(prefix_cases):.3f} on the fixed prefix set.")
    if len(evaluation_tokens)>1:
        contexts=evaluation_tokens[:-1]
        expected_next=evaluation_tokens[1:]
        global_top=[word for word,_ in unigram.most_common(3)]
        global_hits=sum(expected in global_top for expected in expected_next)
        conditional_hits=0
        for context,expected in zip(contexts,expected_next):
            candidates=bigram[context].most_common(3) or unigram.most_common(3)
            conditional_hits+=expected in {word for word,_ in candidates}
        denominator=3*len(expected_next)
        print(f"Next-word frequency baseline precision@3={global_hits/denominator:.4f}, recall@3={global_hits/len(expected_next):.4f}.")
        print(f"Conditional bigram precision@3={conditional_hits/denominator:.4f}, recall@3={conditional_hits/len(expected_next):.4f}.")
    vocabulary=sorted(unigram)
    def correct(word: str) -> str:
        if word in unigram: return word
        distances=[(levenshtein(word,candidate),-unigram[candidate],candidate) for candidate in vocabulary]
        return min(distances)[2]
    from difflib import get_close_matches
    def correct_by_similarity(word: str) -> str:
        if word in unigram: return word
        matches=get_close_matches(word,vocabulary,n=1,cutoff=0)
        return matches[0] if matches else word
    pairs=[("alicee","alice"),("rabitt","rabbit"),("wondr","wonder"),("queeen","queen"),("curous","curious"),
           ("littel","little"),("whitte","white"),("turtel","turtle"),("hatterr","hatter"),("gardn","garden"),
           ("dormousee","dormouse"),("gryphonn","gryphon"),("marchh","march"),("tabble","table"),
           ("cheshiree","cheshire"),("caterpilar","caterpillar"),("duchesss","duchess"),("kingg","king"),
           ("rabbitt","rabbit"),("wonderlandd","wonderland")]
    results=[(wrong,expected,correct(wrong),correct_by_similarity(wrong)) for wrong,expected in pairs]
    print(pd.DataFrame(results,columns=["misspelling","expected","Levenshtein","SequenceMatcher"]).to_string(index=False))
    labels_expected=[expected for _,expected,_,_ in results]
    levenshtein_predictions=[pred for _,_,pred,_ in results]
    similarity_predictions=[pred for _,_,_,pred in results]
    for name,predictions in (("Levenshtein",levenshtein_predictions),("SequenceMatcher",similarity_predictions)):
        hits=sum(pred==expected for expected,pred in zip(labels_expected,predictions))
        precision=precision_score(labels_expected,predictions,average="micro",zero_division=0)
        recall=recall_score(labels_expected,predictions,average="micro",zero_division=0)
        print(f"{name} exact-match accuracy={hits}/{len(results)} ({hits/len(results):.2%}); micro precision={precision:.2f}, recall={recall:.2f}.")
    matrix_labels=sorted(set(labels_expected)|set(levenshtein_predictions))
    matrix=confusion_matrix(labels_expected,levenshtein_predictions,labels=matrix_labels)
    plt.figure(figsize=(12, 10))
    sns.heatmap(matrix,xticklabels=matrix_labels,yticklabels=matrix_labels,cmap="Blues",cbar=False)
    plt.title("Levenshtein autocorrect confusion matrix (expected vs predicted)")
    plt.xticks(rotation=90); plt.yticks(rotation=0); plt.tight_layout(); plt.show()
    pd.Series(unigram).nlargest(20).sort_values().plot.barh(title="Top 20 corpus words"); plt.show()
    print("Comparison: global frequency uses the most common next tokens; the bigram model conditions on the previous token. Levenshtein ranks edit distance, while SequenceMatcher ranks character similarity.")
    print("Limitations: this single-book corpus and fixed spelling list are small; correction is vocabulary-bound, lacks user/keyboard context, and can mishandle ambiguous edits.")


TASKS = {
    "DS1": ("Iris flower classification", iris_classification),
    "DS2": ("Unemployment analysis", unemployment_analysis),
    "DS3": ("Car price prediction", car_price_prediction),
    "DS4": ("SMS spam detection", spam_detection),
    "DS5": ("Advertising sales prediction", sales_prediction),
    "DA1": ("Retail sales EDA", retail_eda),
    "DA2": ("Customer segmentation", customer_segmentation),
    "DA3": ("Professional data cleaning", clean_data),
    "DA4": ("Sentiment analysis", sentiment_analysis),
    "DA5": ("House price regression", house_prices),
    "DA6": ("Wine quality classification", wine_quality),
    "DA7": ("Fraud detection", fraud_detection),
    "DA8": ("Play Store market analysis", play_store),
    "DA9": ("Autocomplete and autocorrect", autocomplete_analysis),
}


def run_task(code: str) -> None:
    if code not in TASKS:
        raise ValueError(f"Unknown notebook task {code!r}. Available: {', '.join(TASKS)}")
    title, task = TASKS[code]
    print(f"{title}\n{'=' * len(title)}")
    task()
