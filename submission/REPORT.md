# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Chỉ cần 3 output text và 5 ảnh runtime; dùng đường dẫn tương đối, ví dụ `evidence/03-incident-trace.png`.

## 1. Thông tin học viên

- **Họ và tên:** Lê Thị Thùy Trang
- **MSSV:** 2A202602678
- **Lớp:** K4-L3B
- **Repository URL:**
- **Commit SHA cuối:**
- **Challenge ID:**
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-2A202602678`

## 2. Evidence index

Giữ đúng ba output text và năm ảnh dưới đây. Không tách thêm ảnh; nếu cần giải thích, ghi bằng chữ trong các mục sau.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/pytest.txt` |
| Log validator | `evidence/log-validator.txt` |
| Dashboard validator | `evidence/dashboard-validator.txt` |
| Structured log + incident log | `evidence/01-incident-log.png` |
| Trace list | `evidence/02-trace-list.png` |
| Trace waterfall + metadata + incident trace | `evidence/03-incident-trace.png` |
| Prompt versions + promote/rollback | `evidence/04-prompt-versioning.png` |
| Dashboard + incident metric | `evidence/05-dashboard-incident.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 | 100/100 | Đạt toàn bộ 4 tiêu chí: schema, correlation ID, enrichment, PII |
| `validate_dashboard.py` | 6/6 panel | 6/6 panel | Đạt chuẩn schema contract 6/6 panel |
| `pytest` | 22 passed | 24 passed | Toàn bộ unit tests bao gồm PII tests pass |
| Số traces hợp lệ | 10 | 21 | Traces hợp lệ đầy đủ span tree trong workload |
| Số PII leak | 0 | 0 | Đã scrub sạch PII (Email, Phone VN, CCCD, Thẻ) |
| Latency P95 / TTFT P95 | 2067ms / 50ms | 2163ms / 53ms | Duy trì dưới ngưỡng SLO 3000ms |
| Retrieval success rate | 100.0% | 100.0% | 21/21 retrieval thành công |

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
  - Version 1 (`baseline`): correlation_id `req-5f97ffb1` (hoặc `req-d76f4139`)
  - Version 2 (`candidate`): correlation_id `req-a45b62fe` (hoặc `req-7c7acfe7`)
  - Version 2 (`production` khi promote): correlation_id `req-0e1b2cce`
  - Version 1 (`production` sau khi rollback): correlation_id `req-ea97b932`
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

- **Challenge ID:**
- **Khoảng thời gian điều tra:**
- **Triệu chứng từ metrics:**
- **Log line và correlation ID liên quan:**
- **Trace ID và span gây ảnh hưởng:**
- **Root cause:**
- **Fix action:**
- **Preventive measure:**

> Gợi ý cách viết ngắn, không thay cho evidence thực tế: "Metric cho thấy `[latency/error/cost/quality]` bất thường trong `[khoảng thời gian]`. Log line `[event]` có `correlation_id=[...]` đại diện cho request bị ảnh hưởng. Trace cùng `correlation_id` cho thấy span `[retrieval/generation/prompt/tool]` có dấu hiệu `[chậm/lỗi/token tăng]`. Root cause là `[nguyên nhân suy ra từ evidence]`. Fix action là `[hành động khôi phục]`; preventive measure là `[alert/runbook/test/guardrail để ngăn tái diễn]`."

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:**
- **Một lỗi/blocker đã gặp:**
- **Cách tìm nguyên nhân và xử lý:**
- **Cách hiểu luồng Metrics → Logs → Traces:**
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
- **Điều quan trọng nhất đã học:**
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:**

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [ ] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Có đúng 3 file text và 5 ảnh runtime theo hướng dẫn.
- [ ] Incident evidence nối đúng metric → log → trace.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [ ] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
