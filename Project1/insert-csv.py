import pandas as pd
from pymongo import MongoClient

# 連接到 MongoDB (請替換成你的 MongoDB 連線資訊)
client = MongoClient('mongodb://localhost:27017/')  # 預設本機連線
db = client['mydatabase']  # 選擇或創建資料庫 (請替換成你的資料庫名稱)
collection = db['reviews']  # 選擇或創建 Collection (請替換成你的 Collection 名稱)

# 讀取 CSV 檔案
### 注意編碼 ###
df = pd.read_csv("Reviews_withURL.csv", encoding='utf-8')

# 轉換 DataFrame 為字典列表，並調整 Document 結構
data = []
for record in df.to_dict(orient="records"):
    # 建立新的 Document 結構，將 ProductURL 放入 ProductInfo
    restructured_record = {
        "ProductId": record.get("ProductId"), # 使用 .get() 避免 KeyError
        "ProductInfo": {
            "URL": record.get("ProductURL")  # 使用 .get() 避免 KeyError
        },
        "UserId": record.get("UserId"),      # 使用 .get() 避免 KeyError
        "ProfileName": record.get("ProfileName"), # 使用 .get() 避免 KeyError
        "HelpfulnessNumerator": record.get("HelpfulnessNumerator"), # 使用 .get() 避免 KeyError
        "HelpfulnessDenominator": record.get("HelpfulnessDenominator"), # 使用 .get() 避免 KeyError
        "Score": record.get("Score"),        # 使用 .get() 避免 KeyError
        "Time": record.get("Time"),         # 使用 .get() 避免 KeyError
        "Summary": record.get("Summary"),     # 使用 .get() 避免 KeyError
        "Text": record.get("Text"),          # 使用 .get() 避免 KeyError
        # 保留原有的 Id (如果需要，或者可以考慮移除，MongoDB 會自動生成 _id)
        "Id": record.get("Id")
    }
    data.append(restructured_record)

# 批量插入資料
if data:
    collection.insert_many(data)
    print(f"成功插入 {len(data)} 筆資料！")
else:
    print("CSV 檔案為空，沒有資料插入。")

# 建立索引 (在插入資料之後建立索引更有效率)
collection.create_index([("ProductId", 1)], name="product_id_index") # 為 ProductId 建立升序索引，並命名索引
collection.create_index([("UserId", 1)], name="user_id_index")       # 為 UserId 建立升序索引，並命名索引
collection.create_index([("Time", -1)], name="time_index")         # 為 Time 建立降序索引 (例如：最新評論)，並命名索引
collection.create_index([("Score", 1)], name="score_index")        # 為 Score 建立升序索引，並命名索引

print("已建立索引：ProductId, UserId, Time, Score")

# 測試查詢剛剛插入的資料 (查詢 ProductId 為 'B001E4KFG0' 的第一筆資料)
found_data = collection.find_one({"ProductId": "B001E4KFG0"})
print("\n查詢 ProductId 為 'B001E4KFG0' 的第一筆資料：")
print(found_data)

# 測試查詢剛剛插入的資料 (顯示第一筆資料，確認結構)
found_data_first = collection.find_one()
print("\n顯示第一筆資料 (確認結構)：")
print(found_data_first)

# 關閉 MongoDB 連線 (程式結束時關閉連線是好習慣)
client.close()