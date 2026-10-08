# 草稿類別（未公開類別）點樣用

網站有一個「草稿類別」機制：列入草稿嘅類別，公眾網站**完全唔會顯示**
（首頁冇格仔、下拉選單冇選項、該類別嘅產品唔會出現、直接入 `#/cat/<id>` 會彈返首頁）。

## 目前嘅草稿類別

| id | 中文 | English |
|---|---|---|
| `highbackchair` | 高背椅 | High-back chair |
| `armchair` | 扶手椅 | Armchair |
| `backrest` | 靠背架 | Bed backrest |
| `hipprotector` | 髖關節保護褲 | Hip protector |
| `restraint` | 約束用品 | Restraint items |

## 預覽草稿（喺正式網站都得）

喺網址後面加 `?draft=1`：

https://ychoccu.github.io/ych-occu-rehab-aids-tracker/?draft=1

頁頂會有黃色橫條提醒你係預覽模式。注意：呢個只係方便自己睇，唔係保密功能，
知道呢個網址嘅人都開到。

## 加產品入草稿類別

照平時咁加入 `products.json`，`category` 填上面嘅 id（例如 `"category": "highbackchair"`）。
加咗之後公眾都係睇唔到，直至你發佈該類別。每週價錢檢查會照常檢查呢啲產品。

## 發佈一個類別（一行改動）

打開 `index.html`，搵 `const DRAFT_CATEGORIES`，刪走要發佈嘅 id：

```js
// 發佈前
const DRAFT_CATEGORIES = new Set([]); // 2026-10-08 起全部公開
// 例如發佈「高背椅」之後
const DRAFT_CATEGORIES = new Set(['hipprotector', 'restraint']);
```

然後 commit 同 push 去 `main`，GitHub Pages 幾分鐘內更新。
如果想一次過全部發佈，改成 `new Set([])` 就得。

## 相關檔案

- `index.html` — `DRAFT_CATEGORIES`、分類下拉選單、中英標籤、首頁格仔、約束用品注意事項
- `scripts/category_schema.py` — 五個新類別嘅規格欄位
- `ych_rehab_aids_standalone.html` — 由 `python scripts/rebuild_html.py` 自動產生，唔使手改


## 目前狀態

2026-10-08：高背椅、扶手椅、靠背架、髖關節保護褲、約束用品五個類別已全部公開，`DRAFT_CATEGORIES` 為空。日後要新增隱藏類別，將其 id 加入 Set 即可。
