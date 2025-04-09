"""
Script: MongoDB Data Ingestion for Amazon Reviews

Description:
This script is designed to download, preprocess, and ingest Amazon product review data into a MongoDB database.
It performs the following key operations:

1. **Data Download:** Checks for the existence of a CSV file containing Amazon reviews. If the CSV is not found,
   it attempts to download a zip file from a specified URL (Kaggle), and extracts the CSV file from the zip archive.
   This step ensures the script can fetch the dataset if it's not already available locally.

2. **MongoDB Connection:** Establishes a connection to a MongoDB database using a provided connection string.
   It verifies the connection and selects a specified database and collection to store the review data.

3. **Data Ingestion (Chunked Processing):** Reads the CSV file in chunks to efficiently handle large datasets
   without overwhelming memory. For each chunk, it transforms the data into a format suitable for MongoDB,
   and performs a batch insert operation to populate the MongoDB collection with review documents.
   Data cleaning and type conversion are applied during this process to ensure data integrity.

4. **Index Creation:** After successfully inserting the review data, the script creates several indexes on the MongoDB
   collection. These indexes are crucial for optimizing query performance, especially for common search patterns
   like querying by Product ID, User ID, time, and score, as well as enabling full-text search on the review text.

5. **Verification:** Finally, the script retrieves and displays the first document from the MongoDB collection
   to confirm that the data ingestion and indexing processes were successful.

This script is intended to set up a MongoDB database with Amazon review data, ready for further analysis or application
development that requires efficient querying and retrieval of review information.
"""

import os
import subprocess
import pandas as pd
from pymongo import MongoClient, TEXT
from pymongo.errors import ConnectionFailure, OperationFailure
import sys
import zipfile

MONGO_CONNECTION_STRING = 'mongodb://localhost:27017/'
DATABASE_NAME = 'mydatabase'
COLLECTION_NAME = 'reviews'
CSV_FILE_PATH = "./Project1/data-preprocess/Reviews.csv"
ZIP_FILE_PATH = "./Project1/data-preprocess/amazon-product-reviews.zip"
DOWNLOAD_URL = "https://www.kaggle.com/api/v1/datasets/download/arhamrumi/amazon-product-reviews"
CHUNK_SIZE = 10000

# Ensure Project1/data-preprocess directory exists
os.makedirs(os.path.dirname(CSV_FILE_PATH), exist_ok=True)

# Check if CSV file exists
if not os.path.exists(CSV_FILE_PATH):
    print(f"CSV file '{CSV_FILE_PATH}' does not exist, attempting to download...")
    try:
        # Download zip file
        subprocess.run([
            'curl', '-L', '-o', ZIP_FILE_PATH, DOWNLOAD_URL
        ], check=True) # check=True will raise an exception if the command fails
        print(f"Zip file downloaded to '{ZIP_FILE_PATH}'")

        # Extract zip file
        print(f"Extracting '{ZIP_FILE_PATH}'...")
        try:
            with zipfile.ZipFile(ZIP_FILE_PATH, 'r') as zip_ref:
                zip_ref.extract('Reviews.csv', path=os.path.dirname(CSV_FILE_PATH)) # Extract Reviews.csv to the specified directory
            print(f"Extracted 'Reviews.csv' to '{CSV_FILE_PATH}'")
        except zipfile.BadZipFile as e:
            print(f"Failed to extract zip file: {e}")
            sys.exit(1) # Exit program if extraction fails

    except subprocess.CalledProcessError as e:
        print(f"File download failed: {e}")
        print("Please ensure curl is installed.")
        sys.exit(1) # Exit program if download fails
    except Exception as e:
        print(f"Unknown error occurred during download or extraction: {e}")
        sys.exit(1) # Exit program for other errors
else:
    print(f"CSV file '{CSV_FILE_PATH}' already exists, skipping download.")

# --- Connection and Setup ---
client = None # Initialize client to None
try:
    client = MongoClient(MONGO_CONNECTION_STRING, serverSelectionTimeoutMS=5000) # Set timeout
    # The ismaster command is cheap and does not require auth.
    client.admin.command('ismaster') # Test connection
    print("MongoDB connection successful!")
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]

except ConnectionFailure as e:
    print(f"Could not connect to MongoDB: {e}")
    sys.exit(1) # Exit program if connection fails

try:
    print(f"Reading data from '{CSV_FILE_PATH}'...")
    # --- Data Reading and Processing (Chunk Processing) ---
    total_inserted_count = 0
    chunk_num = 1
    # Use iterator=True and chunksize for chunk reading
    for chunk_df in pd.read_csv(CSV_FILE_PATH, encoding='utf-8', chunksize=CHUNK_SIZE, iterator=True):
        print(f"  Processing chunk {chunk_num} ({len(chunk_df)} rows)...")
        data_chunk = []
        for record in chunk_df.to_dict(orient="records"):
            # Field check and conversion (ensure correct numeric types, handle possible NaN)
            # .get(key, default_value) is safer than direct [] access, avoids KeyError
            restructured_record = {
                "ProductId": record.get("ProductId"),
                "UserId": record.get("UserId"),
                "ProfileName": record.get("ProfileName"),
                # Ensure numbers are Python native types, handle NaN
                "HelpfulnessNumerator": int(record.get("HelpfulnessNumerator", 0)),
                "HelpfulnessDenominator": int(record.get("HelpfulnessDenominator", 0)),
                "Score": int(record.get("Score", 0)), # Score is an integer
                "Time": int(record.get("Time", 0)), # Time is Unix timestamp, should be integer
                "Summary": record.get("Summary"),
                "Text": record.get("Text"),
            }
            # Simple cleaning, remove None values (if any)
            restructured_record = {k: v for k, v in restructured_record.items() if v is not None}
            data_chunk.append(restructured_record)

        # --- Batch Insert Data ---
        if data_chunk:
            try:
                result = collection.insert_many(data_chunk, ordered=False) # ordered=False might be faster, allows partial failures
                inserted_count = len(result.inserted_ids)
                total_inserted_count += inserted_count
                print(f"    Successfully inserted {inserted_count} records.")
            except OperationFailure as e:
                print(f"    Error inserting data: {e}")
                # Decide whether to continue processing the next chunk based on needs
        else:
            print("    Chunk is empty, skipping insertion.")
        chunk_num += 1

    print(f"\nTotal successfully inserted {total_inserted_count} records!")

    # --- Create Indexes (after all data is inserted) ---
    print("\nStarting to create indexes...")
    try:
        # Core query indexes
        collection.create_index([("ProductId", 1)], name="product_id_idx")
        collection.create_index([("UserId", 1)], name="user_id_idx")
        # Compound indexes (very common)
        collection.create_index([("ProductId", 1), ("Time", -1)], name="product_time_idx") # Query by product, sort by time
        collection.create_index([("ProductId", 1), ("Score", -1)], name="product_score_idx") # Query by product, sort by score (-1 means high score first)
        # Separate time and score indexes (if cross-product sorting is needed)
        collection.create_index([("Time", -1)], name="time_idx") # All reviews sorted by time
        # collection.create_index([("Score", -1)], name="score_idx") # All reviews sorted by score (might partially overlap with product_score_idx)

        # Full-text search index
        # Note: Only one Text Index is allowed per Collection. Here, it's created for 'Text' field.
        # If you generated Keywords field from NLP, consider Multikey Index on Keywords (`Keywords`, 1)
        collection.create_index([("Text", TEXT)], default_language='english', name="text_content_idx")
        # If reviews are mainly in English, specifying default_language='english' is more effective

        print("Indexes created or confirmed successfully.")
        print("Index list:")
        for index_name in collection.index_information():
             print(f" - {index_name}: {collection.index_information()[index_name]}")

    except OperationFailure as e:
        print(f"Error creating indexes: {e}")

    # --- Test Query ---
    print("\nDisplaying the first record (confirm structure):")
    found_data_first = collection.find_one()
    if found_data_first:
        print(found_data_first)
    else:
        print("No data found in the Collection.")

except FileNotFoundError:
    print(f"Error: CSV file '{CSV_FILE_PATH}' not found")
    sys.exit(1)
except Exception as e:
    print(f"Unexpected error during processing: {e}")
    sys.exit(1)
finally:
    # --- Close Connection ---
    if client:
        client.close()
        print("\nMongoDB connection closed.")
