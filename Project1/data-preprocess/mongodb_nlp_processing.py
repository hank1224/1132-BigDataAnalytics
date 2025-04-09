"""
Script: MongoDB Review Data NLP Processing and Indexing

Description:
This script connects to a MongoDB database, retrieves review documents from a specified collection,
performs Natural Language Processing (NLP) on the 'Text' field of each document, and updates
the documents in the database with the NLP results.  **After processing, it also creates indexes on the newly added NLP fields to optimize querying.**

The NLP processing includes:
- Text Cleaning (lowercasing, punctuation removal)
- Tokenization
- Stop word and punctuation removal
- Lemmatization
- Part-of-Speech (POS) tagging
- Named Entity Recognition (NER)
- Sentiment Analysis using VADER
- Keyword Extraction using YAKE!

For performance on large datasets (like 500k reviews), the script uses batch processing
with MongoDB's `bulk_write` operation to minimize database update overhead. It also
only processes documents that have not yet been processed (i.e., are missing the NLP fields),
allowing for resumable execution.

**Index Creation:** After successfully inserting and processing the NLP data, the script creates
several indexes on the MongoDB collection for the newly generated NLP fields.  These indexes
are crucial for efficiently querying and filtering reviews based on sentiment scores, keywords,
named entities, lemmas, and POS tags.

Before running, ensure you have:
1. MongoDB server running and accessible.
2. Required Python libraries installed (pandas, pymongo, spacy, nltk, yake, tqdm).
3. spaCy language model downloaded (e.g., en_core_web_trf).
4. NLTK vader_lexicon downloaded (script attempts to download if missing).

Configuration parameters (MongoDB URI, database/collection names, batch size, spaCy model)
are set at the beginning of the script.

Logging is implemented to track progress and errors during the processing and indexing.
"""
import pandas as pd
from pymongo import MongoClient, UpdateOne
from pymongo.errors import OperationFailure
import spacy
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import yake
import re
import time
import logging
from tqdm import tqdm

# --- Configuration ---
MONGO_URI = 'mongodb://localhost:27017/'  # Your MongoDB connection string
DATABASE_NAME = 'mydatabase'         # Your database name
COLLECTION_NAME = 'reviews'        # Your Collection name
BATCH_SIZE = 500                   # Number of documents to process before updating DB
SPACY_MODEL = "en_core_web_trf"    # spaCy model ('en_core_web_sm', 'md', 'lg', 'trf')

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Connect to MongoDB ---
logging.info(f"Connecting to MongoDB at {MONGO_URI}...")
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000) # Add timeout
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    # Test connection
    client.server_info()
    logging.info(f"Successfully connected to DB: {DATABASE_NAME}, Collection: {COLLECTION_NAME}")
except Exception as e:
    logging.error(f"Failed to connect to MongoDB: {e}")
    exit()

# --- Load NLP Models (Load ONCE) ---
logging.info(f"Loading spaCy model: {SPACY_MODEL}...")
# Optional: Uncomment if you have a compatible GPU and want spaCy to use it
try:
    spacy.prefer_gpu()
    logging.info("spaCy GPU preference enabled.")
except:
    logging.warning("GPU not available or spaCy couldn't enable it. Using CPU.")

try:
    nlp = spacy.load(SPACY_MODEL)
    logging.info("spaCy model loaded successfully.")
except OSError as e:
     logging.error(f"Error loading spaCy model '{SPACY_MODEL}'. Make sure it's downloaded.")
     logging.error(f"Try: python -m spacy download {SPACY_MODEL}")
     logging.error(f"Original error: {e}")
     exit()


logging.info("Initializing NLTK VADER Sentiment Analyzer...")
try:
    analyzer = SentimentIntensityAnalyzer()
    # Perform a dummy analysis to ensure lexicon is loaded
    analyzer.polarity_scores("test")
except LookupError:
    import nltk
    logging.warning("NLTK vader_lexicon not found. Downloading...")
    try:
        nltk.download('vader_lexicon', quiet=True)
        analyzer = SentimentIntensityAnalyzer()
        logging.info("NLTK vader_lexicon downloaded and analyzer initialized.")
    except Exception as e:
        logging.error(f"Failed to download vader_lexicon or initialize analyzer: {e}")
        exit()
logging.info("VADER Analyzer initialized.")

logging.info("Initializing YAKE Keyword Extractor...")
kw_extractor = yake.KeywordExtractor(
    lan="en",
    n=3,
    dedupLim=0.9,
    dedupFunc='seqm',
    windowsSize=1,
    top=10, # Extract top 10 keywords
    features=None
)
logging.info("YAKE Extractor initialized.")

# --- NLP Processing Function ---
def process_review_text(text):
    """
    Performs NLP analysis on a single text string.
    Returns a dictionary with the results or None if input is invalid.
    """
    if not text or not isinstance(text, str):
        return None # Skip empty or non-string text

    try:
        # 1. Process with spaCy
        doc = nlp(text) # Run the main NLP pipeline

        # 2. Text_cleaned
        tokens_for_cleaning = [token.lower_ for token in doc if not token.is_punct]
        text_cleaned = " ".join(tokens_for_cleaning)
        text_cleaned = re.sub(r'\s+', ' ', text_cleaned).strip()

        # 3. Tokens
        tokens = [token.text for token in doc]

        # 4. Tokens_processed (Remove Stop Words and Punctuation)
        tokens_processed = [token.text for token in doc if not token.is_stop and not token.is_punct]

        # 5. Lemmas (Based on processed tokens)
        lemmas = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct]

        # 6. POS_tags (Based on processed tokens, using Lemma and POS)
        pos_tags = [(token.lemma_, token.pos_) for token in doc if not token.is_stop and not token.is_punct]

        # 7. Named_entities
        named_entities = [(ent.text, ent.label_) for ent in doc.ents]

        # 8. Sentiment_score (VADER on original text)
        sentiment_scores = analyzer.polarity_scores(text)
        sentiment_score = sentiment_scores['compound']

        # 9. Keywords (YAKE on original text)
        keywords_data = kw_extractor.extract_keywords(text)
        keywords = [kw for kw, score in keywords_data]

        # --- Structure for DB Update ---
        processed_data = {
            "Text_cleaned": text_cleaned,
            "Tokens": tokens,
            "Tokens_processed": tokens_processed,
            "Lemmas": lemmas,
            "POS_tags": pos_tags, # Store as list of tuples or list of lists
            "Named_entities": named_entities, # Store as list of tuples or list of lists
            "Sentiment_score": sentiment_score,
            "Keywords": keywords
            # Optionally keep original text if needed, but it's already there
            # "Text_original": text
        }
        return processed_data

    except Exception as e:
        logging.error(f"Error processing text: '{text[:100]}...'. Error: {e}", exc_info=False) # Log error but continue
        return None # Indicate failure for this specific text


# --- Main Processing Loop ---
logging.info("Starting NLP processing for MongoDB documents...")

# Query for documents that haven't been processed yet (checking for one field is enough)
query = {"Text_cleaned": {"$exists": False}, "Text": {"$exists": True, "$ne": None, "$ne": ""}}

# Get total count for progress bar
total_docs_to_process = collection.count_documents(query)
logging.info(f"Found {total_docs_to_process} documents to process.")

if total_docs_to_process == 0:
    logging.info("No documents found requiring processing. Exiting.")
    client.close()
    exit()

# Fetch documents using an iterator (memory efficient)
cursor = collection.find(query, {"_id": 1, "Text": 1}) # Only fetch necessary fields

bulk_operations = []
processed_count = 0
batch_count = 0
start_time = time.time()

# Use tqdm for progress bar
with tqdm(total=total_docs_to_process, desc="Processing Reviews") as pbar:
    try:
        for doc in cursor:
            doc_id = doc["_id"]
            original_text = doc.get("Text") # Use .get() for safety

            nlp_results = process_review_text(original_text)

            if nlp_results:
                # Create an update operation for this document
                bulk_operations.append(
                    UpdateOne({"_id": doc_id}, {"$set": nlp_results})
                )

                # Check if batch is full
                if len(bulk_operations) >= BATCH_SIZE:
                    logging.debug(f"Executing bulk write for batch {batch_count + 1} ({len(bulk_operations)} operations)...")
                    try:
                        collection.bulk_write(bulk_operations)
                        processed_count += len(bulk_operations)
                        batch_count += 1
                        logging.debug(f"Bulk write successful for batch {batch_count}.")
                    except Exception as e:
                        logging.error(f"Error during bulk write for batch {batch_count + 1}: {e}")
                        # Optional: Decide if you want to stop or just log and continue
                        # For now, we log and clear to avoid retrying the same failing batch
                    finally:
                        bulk_operations = [] # Clear the batch list

            # Update progress bar regardless of whether processing succeeded for this doc
            pbar.update(1)


        # Process any remaining operations after the loop finishes
        if bulk_operations:
            logging.info(f"Executing final bulk write for {len(bulk_operations)} remaining operations...")
            try:
                collection.bulk_write(bulk_operations)
                processed_count += len(bulk_operations)
                logging.info("Final bulk write successful.")
            except Exception as e:
                logging.error(f"Error during final bulk write: {e}")
            finally:
                 bulk_operations = [] # Ensure it's clear

    except KeyboardInterrupt:
         logging.warning("Processing interrupted by user (KeyboardInterrupt).")
         # Write any pending operations before exiting if interrupted
         if bulk_operations:
            logging.info(f"Executing final bulk write for {len(bulk_operations)} remaining operations due to interruption...")
            try:
                collection.bulk_write(bulk_operations)
                processed_count += len(bulk_operations)
                logging.info("Final bulk write successful.")
            except Exception as e:
                logging.error(f"Error during final bulk write on interrupt: {e}")

    except Exception as e:
        logging.error(f"An unexpected error occurred during processing loop: {e}", exc_info=True)

    finally:
        # Ensure cursor is closed if still open (though `for` loop usually handles this)
        if 'cursor' in locals() and cursor.alive:
             cursor.close()
             logging.info("MongoDB cursor closed.")


# --- Final Summary ---
end_time = time.time()
total_time = end_time - start_time
logging.info(f"\n--- Processing Summary ---")
logging.info(f"Total documents processed in this run: {processed_count}")
logging.info(f"Total time taken: {total_time:.2f} seconds")
if processed_count > 0:
    logging.info(f"Average processing time per document (incl. DB ops): {total_time / processed_count:.4f} seconds")
logging.info(f"Number of batches executed: {batch_count + (1 if processed_count % BATCH_SIZE != 0 and processed_count > 0 else 0)}") # Adjust batch count display

# --- Create Indexes for NLP Fields (Place after processing and before client.close()) ---
logging.info("\nStarting to create indexes for NLP fields...")

if 'client' in locals() and client and client.admin.command('ping')['ok']: # Check if client exists and connection is alive
    try:
        # Index for Sentiment Score (useful for sorting/filtering by sentiment)
        logging.info("Creating index on Sentiment_score...")
        collection.create_index([("Sentiment_score", -1)], name="sentiment_score_idx") # -1 for descending (e.g., find most positive)

        # Multikey Index for Keywords (useful for finding reviews with specific keywords)
        logging.info("Creating multikey index on Keywords...")
        collection.create_index([("Keywords", 1)], name="keywords_idx") # 1 for ascending (standard for multikey)

        # Multikey Index for Named Entity Labels (useful for filtering by entity type, e.g., PERSON, ORG)
        # We index the second element ('label_') of the tuples within the 'Named_entities' array.
        logging.info("Creating multikey index on Named_entities labels...")
        collection.create_index([("Named_entities.1", 1)], name="named_entities_label_idx")

        # Optional: Multikey Index for Named Entity Text (useful for finding specific entities)
        # We index the first element ('text') of the tuples within the 'Named_entities' array.
        logging.info("Creating multikey index on Named_entities text...")
        collection.create_index([("Named_entities.0", 1)], name="named_entities_text_idx")

        # Optional: Multikey Index for Lemmas (useful for searching base forms of words)
        logging.info("Creating multikey index on Lemmas...")
        collection.create_index([("Lemmas", 1)], name="lemmas_idx")

        # Optional: Multikey Index for POS Tags (useful for linguistic analysis)
        # Indexing the tag itself (second element of the tuple)
        logging.info("Creating multikey index on POS_tags...")
        collection.create_index([("POS_tags.1", 1)], name="pos_tags_idx")


        logging.info("NLP field indexes created or confirmed successfully.")
        logging.info("Current index list:")
        # List all indexes again to show the newly added ones
        for index_name in collection.index_information():
             logging.info(f" - {index_name}: {collection.index_information()[index_name]}")

    except OperationFailure as e:
        logging.error(f"Error creating NLP indexes: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred during NLP index creation: {e}")
else:
    logging.warning("MongoDB client not available or connection lost. Skipping NLP index creation.")

# Close MongoDB connection
client.close()
logging.info("MongoDB connection closed.")
