# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert mẫu để tham khảo

Ví dụ dưới đây minh họa mức độ cụ thể cần có. Học viên không cần copy nguyên, nhưng ba alert trong bài nộp nên rõ ràng tương tự: điều kiện là gì, kéo dài bao lâu, ảnh hưởng tới user ra sao và người trực cần kiểm tra gì trước.

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms`
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` trong 5 phút
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn trước khi nhận câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard latency để xác nhận P95/P99 và khoảng thời gian tăng.
  2. Lọc `data/logs.jsonl` trong khoảng đó, lấy một `correlation_id` có `latency_ms` cao.
  3. Mở trace cùng `correlation_id` trên Langfuse, so sánh các span chính để xác định bước nào bất thường.
- Mitigation tạm thời: dựa trên evidence thực tế để rollback prompt, khôi phục cấu hình liên quan, tắt practice scenario hoặc giảm tải khi demo.
- Owner: `student-<MSSV>`

## Alert 1

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms` (SLO <= 3000ms)
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` trong 5 phút
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn trước khi nhận câu trả lời, trải nghiệm suy giảm
- Ba bước kiểm tra đầu tiên:
  1. **Metrics:** Mở dashboard latency để xác nhận P95/P99 và khoảng thời gian latency tăng vọt.
  2. **Logs:** Lọc `data/logs.jsonl` trong khoảng đó, lấy một `correlation_id` có `latency_ms > 3000`.
  3. **Traces:** Mở trace cùng `correlation_id` trên Langfuse, so sánh span `retrieval` và `generation` để xác định bước nào gây chậm trễ.
- Mitigation tạm thời: Nếu do retrieval (chậm 2.5s do `rag_slow`), kiểm tra database vector; nếu do prompt version mới làm tăng token/generation, rollback nhãn `production` về prompt version cũ.
- Owner: `student-2A202602678`

## Alert 2

- Tên: `HighErrorRate`
- Severity: `critical`
- Duration: `2m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: tỉ lệ request lỗi so với tổng request (Guardrail: error_rate <= 2%)
- Điều kiện và thời gian duy trì: `error_rate > 2%` kéo dài trong 2 phút
- Ảnh hưởng tới người dùng: người dùng nhận mã lỗi HTTP 500 hoặc không nhận được câu trả lời từ chatbot
- Ba bước kiểm tra đầu tiên:
  1. **Metrics:** Kiểm tra panel Errors trên Dashboard để biết tỉ lệ lỗi và thời điểm bắt đầu xảy ra sự cố.
  2. **Logs:** Lọc `data/logs.jsonl` tìm các sự kiện `request_failed`, trích xuất `error_type` và `correlation_id`.
  3. **Traces:** Tìm trace có cùng `correlation_id` trên Langfuse để xem exception stack trace ở span `retrieval` (ví dụ `Vector store timeout`) hoặc `generation`.
- Mitigation tạm thời: Khởi động lại dịch vụ backend bị lỗi, tắt incident scenario nếu đang trong đợt diễn tập (`python scripts/inject_incident.py --disable`), hoặc chuyển sang cơ chế fallback tĩnh.
- Owner: `student-2A202602678`

## Alert 3

- Tên: `RetrievalFailureSurge`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: tỉ lệ thành công của Retrieval (Guardrail: retrieval_success_rate >= 90%)
- Điều kiện và thời gian duy trì: `retrieval_success_rate < 90%` trong 5 phút
- Ảnh hưởng tới người dùng: bot không trích xuất được tài liệu liên quan, câu trả lời bị fallback hoặc trả lời sai/hallucination
- Ba bước kiểm tra đầu tiên:
  1. **Metrics:** Kiểm tra panel Errors (Retrieval success) và Quality trên Dashboard để xem mức độ sụt giảm.
  2. **Logs:** Lọc log tìm các bản ghi có `tool_name == "retrieval"` và `tool_success == false` hoặc `request_failed` có `RuntimeError`.
  3. **Traces:** Mở trace Langfuse xem span `retrieval` có bị lỗi hoặc trả về context rỗng hay không.
- Mitigation tạm thời: Kiểm tra kết nối đến vector database / mock RAG service, nạp lại index dữ liệu tài liệu corpus.
- Owner: `student-2A202602678`
