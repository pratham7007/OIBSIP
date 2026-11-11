# Dataset sources and limitations

| Dataset | Download/source | Use | License/provenance note |
|---|---|---|---|
| Online Retail | [UCI dataset 352](https://archive.ics.uci.edu/dataset/352/online+retail) | Retail sales, customer RFM, and intentionally dirtied cleaning sample | UCI dataset page; British online-retail transactions from 2010–2011. Columns do not include age, gender, or category. |
| Financial PhraseBank | [Dataset card and archive](https://huggingface.co/datasets/takala/financial_phrasebank) | Three-class financial text sentiment | CC BY-NC-SA 3.0; use `Sentences_AllAgree.txt`; cite Malo et al. (2014), DOI: 10.1002/asi.23062. Non-commercial/share-alike terms apply. |
| Real Estate Valuation | [UCI dataset 477](https://archive.ics.uci.edu/dataset/477/real+estate+valuation+data+set) | House-price regression | 414 historical transactions in Sindian District, Taiwan. Target is unit price per 10,000 New Taiwan dollars per ping; it is not a current valuation. |
| SMS Spam Collection | [UCI dataset 228](https://archive.ics.uci.edu/dataset/228/sms+spam+collection) | Binary spam classification | Public UCI labelled SMS collection. |
| Wine Quality | [UCI dataset 186](https://archive.ics.uci.edu/dataset/186/wine+quality) | Wine quality classification | Public UCI red-wine chemistry/quality measurements. |
| Advertising | [ISLR data](https://www.statlearning.com/s/Advertising.csv) | Advertising spend/sales regression | Classic 200-observation teaching dataset; associated with *An Introduction to Statistical Learning*. |
| Google Play apps and user reviews | [Pinned public repository revision](https://github.com/KamgangAnthony/The-Android-App-Market-on-Google-Play/tree/f605ed273d131a8661706ef4c9335b0961d74707) | App-market EDA and VADER review-sentiment summaries | Attribute the repository author, KamgangAnthony, and link the pinned source; the repository includes a CC BY 3.0 license. The snapshot is historical (2018); install counts are buckets, revenue is not observed, and source sentiment labels are used only as a comparison reference. |
| Alice's Adventures in Wonderland | [Project Gutenberg ebook 11](https://www.gutenberg.org/ebooks/11) | Autocomplete/autocorrect corpus | Public-domain text in the United States; confirm local law before redistribution elsewhere. |

The unemployment notebook's synthetic values are not an acceptable substitute for a
verified state-by-month Indian unemployment source. The car-price and fraud examples
remain synthetic unless suitable sources are supplied. The Play Store workflow uses the
cited public 2018 snapshot, but its age and limitations prevent current-market claims.
These limitations are stated rather than hidden.
