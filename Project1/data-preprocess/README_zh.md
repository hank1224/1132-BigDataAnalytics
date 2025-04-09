# Amazon 評論資料導入和 NLP 管道 - 代碼描述

這個項目包含兩個 Python 腳本，它們協同工作來處理 Amazon 產品評論資料並將其儲存在 MongoDB 中。 以下是對每個腳本的功能以及最終資料結構的詳細說明。

## 腳本概述

1. **`mongodb_ingestion.py`**：
    * **下載資料：** 如果找不到本地的 Amazon 評論資料 CSV 檔案，此腳本會自動從 Kaggle 下載。
    * **導入到 MongoDB：** 從 CSV 檔案中獲取評論資料，並將其載入到您指定的 MongoDB 資料庫和集合中。 它通過分塊處理資料來處理大型檔案。
    * **設定初始資料庫：** 在 MongoDB 中建立基本索引，以加快初始資料查詢的速度。

2. **`mongodb_nlp_processing.py`**：
    * **分析評論文本 (NLP)：** 連接到第一個腳本建立的 MongoDB 資料庫，並對評論文本（`Text` 欄位）執行自然語言處理 (NLP)。
    * **新增 NLP 特徵：** 從評論文本中提取各種 NLP 特徵，並將它們作為新的欄位新增到 MongoDB 中每個評論文檔中。 這些特徵包括：
        * 清理過的文本
        * 詞語化 (tokens)
        * 詞形還原 (lemmas, 詞語的基礎形式)
        * 詞性標註 (Part-of-Speech tags)
        * 在文本中識別的命名實體
        * 情感分數（正面/負面/中性）
        * 關鍵詞
    * **為 NLP 資料建立索引：** 在 MongoDB 中為這些新的 NLP 欄位建立索引，使其能夠有效地根據 NLP 分析結果搜尋和過濾評論。

## 執行

按以下順序執行這些腳本：

1. **`mongodb_ingestion.py`**：
    ```bash
    python mongodb_ingestion.py
    ```

2. **`mongodb_nlp_processing.py`**：
    ```bash
    python mongodb_nlp_processing.py
    ```

## 執行後 MongoDB 中的資料格式

執行完兩個腳本後，您的 MongoDB 集合將包含代表 Amazon 評論的文檔。 每個文檔將具有以下結構：

**原始欄位（來自 CSV 資料，由 `mongodb_ingestion.py` 導入）：**

*   **`ProductId`**: (字串) 產品的唯一識別碼。
*   **`UserId`**: (字串) 撰寫評論的用戶的唯一識別碼。
*   **`ProfileName`**: (字串) 用戶的姓名。
*   **`HelpfulnessNumerator`**: (整數) 認為該評論有幫助的用戶數量。
*   **`HelpfulnessDenominator`**: (整數) 評論有用性總評分人數。
*   **`Score`**: (整數) 給產品的評分（例如，1 到 5 星）。
*   **`Time`**: (整數) 撰寫評論的時間的 Unix 時間戳。
*   **`Summary`**: (字串) 評論的摘要。
*   **`Text`**: (字串) 評論的完整文本。

**NLP 欄位（由 `mongodb_nlp_processing.py` 新增）：**

*   **`Text_cleaned`**: (字串) `Text` 欄位的清潔版本（小寫，刪除標點符號）。
*   **`Tokens`**: (字串陣列) 原始 `Text` 中的所有詞語化 (words) 的清單。
*   **`Tokens_processed`**: (字串陣列) 刪除停用詞和標點符號後的詞語化 (tokens) 的清單。
*   **`Lemmas`**: (字串陣列) 已處理詞語化的詞形還原（基礎形式）的清單。
*   **`POS_tags`**: (陣列的陣列/元組) 詞性標註的清單，每個元素可能是一個元組或陣列，例如 `["lemma", "POS_tag"]`。
*   **`Named_entities`**: (陣列的陣列/元組) 識別的命名實體的清單，每個元素可能是一個元組或陣列，例如 `["entity_text", "entity_label"]`（例如，`["Amazon", "ORG"]`）。
*   **`Sentiment_score`**: (浮點數) `Text` 欄位的情感分數，通常是介於 -1（負面）和 1（正面）之間的值。
*   **`Keywords`**: (字串陣列) 從 `Text` 欄位提取的關鍵詞的清單。

**索引：**

索引在各個欄位上建立，包括：`ProductId`、`UserId`、`Time`、`Score`、`Text`（用於全文搜尋）、`Sentiment_score`、`Keywords`、`Named_entities`、`Lemmas` 和 `POS_tags`。 這些索引提高了資料檢索和分析的查詢效能。

## 後續步驟

透過 MongoDB 中這些經過處理和索引的資料，您現在可以執行各種分析，例如探索情感趨勢、識別熱門關鍵詞、理解評論中的常見主題，或建立利用這些豐富評論資料的應用程式。
