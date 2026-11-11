# Data Analytics

Nine separate notebooks are grouped by the PDF's levels:

- **Level 1:** [Retail EDA](./Level%201/01_retail_sales_eda.ipynb), [RFM customer
  segmentation](./Level%201/02_customer_segmentation.ipynb), [data cleaning](./Level%201/03_cleaning_data.ipynb),
  [sentiment analysis](./Level%201/04_sentiment_analysis.ipynb).
- **Level 2:** [house-price regression](./Level%202/01_house_price_regression.ipynb),
  [UCI wine-quality classification](./Level%202/02_wine_quality_prediction.ipynb),
  [fraud detection](./Level%202/03_fraud_detection.ipynb), [Play Store market analysis](./Level%202/04_play_store_analysis.ipynb),
  [autocomplete/autocorrect](./Level%202/05_autocomplete_autocorrect.ipynb).

For provenance and repeatable setup, see [Data Science](../DATA%20SCIENCE/README.md)
and [dataset sources](../DATA%20SCIENCE/data/SOURCES.md). Public UCI Online Retail records
drive retail EDA, RFM analysis, and a documented messy-data exercise; Financial PhraseBank
provides labelled financial sentiment; UCI Real Estate Valuation provides historical sale
prices. The UCI retail source has no demographic/product-category columns, so those
specific slices remain unavailable. The Play Store workflow uses a pinned 2018 app/review
snapshot under CC BY 3.0; install counts are buckets and review labels are source-provided.
Any remaining synthetic data is for workflow demonstration only; the unemployment and
fraud exercises use no real-world records.
