# 如何架 Project_1 環境

## 從頭建立 MongoDB 分析資料庫

```bash
docker-compose up -d
```

然後就可以從 [localhost:8081](http://localhost:8081) 存取 MongoExpress 介面。

### 做 NLP 轉換並寫入進 MongoDB

完整流程請看 [data-preprocess/README_zh.md](./data-preprocess/README_zh.md)。

**注意！** [mongodb_nlp_processing.py](./data-preprocess/mongodb_nlp_processing.py) 處理需要大約四小時。

執行完後可以去 MongoExpress [localhost:8081](http://localhost:8081) 看看寫入的資料長怎樣。

### 寫入時有做一些轉換

插入 MongoDB 後的資料與原始 CSV 資料主要有以下差別：

1. **新增 `_id` 欄位：** MongoDB 自動為每個文檔新增唯一的 `_id` 欄位。
2. **移除 csv 自帶的 `id`：** 原始 CSV 檔案的 `id` 欄位被移除，因為它是多餘的。
2. **並沒有 `ProductURL`：** ProductId 加上 `https://www.amazon.com/dp/` 即是 ProductURL。

## For 巨量第七組組員，請這樣做

1. 刪除此目錄的內的所有檔案 `1132-BigDataAnalytics/Project1/database/data`。

2. 下載我的整包資料庫 docker vloume，然後放進 `/data` 內（**注意： `/data` 資料夾只會有一個，不會是兩層 `/data/data` ！**）。

3. 啟動 MongoDB 和 MongoExpress：

    ```bash
    docker-compose up -d
    ```

3. 到 MongoExpress [localhost:8081](http://localhost:8081) 檢查資料格式是否與下面提供的一致。


## 開始做資料分析作業

檔案 [start_work.ipynb](./start-work.ipynb) 有做初步示範如何與資料庫做溝通，並且使用 pandas 做資料分析。

這樣大家就可以在同一個環境下獨立作業了，但要互相溝通好才不會做重複的分析工作。

**獨立作業時注意: 請不要有更動資料庫裡資料的操作，避免後續程式碼整合不起來。**