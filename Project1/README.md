# Analyze Amazon Review by MongoDB

Using Dataset: [Amazon Product Reviews](https://www.kaggle.com/api/v1/datasets/download/arhamrumi/amazon-product-reviews)

Teacher Provided: [Amazon Fine Food Reviews](https://www.kaggle.com/datasets/snap/amazon-fine-food-reviews)

Hopefully, the dataset is consistent with the one provided by the teacher.

## Build MongoDB Analysis Database from Scratch

```bash
docker-compose up -d
```

Then you can access the MongoExpress interface from [localhost:8081](http://localhost:8081).

### Perform NLP Transformation and Write to MongoDB

For the complete process, please refer to [data-preprocess/README_zh.md](./data-preprocess/README_zh.md).

**Attention!** [mongodb_nlp_processing.py](./data-preprocess/mongodb_nlp_processing.py) processing takes approximately four hours.

After execution, you can check the written data structure in MongoExpress [localhost:8081](http://localhost:8081).

### Transformations During Write Operations

The data inserted into MongoDB differs from the original CSV data in the following key aspects:

1.  **Added `_id` Field:** MongoDB automatically adds a unique `_id` field to each document.
2.  **Removed CSV Built-in `id`:** The original `id` field from the CSV file has been removed as it is redundant.
3.  **No `ProductURL`:**  ProductId combined with `https://www.amazon.com/dp/` forms the ProductURL.
4.  **Indexes Created:**  Used to enhance query efficiency.
    - _id_
    - product_id_idx
    - user_id_idx
    - product_time_idx
    - product_score_idx
    - time_idx
    - text_content_idx
    - sentiment_score_idx
    - keywords_idx
    - named_entities_label_idx
    - named_entities_text_idx
    - lemmas_idx
    - pos_tags_idx

### (Optional) Add Product Metadata

The dataset contains 74250 distinct products. Although product information can be obtained by web scraping from URLs, it is highly likely to be blocked.

Therefore, I attempted to match data with the same Product ID from other datasets, as shown in [match_products.ipynb](./data-preprocess/match-product-metadata/match_products.ipynb). **Running this notebook takes approximately five hours.**

However, only 33817 product matches were found, representing approximately 50% of the data.

After running the matching process, use [mongodb_products_metadata.py](./data-preprocess/match-product-metadata/mongodb_products_metadata.py) to write the metadata into the database.

### Collection: `reviews`
```
{
  _id: ObjectId,                      // MongoDB-generated unique identifier
  ProductId: String,                   // Product ID
  UserId: String,                      // User ID
  ProfileName: String,                // User profile name
  HelpfulnessNumerator: Number (Integer),   // Number of users who found the review helpful
  HelpfulnessDenominator: Number (Integer), // Total number of users who rated the review helpful
  Score: Number (Integer),                // Review score (e.g., 1-5 stars)
  Time: Number (Integer/Timestamp),       // Review timestamp (Unix timestamp)
  Summary: String,                     // Review summary/title
  Text: String,                        // Full review text
  Keywords: Array (String),            // List of keywords (array of strings)
  Lemmas: Array (String),             // List of lemmas (array of strings)
  Named_entities: Array (Array (String)),  // List of named entities (2D array of strings, e.g., [['Vitality', 'ORG']])
  POS_tags: Array (Array (String)),     // List of Part-of-Speech tags (2D array of strings, e.g., [['buy', 'VERB']])
  Sentiment_score: Number (Float),          // Sentiment score (floating-point number)
  Text_cleaned: String,                // Cleaned review text
  Tokens: Array (String),              // List of tokens (array of strings)
  Tokens_processed: Array (String)       // List of processed tokens (array of strings)
}
```

### Collection: `products`
```
{
  _id: ObjectId,                      // MongoDB-generated unique identifier
  main_category: String,                // Main category
  title: String,                       // Product title
  average_rating: Number (Float),       // Average rating (floating-point number)
  rating_number: Number (Integer),      // Number of ratings (integer)
  features: Array,                    // Product features (array, may contain strings or objects)
  description: String,                 // Product description (string, may contain JSON string)
  price: null,                        // Product price (can be null)
  images: Object,                     // Product images (object, structure unknown)
  videos: Object,                     // Product videos (object, structure unknown)
  store: null,                        // Store name (can be null)
  categories: Array,                   // Product categories (array, may contain strings)
  details: Object,                    // Product details (object, key-value pairs)
  parent_asin: String,                // Parent ASIN (Amazon Standard Identification Number)
  bought_together: Array,             // Products frequently bought together (array, may contain ASINs)
  subtitle: null,                      // Subtitle (can be null)
  author: null                         // Author (can be null)
}