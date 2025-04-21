# Analyze Amazon Review by MongoDB

使用資料集：[Amazon Product Reviews](https://www.kaggle.com/datasets/arhamrumi/amazon-product-reviews)

我來才發現老師有給[來源](https://www.kaggle.com/datasets/snap/amazon-fine-food-reviews)，希望這檔案跟老師給的一致（應該是一樣的啦）。

## 第七組 組員分工

*   **環境設置、數據前處理與基礎 NLP 處理**:
    *   [M11351002 陳澔恩](https://github.com/hank1224)
    *   相關程式碼: [數據前處理](./data-preprocess/)

*   **NAPL 產品偏好、情感分析與關鍵詞分析**:
    *   [B11001019 傅煒宸](https://github.com/Weichen20021223)
    *   [B11001137 許庭瑄](https://github.com/crazipig)
    *   相關分析 Notebook: [NAPL 分析](./analyzing-code/NAPL-NLP.ipynb)

*   **熱門產品時序性評論趨勢分析與捆綁產品探討**:
    *   [M11351015 李國禎](https://github.com/M11351015)
    *   相關分析 Notebook: [熱門與捆綁產品分析](./analyzing-code/Popular-and-Bundle-Product.ipynb)

*   **隨機森林模型建構與評論中關鍵詞萃取**:
    *   [M11301302 黃冠翔](https://github.com/Kuan-Sean)
    *   相關分析 Notebook: [隨機森林與關鍵詞分析](./analyzing-code/RandomForest-Keyword.ipynb)

*   **專案投影片與簡報製作**:
    *   M11301108 周易儒
    *   最終專案簡報 (PDF) [Presentation](./presentation.pdf)


## 從頭建立 MongoDB 分析資料庫

```bash
docker-compose up -d
```

然後就可以從 [localhost:8081](http://localhost:8081) 存取 MongoExpress 介面。

### 做 NLP 轉換並寫入進 MongoDB

完整流程請看 [data-preprocess/README_zh.md](./data-preprocess/README_zh.md)。

**注意！** [mongodb_nlp_processing.py](./data-preprocess/mongodb_nlp_processing.py) 處理需要**大約四小時**。

執行完後可以去 MongoExpress [localhost:8081](http://localhost:8081) 看看寫入的資料長怎樣。

### 寫入時有做一些轉換

插入 MongoDB 後的資料與原始 CSV 資料主要有以下差別：

1. **新增 `_id` 欄位：** MongoDB 自動為每個文檔新增唯一的 `_id` 欄位。
2. **移除 csv 自帶的 `id`：** 原始 CSV 檔案的 `id` 欄位被移除，因為它是多餘的。
3. **並沒有 `ProductURL`：** ProductId 加上 `https://www.amazon.com/dp/` 即是 ProductURL。
4. **建立 indexes：** 用於增加查詢效率。
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

### （可選）加入 Product Metadata

資料集共有 74250 不同的產品，雖然可以從 URL 爬蟲取得商品資訊，但一定會被鎖。

所以我嘗試從其他資料集 match 相同產品 ID 的資料，見 [match_products.ipynb](./data-preprocess/match-product-metadata/match_products.ipynb)，跑完**需要五小時**。

但也只 match 到 33817 筆 商品，接近 50% 的資料。

跑完再用 [mongodb_products_metadata.py](./data-preprocess/match-product-metadata/mongodb_products_metadata.py) 寫入資料庫。

## For 巨量第七組組員，請這樣做

1. 刪除此目錄的內的所有檔案 `1132-BigDataAnalytics/Project1/database/data`。

2. 下載我的整包資料庫然後放進 `database/` 內（放入後路徑會是這樣：Project1/database/data/...）。

3. 啟動 MongoDB 和 MongoExpress：

    ```bash
    docker-compose up -d
    ```

3. 到 MongoExpress [localhost:8081](http://localhost:8081) 檢查資料格式是否與下面提供的一致。

### Collection: `reviews`
```
{
  _id: ObjectId,                      // MongoDB 自動產生的唯一識別碼
  ProductId: String,                   // 產品 ID
  UserId: String,                      // 使用者 ID
  ProfileName: String,                // 使用者名稱
  HelpfulnessNumerator: Number (Integer),   // 認為評論有幫助的人數
  HelpfulnessDenominator: Number (Integer), // 評論總共被評估為有幫助的人數
  Score: Number (Integer),                // 評論分數 (例如 1-5)
  Time: Number (Integer/Timestamp),       // 評論的時間 (Unix 時間戳記)
  Summary: String,                     // 評論標題
  Text: String,                        // 完整評論文字
  Keywords: Array (String),            // 關鍵字列表 (字串陣列)
  Lemmas: Array (String),             // 詞元列表 (字串陣列)
  Named_entities: Array (Array (String)),  // 命名實體列表 (二維字串陣列，例如 [['Vitality', 'ORG']])
  POS_tags: Array (Array (String)),     // 詞性標籤列表 (二維字串陣列，例如 [['buy', 'VERB']])
  Sentiment_score: Number (Float),          // 情感分數 (浮點數)
  Text_cleaned: String,                // 清理後的評論文字
  Tokens: Array (String),              // 分詞列表 (字串陣列)
  Tokens_processed: Array (String)       // 處理後的分詞列表 (字串陣列)
}
```

### Collection: `products`
```
{
  _id: ObjectId,                      // MongoDB 自動產生的唯一識別碼
  main_category: String,                // 主要分類
  title: String,                       // 商品標題
  average_rating: Number (Float),       // 平均評分 (浮點數)
  rating_number: Number (Integer),      // 評分人數 (整數)
  features: Array,                    // 商品特色 (陣列，可能包含字串或物件)
  description: String,                 // 商品描述 (字串，可能包含 JSON 字串)
  price: null,                        // 商品價格 (可以為空值)
  images: Object,                     // 商品圖片 (物件，結構未知)
  videos: Object,                     // 商品影片 (物件，結構未知)
  store: null,                        // 商店名稱 (可以為空值)
  categories: Array,                   // 商品分類 (陣列，可能包含字串)
  details: Object,                    // 商品詳細資訊 (物件，鍵值對形式)
  parent_asin: String,                // 父 ASIN (亞馬遜商品識別碼)
  bought_together: Array,             // 一起購買的商品 (陣列，可能包含 ASIN)
  subtitle: null,                      // 副標題 (可以為空值)
  author: null                         // 作者 (可以為空值)
}
```


## 開始做資料分析作業

檔案 [start_work.ipynb](./start-work.ipynb) 有做初步示範如何與資料庫做溝通，並且使用 pandas 做資料分析。

這樣大家就可以在同一個環境下獨立作業了，但要互相溝通好才不會做重複的分析工作。

**獨立作業時注意: 請不要有更動資料庫裡資料的操作，避免後續程式碼整合不起來。**

## Contributions

<a href="https://github.com/hank1224/1132-BigDataAnalytics/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=hank1224/1132-BigDataAnalytics" />
</a>