# Retrieval Evaluation Report
- Index: **atlas_chunks**
- k: **5**
- Queries: **10**
- Hits: **6**
- Recall@5: **0.600**

## Per-query detail (top 3 hits)

### Query: What is data engineering?
- Expected contains: `data`
- OK: **True**
  - sha256:ec678a49e623db418b42bb3e26a7988604c6d0700a72e0520c19b4f4265cfaec — https://en.wikipedia.org/wiki/Data_engineering
  - sha256:a285f423c02ede0ecfec5f425d2d5aae9fd11ba0d237cfa5825ca5285399e79a — https://en.wikipedia.org/wiki/Data_engineering
  - sha256:693ab6c791df4bc1e9accd9ff1dfcb05e2c1f65ce1a5e31f329d511e74d2fa76 — https://en.wikipedia.org/wiki/Data_engineering

### Query: What is information extraction?
- Expected contains: `extraction`
- OK: **True**
  - sha256:d506ef2b152de1c72ee12214ce323f9e6b68dca67d37bd81b848b62c8c868187 — https://en.wikipedia.org/wiki/Information_extraction
  - sha256:372667c0adf1cab7b3f0fe4c9f0d96e450794b000ea3ce3b938defc1b78b9b63 — https://en.wikipedia.org/wiki/Information_extraction
  - sha256:4ceb67bdfbb9cb297bef29f65b01ed81fb23c73145023de65616e9fa5c35993f — https://en.wikipedia.org/wiki/Information_extraction

### Query: What is SimHash used for?
- Expected contains: `simhash`
- OK: **False**
  - sha256:aa159ce7671eaffcd61773e6fc576f407c78a00adcba325aac9a40751adc321e — data\raw\pdfs\AI & the Web_ Understanding and managing the impact of Machine Learning models on the Web.pdf
  - sha256:3b0bef6d0b9e9669b67ce1c85bc31fbf840631a75b715414fcae4fa4898fecd2 — data\raw\pdfs\Strategies for Creating Uncertainty in the AI Era to Trigger Students’ Critical.pdf
  - sha256:ca99b2805746e707ca0c9d1aad152cb3f2641bed77efa7fb7577e3c679a832b3 — data\raw\pdfs\PLAW-107publ347.pdf

### Query: What is a PDF ingestion pipeline?
- Expected contains: `pdf`
- OK: **True**
  - sha256:a285f423c02ede0ecfec5f425d2d5aae9fd11ba0d237cfa5825ca5285399e79a — https://en.wikipedia.org/wiki/Data_engineering
  - sha256:56ecbbba258c6db155bf87fd760be5810e2b4250d719ec5eabc62d2eca363497 — data\raw\pdfs\AI & the Web_ Understanding and managing the impact of Machine Learning models on the Web.pdf
  - sha256:ec678a49e623db418b42bb3e26a7988604c6d0700a72e0520c19b4f4265cfaec — https://en.wikipedia.org/wiki/Data_engineering

### Query: What does chunking mean in NLP pipelines?
- Expected contains: `chunk`
- OK: **False**
  - sha256:c35bae96bd680641498677716f1bfcf4746fc7e0f05e71913fb762144254eeb8 — data\raw\pdfs\Identity & the Web.pdf
  - sha256:8babe9743211e7b52b35c43d5bbddae94110a01734b6e0de7c8c52f3a710c2ba — data\raw\pdfs\Agent2Agent Threats in Safety-Critical LLM Assistants.pdf
  - sha256:bff9d82d486b5bd4f887f929612f7becb0b9dd8a5bebd4760934fc215dae912f — data\raw\pdfs\Time-to-Event Estimation with Unreliably Reported Events in Medicare Health Plan Payment.pdf

### Query: What is near-duplicate detection?
- Expected contains: `duplicate`
- OK: **False**
  - sha256:9a23ed22c4d879ee8786fd7acbd020057d7ad6a707224f275bff15bfbf78aaf0 — data\raw\pdfs\AI & the Web_ Understanding and managing the impact of Machine Learning models on the Web.pdf
  - sha256:ea6cb70f5f3fa306e080e08238d4e6f7c273f1f697c00c869fe4e7751d6d66fd — https://en.wikipedia.org/wiki/Information_extraction
  - sha256:d9a13ee8d7dc0d2db4878d963b8d2629220cd82a656b1f43c7bdf9bf0ff6897d — data\raw\pdfs\AI & the Web_ Understanding and managing the impact of Machine Learning models on the Web.pdf

### Query: What is a web crawler?
- Expected contains: `crawl`
- OK: **True**
  - sha256:a285f423c02ede0ecfec5f425d2d5aae9fd11ba0d237cfa5825ca5285399e79a — https://en.wikipedia.org/wiki/Data_engineering
  - sha256:aa159ce7671eaffcd61773e6fc576f407c78a00adcba325aac9a40751adc321e — data\raw\pdfs\AI & the Web_ Understanding and managing the impact of Machine Learning models on the Web.pdf
  - sha256:c35bae96bd680641498677716f1bfcf4746fc7e0f05e71913fb762144254eeb8 — data\raw\pdfs\Identity & the Web.pdf

### Query: What is OpenSearch used for?
- Expected contains: `search`
- OK: **True**
  - sha256:aa159ce7671eaffcd61773e6fc576f407c78a00adcba325aac9a40751adc321e — data\raw\pdfs\AI & the Web_ Understanding and managing the impact of Machine Learning models on the Web.pdf
  - sha256:3b0bef6d0b9e9669b67ce1c85bc31fbf840631a75b715414fcae4fa4898fecd2 — data\raw\pdfs\Strategies for Creating Uncertainty in the AI Era to Trigger Students’ Critical.pdf
  - sha256:ca99b2805746e707ca0c9d1aad152cb3f2641bed77efa7fb7577e3c679a832b3 — data\raw\pdfs\PLAW-107publ347.pdf

### Query: What is a metadata store in a pipeline?
- Expected contains: `metadata`
- OK: **True**
  - sha256:aa159ce7671eaffcd61773e6fc576f407c78a00adcba325aac9a40751adc321e — data\raw\pdfs\AI & the Web_ Understanding and managing the impact of Machine Learning models on the Web.pdf
  - sha256:a1c4328c7e6a9d8e238e343f5340eb451e7c66b5bdf2ba6df0c48df313e8b165 — data\raw\pdfs\Identity & the Web.pdf
  - sha256:08e26d37ea4fbeb23aeabd738390e69bdb4245dd27a24a42b90fb89908e530ea — data\raw\pdfs\Identity & the Web.pdf

### Query: What is JSONL format used for?
- Expected contains: `json`
- OK: **False**
  - sha256:ca99b2805746e707ca0c9d1aad152cb3f2641bed77efa7fb7577e3c679a832b3 — data\raw\pdfs\PLAW-107publ347.pdf
  - sha256:81cbc4aa45d3297f7a27bca7349c3946a7295ecbda122b6afce692fdab2ecc3d — data\raw\pdfs\Identity & the Web.pdf
  - sha256:aa159ce7671eaffcd61773e6fc576f407c78a00adcba325aac9a40751adc321e — data\raw\pdfs\AI & the Web_ Understanding and managing the impact of Machine Learning models on the Web.pdf
