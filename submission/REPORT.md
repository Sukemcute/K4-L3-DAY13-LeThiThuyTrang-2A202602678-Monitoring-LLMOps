# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Chỉ cần 3 output text và 5 ảnh runtime; dùng đường dẫn tương đối, ví dụ `evidence/03-incident-trace.png`.

## 1. Thông tin học viên

- **Họ và tên:** Lê Thị Thùy Trang
- **MSSV:** 2A202602678
- **Lớp:** K4-L3B
- **Repository URL:** `https://github.com/Sukemcute/K4-L3-DAY13-LeThiThuyTrang-2A202602678-Monitoring-LLMOps`
- **Commit SHA cuối:** `8da9f1d`
- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-2A202602678`

## 2. Evidence index

Bảng ánh xạ toàn bộ evidence được lưu trong thư mục `submission/evidence/` theo hướng dẫn chi tiết [docs/SCREENSHOT_GUIDE.md](../docs/SCREENSHOT_GUIDE.md):

| STT | Tên file evidence | Mô tả nội dung chứng minh | Đường dẫn tương đối |
|:---:|---|---|---|
| 01 | `01-pytest.png` / `pytest.txt` | Kết quả chạy test tự động (24/24 passed) | `evidence/pytest.txt` / `evidence/01-pytest.png` |
| 02 | `02-log-validator.png` / `log-validator.txt` | Điểm đánh giá log format và PII (100/100) | `evidence/log-validator.txt` / `evidence/02-log-validator.png` |
| 03 | `03-dashboard-validator.png` / `dashboard-validator.txt` | Kiểm tra hợp lệ 6/6 panels của Dashboard contract | `evidence/dashboard-validator.txt` / `evidence/03-dashboard-validator.png` |
| 04 | `04-structured-log.png` | Cấu trúc log JSON và metadata (`correlation_id`, `model`, `env`...) | `evidence/04-structured-log.png` |
| 05 | `05-pii-redaction.png` | Dữ liệu PII (Email, SĐT, CCCD, Thẻ) được scrub thành `[REDACTED_...]` | `evidence/05-pii-redaction.png` |
| 06 | `06-trace-list.png` | Danh sách traces trong project cá nhân (`day13-k4-l3b-2A202602678`) | `evidence/06-trace-list.png` |
| 07 | `07-trace-waterfall.png` | Cây quan sát phân cấp: `lab-agent-run` -> `retrieval` & `generation` | `evidence/07-trace-waterfall.png` |
| 08 | `08-trace-metadata.png` | Chi tiết metadata của trace (`correlation_id`, `prompt_name`, `version`) | `evidence/08-trace-metadata.png` |
| 09 | `09-prompt-versions.png` | Quản lý prompt `day13-chat` gồm Version 1 và Version 2 | `evidence/09-prompt-versions.png` |
| 10 | `10-prompt-rollback.png` | Bằng chứng promote prompt v2 lên production và rollback về v1 | `evidence/10-prompt-rollback.png` |
| 11 | `11-dashboard-overview.png` | Toàn cảnh Dashboard 6 panels đọc trực tiếp từ `data/logs.jsonl` | `evidence/11-dashboard-overview.png` |
| 12 | `12-incident-metric.png` | Đỉnh nhọn độ trễ P95 tăng vọt trên Dashboard do sự cố `rag_slow` | `evidence/12-incident-metric.png` |
| 13 | `13-incident-log.png` | Dòng log trong `data/logs.jsonl` của request sự cố (`req-cc2997e5`) | `evidence/13-incident-log.png` |
| 14 | `14-incident-trace.png` | Waterfall trace trên Langfuse của `req-cc2997e5` định vị span `retrieval` bị chậm | `evidence/14-incident-trace.png` |

> **Ánh xạ tương đương với 5 ảnh runtime bắt buộc theo [docs/SUBMISSION.md](../docs/SUBMISSION.md):**
> - **Ảnh 1 (`01-incident-log.png`):** Structured log và log của request sự cố ↔ `evidence/13-incident-log.png` (và `evidence/04-structured-log.png`).
> - **Ảnh 2 (`02-trace-list.png`):** Danh sách traces trong project cá nhân ↔ `evidence/06-trace-list.png`.
> - **Ảnh 3 (`03-incident-trace.png`):** Trace waterfall & metadata của incident ↔ `evidence/14-incident-trace.png` (và `evidence/07-trace-waterfall.png`, `evidence/08-trace-metadata.png`).
> - **Ảnh 4 (`04-prompt-versioning.png`):** Quản lý prompt versions, promote và rollback ↔ `evidence/10-prompt-rollback.png` (và `evidence/09-prompt-versions.png`).
> - **Ảnh 5 (`05-dashboard-incident.png`):** Toàn cảnh 6 panel dashboard và metric bất thường ↔ `evidence/11-dashboard-overview.png` & `evidence/12-incident-metric.png`.

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 | 100/100 | Đạt toàn bộ 4 tiêu chí: schema, correlation ID, enrichment, PII |
| `validate_dashboard.py` | 6/6 panel | 6/6 panel | Đạt chuẩn schema contract 6/6 panel |
| `pytest` | 22 passed | 24 passed | Toàn bộ unit tests bao gồm PII tests pass |
| Số traces hợp lệ | 10 | > 150 (~154 traces) | Traces hợp lệ đầy đủ span tree (`agent`, `retriever`, `generation`) ghi nhận trên Langfuse (ảnh `06-trace-list.png`) |
| Số PII leak | 0 | 0 | Đã scrub sạch PII (Email, Phone VN, CCCD, Thẻ) |
| Latency P95 / TTFT P95 | 2067ms / 50ms | 2657ms / 50ms | Phản ánh đầy đủ baseline và đỉnh nhọn do sự cố challenge |
| Retrieval success rate | 100.0% | 100.0% | 100% retrieval thành công |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Dùng middleware `CorrelationIdMiddleware` kế thừa `BaseHTTPMiddleware`. Đầu mỗi request gọi `clear_contextvars()`, kiểm tra header `x-request-id` từ client (nếu có thì tái sử dụng, không có thì sinh mã ngẫu nhiên dạng `req-<8-hex>` qua `uuid.uuid4().hex[:8]`). Sau đó bind vào structlog contextvars `correlation_id`, lưu vào `request.state.correlation_id` và trả lại cho client trong response header `x-request-id` cùng `x-response-time-ms`.
- **Các metadata được ghi vào structured log:** Tại endpoint `/chat`, gọi `bind_contextvars` để gắn `user_id_hash` (băm SHA-256 12 ký tự từ `user_id`), `session_id`, `feature`, `model` (`agent.model`), `env` (`APP_ENV`) trước log `request_received`. Log `response_sent` bổ sung thêm `latency_ms`, `ttft_ms`, `tokens_in`, `tokens_out`, `cost_usd`, `quality_score`, `tool_name`, `tool_success` và `answer_preview`.
- **Cách bảo đảm PII được scrub trước khi ghi:** Đăng ký processor `scrub_event` vào pipeline của `structlog` trước bước `JsonlFileProcessor()` và `JSONRenderer()`. `scrub_event` quét đệ quy các chuỗi trong log và thay thế bằng regex: Email -> `[REDACTED_EMAIL]`, Số điện thoại VN -> `[REDACTED_PHONE_VN]`, CCCD 12 số -> `[REDACTED_CCCD]`, Thẻ ngân hàng 16 số -> `[REDACTED_CREDIT_CARD]`. Vì xử lý trước serializer, PII thô không bao giờ bị ghi vào file log hoặc console.
- **Cách kiểm chứng kết quả:** Chạy `python -m pytest tests/test_pii.py` (pass 4/4 test). Gửi request thực tế có chứa các loại PII và `x-request-id`, kiểm tra file `data/logs.jsonl` thấy toàn bộ PII đã bị che và response header trả đúng correlation ID. Chạy `python scripts/validate_logs.py` đạt điểm tuyệt đối **100/100**.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Traces được ghi trực tiếp vào project Langfuse cá nhân `day13-k4-l3b-2A202602678` thông qua key pair riêng cấu hình trong `.env`. Mỗi trace có `user_id_hash` băm từ MSSV/user_id, danh sách tags `["lab", feature, model]` và tên trace `day13-agent-request`.
- **Cấu trúc root/retrieval/generation observations:**
  - Root observation: `lab-agent-run` (loại `agent`) theo dõi toàn bộ hàm `run()` của agent.
  - Child observation 1: `retrieval` (loại `retriever`) gắn decorator `@observe` trên hàm `retrieve()` để đo độ trễ tra cứu tài liệu liên quan.
  - Child observation 2: `generation` (loại `generation`) gắn decorator `@observe` trên hàm `FakeLLM.generate()`, ghi nhận `model`, `usage` (`input_tokens`, `output_tokens`), `cost` và liên kết với đối tượng prompt từ Langfuse. Cả hai child observation đều tắt `capture_input` và `capture_output` để bảo vệ PII.
- **Cách nối trace với log:** Middleware sinh ra mã `correlation_id` (định dạng `req-<8-hex>`) và lưu vào context request. Khi khởi tạo trace, trường này được đưa vào metadata của trace: `metadata={"correlation_id": correlation_id}`. Khi cần điều tra, chỉ cần copy `correlation_id` từ dòng log nghi vấn trong `data/logs.jsonl` và dán vào ô tìm kiếm của Langfuse để mở đúng trace.
- **Prompt name:** `day13-chat`
- **Version/label baseline:** Version 1 (labels: `baseline`, `production`)
- **Version/label candidate:** Version 2 (labels: `candidate`, `latest`)
- **Trace ID / Correlation ID của mỗi version:**
  - Version 1 (`baseline` / ban đầu `production`):
    - Correlation ID: `req-3f12a3be` (hoặc `req-5f97ffb1`, `req-d76f4139`).
    - Trace ID minh họa: `35d96de4a734f853ee2ecd570fc6b888` (thể hiện trong ảnh `07-trace-waterfall.png` và `08-trace-metadata.png`: root `lab-agent-run`, child span `retrieval` và `generation`, prompt `day13-chat` v1 nhãn `production`).
  - Version 2 (`candidate`):
    - Correlation ID: `req-a45b62fe` (hoặc `req-7c7acfe7`).
  - Version 2 (`production` khi promote):
    - Correlation ID: `req-0e1b2cce`.
    - Trace ID minh họa: `f956e7df34e2883c4669a598ea4581b0` (thể hiện trong ảnh `10-prompt-rollback.png`: query `"Testing prompt v2 in production"`, prompt `day13-chat` version 2 nhãn `production`, 180 tokens, cost $0.002208).
  - Version 1 (`production` sau khi rollback):
    - Correlation ID: `req-ea97b932` (query `"Testing prompt v1 after rollback in production"`, nhãn `production` được chuyển về lại cho Version 1 an toàn không cần sửa code).
  *(Tìm kiếm correlation_id trên thanh search của Langfuse Traces để đối chiếu trace ID tương ứng).*
- **Cách promote và rollback `production`:**
  - Promote: Trên Langfuse Prompts, chuyển nhãn `production` từ v1 sang v2. Khởi động lại API hoặc đợi hết 60s cache TTL để app nhận prompt mới.
  - Rollback: Khi prompt v2 gây tăng chi phí hoặc suy giảm chất lượng, di chuyển nhãn `production` trên Langfuse quay trở lại v1. Hệ thống quay về phiên bản ổn định mà không cần sửa source code hay cấu hình server.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:**
  1. `Latency`: Theo dõi thời gian phản hồi qua các phân vị P50, P95, P99 và TTFT (Time to First Token) của request `response_sent`. Ngưỡng cảnh báo: 3000ms.
  2. `Traffic`: Theo dõi lưu lượng request theo thời gian thực (request rate/throughput), phân tách theo từng tính năng (`qa`, `summary`).
  3. `Errors`: Theo dõi tỉ lệ request thất bại (HTTP 500 / `request_failed`) và tỉ lệ thành công của bước retrieval (`tool_success == true`).
  4. `Cost`: Theo dõi chi phí ước tính theo thời gian thực (USD) dựa trên token input/output của LLM ($3/1M input, $15/1M output).
  5. `Tokens`: Theo dõi số lượng `tokens_in` và `tokens_out` của từng request để phát hiện kịp thời prompt/output phình to bất thường.
  6. `Quality`: Theo dõi điểm đánh giá chất lượng tự động (`quality_score`) dựa trên heuristics (sử dụng context, độ dài, từ khóa câu hỏi).
- **SLO và lý do chọn:** SLO chính là `fast_successful_requests`: 99.5% requests đạt `event == "response_sent"` và `latency_ms <= 3000ms` trong chu kỳ rolling window 28 ngày. Lý do chọn: dựa trên baseline đo được P95 latency ở điều kiện bình thường khoảng 2067ms và tỉ lệ thành công 100%; ngưỡng 3000ms đảm bảo người dùng tương tác với chatbot không bị cảm giác chờ đợi quá lâu mà vẫn chịu tải tốt.
- **Cách tính error budget:** Với target SLO 99.5%, error budget là `100% - 99.5% = 0.5%`. Nếu hệ thống tiếp nhận khoảng 10,000 requests trong cửa sổ đánh giá 28 ngày, số lượng request tối đa được phép bị chậm (> 3000ms) hoặc thất bại là `10,000 * 0.5% = 50 requests`.
- **Ba alert và runbook tương ứng:**
  1. `HighLatencyP95` (Warning, `p95(latency_ms) > 3000ms` kéo dài 5m, kênh Slack `#k4-l3b-alerts`, runbook tại `docs/alerts.md#alert-1`).
  2. `HighErrorRate` (Critical, `error_rate > 2%` kéo dài 2m, kênh Slack `#k4-l3b-alerts`, runbook tại `docs/alerts.md#alert-2`).
  3. `RetrievalFailureSurge` (Warning, `retrieval_success_rate < 90%` kéo dài 5m, kênh Slack `#k4-l3b-alerts`, runbook tại `docs/alerts.md#alert-3`).

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1` (Cohort K4, seed 1312)
- **Khoảng thời gian điều tra:** `2026-09-30 05:24:15 UTC` đến `2026-09-30 05:24:30 UTC` (tương đương `12:24:15 - 12:24:30 UTC+7`).
- **Triệu chứng từ metrics:** Panel `1. Latency percentiles and TTFT` trên Dashboard ghi nhận đỉnh nhọn độ trễ tăng vọt: P95 latency vượt ngưỡng 2000ms (đạt mức ~2655ms nội bộ API và ~10600ms - 13300ms từ góc nhìn client dưới tải đồng thời 5 workers). Trong khi đó, `TTFT` vẫn ổn định ở 50ms, `Error rate` là 0% và `Quality score` đạt 0.8 - 0.9, chứng minh sự cố chỉ nằm ở độ trễ xử lý trước khi gọi LLM.
- **Log line và correlation ID liên quan:**
  - `correlation_id`: `req-cc2997e5` (hoặc `req-ef6ddae0`, `req-de3cbfb9`, `req-4a43c8b8`, `req-d97ca85b`).
  - Dòng log đại diện trong `data/logs.jsonl`:
    ```json
    {"service": "api", "latency_ms": 2655, "ttft_ms": 50, "tokens_in": 36, "tokens_out": 118, "cost_usd": 0.001878, "quality_score": 0.9, "tool_name": "retrieval", "tool_success": true, "payload": {"answer_preview": "Starter answer. You should improve this output logic and add better quality chec..."}, "event": "response_sent", "model": "claude-sonnet-4-5", "env": "dev", "user_id_hash": "c3a24a72d92a", "feature": "monitoring", "correlation_id": "req-cc2997e5", "session_id": "k4-l3b-challenge-s04", "level": "info", "ts": "2026-09-30T05:24:17.990603Z"}
    ```
- **Trace ID và span gây ảnh hưởng:**
  - **Trace ID:** `fb112dcc96e8756e3275bf2bf2c93fcf` (tìm kiếm theo `correlation_id=req-cc2997e5` trong project Langfuse cá nhân `day13-k4-l3b-2A202602678`).
  - Cây quan sát Timeline/Waterfall (ảnh `14-incident-trace.png`) cho thấy root trace mất 2.66s (2655ms), trong đó span con **`retrieval`** chiếm tới **2.50s (2500ms)**, còn span **`generation`** chỉ mất **152ms**. Span gây tắc nghẽn chính là `retrieval`.
- **Root cause:** Bước tra cứu tài liệu liên quan trong `app/mock_rag.py` (hàm `retrieve()`) bị nghẽn do kích hoạt sự cố `rag_slow` (mô phỏng tình huống vector database bị quá tải, suy giảm hiệu năng kết nối hoặc slow query kéo dài 2.5s).
- **Fix action:** Tắt sự cố qua endpoint `/incidents/rag_slow/disable`. Đối với môi trường thực tế: scale out cluster cơ sở dữ liệu vector, tối ưu hóa index tìm kiếm tương đồng (ANN index), bổ sung tầng cache Redis/In-memory cho các câu hỏi phổ biến, và cấu hình timeout 1.5s kèm fallback về keyword search/cached context khi vector DB phản hồi chậm.
- **Preventive measure:**
  - Kích hoạt alert `HighLatencyP95` (cảnh báo khi P95 latency vượt quá 2000ms trong 5 phút vào kênh Slack `#k4-l3b-alerts`).
  - Thiết lập Circuit Breaker và Timeout cho client gọi dịch vụ RAG Retrieval.
  - Bổ sung integration test & load test kiểm tra SLA của tầng RAG vào pipeline CI/CD trước khi deploy.

> Gợi ý cách viết ngắn, không thay cho evidence thực tế: "Metric cho thấy `[latency/error/cost/quality]` bất thường trong `[khoảng thời gian]`. Log line `[event]` có `correlation_id=[...]` đại diện cho request bị ảnh hưởng. Trace cùng `correlation_id` cho thấy span `[retrieval/generation/prompt/tool]` có dấu hiệu `[chậm/lỗi/token tăng]`. Root cause là `[nguyên nhân suy ra từ evidence]`. Fix action là `[hành động khôi phục]`; preventive measure là `[alert/runbook/test/guardrail để ngăn tái diễn]`."

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Đăng ký bộ xử lý `scrub_event` vào pipeline của `structlog` trước bước renderer/file writer, đồng thời thiết lập `capture_input=False` và `capture_output=False` trên các decorator `@observe` của Langfuse. Lý do: bảo đảm an toàn dữ liệu cá nhân (PII) theo nguyên tắc Security by Design / Defense in Depth, ngăn chặn triệt để nguy cơ PII thô (CCCD, email, điện thoại, thẻ ngân hàng) bị ghi xuống đĩa cục bộ hay gửi lên cloud của bên thứ ba.
- **Một lỗi/blocker đã gặp:** Gặp lỗi `401 Unauthorized` khi kết nối Langfuse Cloud do nhầm lẫn giữa host EU (`cloud.langfuse.com`) và US (`us.cloud.langfuse.com`), khiến SDK phải dùng local fallback. Ngoài ra, giao diện Dashboard ở Panel 1 ban đầu bị tràn viền (overflow) giá trị TTFT khi co màn hình do kích thước font cố định `1.5rem` trên 4 chỉ số metric.
- **Cách tìm nguyên nhân và xử lý:** Dùng script Python gọi trực tiếp `Langfuse.auth_check()` trên cả hai host để xác định chính xác project thuộc region EU, sau đó cập nhật `LANGFUSE_BASE_URL` trong `.env`. Với giao diện Dashboard, đã tái cấu trúc CSS sang `flex-wrap: wrap`, tinh chỉnh kích thước chữ `1.25rem`, đặt `min-width: 65px` và bổ sung `overflow: hidden` cho `.panel`.
- **Cách hiểu luồng Metrics → Logs → Traces:**
  - **Metrics (What & When):** Đóng vai trò radar phát hiện triệu chứng tổng quan (ví dụ P95 latency vượt ngưỡng SLO) và mốc thời gian bắt đầu xảy ra sự cố.
  - **Logs (Which):** Đóng vai trò danh sách đối tượng bị ảnh hưởng; lọc theo khung thời gian từ metrics để xác định các request lỗi/chậm và lấy ra mã định danh duy nhất `correlation_id`.
  - **Traces (Where & Why):** Đóng vai trò kính hiển vi phân tích nguyên nhân; dùng `correlation_id` tra cứu trên cây Waterfall để định vị chính xác span con nào (retrieval hay generation) gây nghẽn, từ đó kết luận root cause một cách không thể chối cãi.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:** Ứng dụng LLMOps có hành vi biến động phụ thuộc vào prompt và dữ liệu đầu vào. Việc gắn nhãn (`baseline`, `candidate`, `production`) cho phép thử nghiệm và chuyển đổi an toàn mà không cần sửa code. Giám sát token/cost giúp kiểm soát chi phí API thời gian thực. Khả năng **Rollback nhanh** là lá chắn an toàn tối hậu, cho phép đưa hệ thống về trạng thái ổn định trong vài giây khi prompt mới gây ảo giác hoặc làm tăng vọt độ trễ.
- **Điều quan trọng nhất đã học:** Nắm vững phương pháp luận điều tra sự cố bài bản theo chuỗi quan sát chuẩn mực `Metrics -> Logs -> Traces` và kỹ năng xây dựng hệ thống quan sát (Observability) toàn diện cho ứng dụng AI/LLM.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** Các thành phần LLM và RAG hiện tại đang chạy mô phỏng (FakeLLM / Mock RAG); trên môi trường production quy mô lớn, cần mở rộng thêm semantic caching bằng Redis, circuit breaker tự động và webhook cảnh báo trực tiếp về PagerDuty/Slack.

## 9. Checklist trước khi nộp

- [x] Kết quả và evidence thuộc commit SHA cuối.
- [x] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [x] Có đúng 3 file text và 5 ảnh runtime theo hướng dẫn.
- [x] Incident evidence nối đúng metric → log → trace.
- [x] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [x] Repository chạy lại được theo README.
- [x] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [x] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
