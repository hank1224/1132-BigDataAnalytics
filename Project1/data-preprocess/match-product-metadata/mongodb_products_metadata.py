from pymongo import MongoClient
import csv
import json
import ast

MONGO_CONNECTION_STRING = 'mongodb://localhost:27017/'
DATABASE_NAME = 'mydatabase'
COLLECTION_NAME = 'products'
CSV_FILE_PATH = './Project1/data-preprocess/matched_products_metadata.csv'

def insert_csv_to_mongodb_from_file(csv_file_path, mongo_connection_string, database_name, collection_name):
    """
    Inserts CSV data from a file into a MongoDB collection.

    Args:
        csv_file_path (str): Path to the CSV file.
        mongo_connection_string (str): MongoDB connection string.
        database_name (str): Name of the MongoDB database.
        collection_name (str): Name of the MongoDB collection.
    """
    try:
        client = MongoClient(mongo_connection_string, serverSelectionTimeoutMS=5000)
        client.admin.command('ismaster')
        print("MongoDB connection successful!")
        db = client[database_name]
        collection = db[collection_name]

        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:  # Open the CSV file
            csv_reader = csv.DictReader(csvfile)
            headers = csv_reader.fieldnames

            for row in csv_reader:
                document = {}
                for header in headers:
                    value = row[header]

                    if header in ['average_rating']:
                        try:
                            document[header] = float(value) if value else None
                        except ValueError:
                            document[header] = None
                    elif header in ['rating_number']:
                        try:
                            document[header] = int(value) if value else None
                        except ValueError:
                            document[header] = None
                    elif header in ['price']:
                        try:
                            document[header] = float(value) if value and value != 'None' else None
                        except ValueError:
                            document[header] = None
                    elif header in ['features', 'categories', 'bought_together']:
                        try:
                            document[header] = ast.literal_eval(value) if value else []
                        except (ValueError, SyntaxError):
                            document[header] = []
                    elif header in ['images', 'videos', 'details']:
                        try:
                            document[header] = json.loads(value) if value and value != 'None' else {}
                        except json.JSONDecodeError:
                            document[header] = {}
                    else:
                        document[header] = value if value else None
                collection.insert_one(document)
        print(f"Successfully inserted data from '{csv_file_path}' into collection '{collection_name}'.")

    except FileNotFoundError:
        print(f"Error: CSV file not found at path: {csv_file_path}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    insert_csv_to_mongodb_from_file(CSV_FILE_PATH, MONGO_CONNECTION_STRING, DATABASE_NAME, COLLECTION_NAME)