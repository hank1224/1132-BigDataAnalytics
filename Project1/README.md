# 如何架 Project_1 環境

## Docker 啟動服務

裝好 Docker 後，在這個資料夾目錄下：

```bash
docker-compose up -d
```

然後就可以從 [localhost:8081](localhost:8081) 存取 MongoExpress 介面。

## 寫入資料進資料庫

安裝操作 Python 操作 MongoDB 的套件 跟 pandas：

```bash
pip install pymongo pandas
```

**下載老師給的資料集 `Reviews_withURL.csv` 放在這個目錄下。**

然後執行[`insert_csv.py`](insert-csv.py)，

執行完後可以去 MongoExpress [localhost:8081](localhost:8081) 看看寫入的資料長怎樣。

### 寫入時有做一些轉換

插入 MongoDB 後的資料與原始 CSV 資料主要有以下差別：

1. **新增 `_id` 欄位：** MongoDB 自動為每個文檔新增唯一的 `_id` 欄位。
2. **`ProductURL` 移動到 `ProductInfo`：** 原始資料的 `ProductURL` 欄位被移到 `ProductInfo` 字典中，並更名為 `URL`。
3. **結構差異：** 原始 CSV 資料是扁平結構，MongoDB 資料是包含 `ProductInfo` 的層次結構。

## 開始做資料分析作業

檔案 [`start_work.ipynb`](./start-work.ipynb) 有做初步示範如何與資料庫做溝通，並且使用 pandas 做資料分析。

這樣大家就可以在同一個環境下獨立作業了，但要互相溝通好才不會做重複的分析工作。（或許可以開一個 git repo 比較方便？）

**獨立作業時注意: 請不要有更動資料庫裡資料的操作，避免後續程式碼整合不起來。**