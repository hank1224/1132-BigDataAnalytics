# Amazon Review Data Ingestion and NLP Pipeline - Code Description

This project contains two Python scripts that work together to process Amazon product review data and store it in MongoDB.  Here's a breakdown of what each script does and the resulting data structure.

## Scripts Overview

1.  **`mongodb_ingestion.py`**:
    *   **Downloads Data:** If the Amazon review data CSV file isn't found locally, this script automatically downloads it from Kaggle.
    *   **Imports to MongoDB:**  Takes the review data from the CSV file and loads it into a MongoDB database and collection you specify. It handles large files by processing data in chunks.
    *   **Sets Up Initial Database:** Creates basic indexes in MongoDB to make initial data queries faster.

2.  **`mongodb_nlp_processing.py`**:
    *   **Analyzes Review Text (NLP):** Connects to the MongoDB database created by the first script and performs Natural Language Processing (NLP) on the review text (`Text` field).
    *   **Adds NLP Features:**  Extracts various NLP features from the review text and adds them as new fields to each review document in MongoDB. These features include:
        *   Cleaned text
        *   Tokens (words)
        *   Lemmas (base forms of words)
        *   Part-of-Speech tags
        *   Named Entities recognized in the text
        *   Sentiment Score (positive/negative/neutral)
        *   Keywords
    *   **Indexes NLP Data:** Creates indexes on these new NLP fields in MongoDB, making it efficient to search and filter reviews based on their NLP analysis.

## Execution

Run the scripts in this order:

1.  **`mongodb_ingestion.py`**:
    ```bash
    python mongodb_ingestion.py
    ```

2.  **`mongodb_nlp_processing.py`**:
    ```bash
    python mongodb_nlp_processing.py
    ```

## Data Format in MongoDB after Execution

After running both scripts, your MongoDB collection will contain documents representing Amazon reviews. Each document will have the following structure:

**Original Fields (from CSV data, ingested by `mongodb_ingestion.py`):**

*   **`ProductId`**:  (String) Unique identifier of the product.
*   **`UserId`**: (String) Unique identifier of the user who wrote the review.
*   **`ProfileName`**: (String) Name of the user.
*   **`HelpfulnessNumerator`**: (Integer) Number of users who found the review helpful.
*   **`HelpfulnessDenominator`**: (Integer) Total number of users who rated the review helpfulness.
*   **`Score`**: (Integer) Rating given to the product (e.g., 1 to 5 stars).
*   **`Time`**: (Integer) Unix timestamp of when the review was written.
*   **`Summary`**: (String) Summary of the review.
*   **`Text`**: (String) Full text of the review.

**NLP Fields (added by `mongodb_nlp_processing.py`):**

*   **`Text_cleaned`**: (String)  Cleaned version of the `Text` field (lowercase, punctuation removed).
*   **`Tokens`**: (Array of Strings) List of all tokens (words) in the original `Text`.
*   **`Tokens_processed`**: (Array of Strings) List of tokens after removing stop words and punctuation.
*   **`Lemmas`**: (Array of Strings) List of lemmas (base forms) of the processed tokens.
*   **`POS_tags`**: (Array of Arrays/Tuples) List of Part-of-Speech tags, each element might be a tuple or array like `["lemma", "POS_tag"]`.
*   **`Named_entities`**: (Array of Arrays/Tuples) List of named entities recognized, each element might be a tuple or array like `["entity_text", "entity_label"]` (e.g., `["Amazon", "ORG"]`).
*   **`Sentiment_score`**: (Float) Sentiment score of the `Text` field, typically a value between -1 (negative) and 1 (positive).
*   **`Keywords`**: (Array of Strings) List of keywords extracted from the `Text` field.

**Indexes:**

Indexes are created on various fields including: `ProductId`, `UserId`, `Time`, `Score`, `Text` (for full-text search), `Sentiment_score`, `Keywords`, `Named_entities`, `Lemmas`, and `POS_tags`. These indexes enhance query performance for data retrieval and analysis.

## Further Steps

With this processed and indexed data in MongoDB, you can now perform various analyses, such as exploring sentiment trends, identifying popular keywords, understanding common themes in reviews, or building applications that leverage this rich review data.