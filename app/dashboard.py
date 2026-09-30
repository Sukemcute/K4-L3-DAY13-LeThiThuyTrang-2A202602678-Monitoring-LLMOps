from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOG_PATH = Path(os.getenv("LOG_PATH", "data/logs.jsonl"))


def calculate_metrics() -> dict[str, Any]:
    if not LOG_PATH.exists():
        return {"empty": True}

    records: list[dict[str, Any]] = []
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except Exception:
            continue

    total_requests = 0
    failed_requests = 0
    tool_success_count = 0
    tool_total_count = 0
    latencies: list[int] = []
    ttfts: list[int] = []
    costs: list[float] = []
    tokens_in_list: list[int] = []
    tokens_out_list: list[int] = []
    quality_scores: list[float] = []
    error_types: dict[str, int] = {}

    # Traffic by minute
    traffic_by_min: dict[str, int] = {}
    time_points: list[dict[str, Any]] = []

    for r in records:
        event = r.get("event")
        ts = r.get("ts", "")
        minute_key = ts[:16].replace("T", " ") if len(ts) >= 16 else "N/A"

        if event == "request_received":
            total_requests += 1
            traffic_by_min[minute_key] = traffic_by_min.get(minute_key, 0) + 1

        elif event == "request_failed":
            failed_requests += 1
            err = r.get("error_type", "UnknownError")
            error_types[err] = error_types.get(err, 0) + 1
            if r.get("tool_name") == "retrieval":
                tool_total_count += 1
                if r.get("tool_success") is True:
                    tool_success_count += 1

        elif event == "response_sent":
            lat = r.get("latency_ms")
            if lat is not None:
                latencies.append(lat)
            ttft = r.get("ttft_ms")
            if ttft is not None:
                ttfts.append(ttft)
            c = r.get("cost_usd")
            if c is not None:
                costs.append(c)
            ti = r.get("tokens_in")
            if ti is not None:
                tokens_in_list.append(ti)
            to = r.get("tokens_out")
            if to is not None:
                tokens_out_list.append(to)
            qs = r.get("quality_score")
            if qs is not None:
                quality_scores.append(qs)

            if r.get("tool_name") == "retrieval":
                tool_total_count += 1
                if r.get("tool_success") is True:
                    tool_success_count += 1

            time_points.append({
                "time": ts[11:19] if len(ts) >= 19 else "",
                "latency": lat or 0,
                "ttft": ttft or 0,
                "tokens": (ti or 0) + (to or 0),
                "cost": c or 0.0,
                "cid": r.get("correlation_id", ""),
            })

    def pct(arr: list[int | float], p: float) -> float:
        if not arr:
            return 0.0
        sorted_arr = sorted(arr)
        idx = max(0, min(len(sorted_arr) - 1, int(len(sorted_arr) * (p / 100.0))))
        return round(float(sorted_arr[idx]), 2)

    p50 = pct(latencies, 50)
    p95 = pct(latencies, 95)
    p99 = pct(latencies, 99)
    ttft_p95 = pct(ttfts, 95)

    error_rate = round((failed_requests / total_requests * 100), 2) if total_requests else 0.0
    retrieval_success_rate = (
        round((tool_success_count / tool_total_count * 100), 2) if tool_total_count else 100.0
    )
    total_cost = round(sum(costs), 6)
    total_tokens_in = sum(tokens_in_list)
    total_tokens_out = sum(tokens_out_list)
    avg_quality = round(sum(quality_scores) / len(quality_scores), 2) if quality_scores else 0.0

    return {
        "empty": False,
        "total_requests": total_requests,
        "failed_requests": failed_requests,
        "p50": p50,
        "p95": p95,
        "p99": p99,
        "ttft_p95": ttft_p95,
        "error_rate": error_rate,
        "retrieval_success_rate": retrieval_success_rate,
        "error_types": error_types,
        "total_cost": total_cost,
        "tokens_in": total_tokens_in,
        "tokens_out": total_tokens_out,
        "avg_quality": avg_quality,
        "traffic_by_min": traffic_by_min,
        "time_points": time_points[-20:],
    }


def render_dashboard_html() -> str:
    data = calculate_metrics()
    p95_val = data.get("p95", 0.0)
    p95_status = "status-ok" if p95_val <= 3000 else "status-warn"
    err_val = data.get("error_rate", 0.0)
    err_status = "status-ok" if err_val <= 2.0 else "status-error"
    cost_val = data.get("total_cost", 0.0)
    cost_status = "status-ok" if cost_val <= 2.5 else "status-warn"
    qual_val = data.get("avg_quality", 0.0)
    qual_status = "status-ok" if qual_val >= 0.75 else "status-warn"

    pts = data.get("time_points", [])
    chart_labels = json.dumps([p["time"] for p in pts])
    chart_latencies = json.dumps([p["latency"] for p in pts])
    chart_ttfts = json.dumps([p["ttft"] for p in pts])
    chart_costs = json.dumps([p["cost"] for p in pts])

    traffic_keys = list(data.get("traffic_by_min", {}).keys())[-10:]
    traffic_vals = [data.get("traffic_by_min", {})[k] for k in traffic_keys]

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="refresh" content="30">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>K4-L3B Day 13 Monitoring &amp; LLMOps Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root {{
      --bg: #0b0f19;
      --card-bg: #151d2f;
      --border: #23314d;
      --text: #e2e8f0;
      --muted: #8e9bb0;
      --primary: #38bdf8;
      --success: #10b981;
      --warning: #f59e0b;
      --danger: #ef4444;
      --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: var(--font);
      padding: 24px;
    }}
    header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--border);
    }}
    h1 {{ font-size: 1.5rem; font-weight: 700; color: #fff; }}
    .meta-tags {{ display: flex; gap: 12px; }}
    .tag {{
      background: rgba(56, 189, 248, 0.1);
      border: 1px solid rgba(56, 189, 248, 0.3);
      color: var(--primary);
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 0.8rem;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
      gap: 20px;
    }}
    .panel {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
      overflow: hidden;
    }}
    .panel-header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 14px;
      gap: 8px;
    }}
    .panel-title {{
      font-size: 1rem;
      font-weight: 600;
      color: #f1f5f9;
    }}
    .panel-desc {{
      font-size: 0.75rem;
      color: var(--muted);
      margin-top: 2px;
    }}
    .badge {{
      font-size: 0.72rem;
      padding: 3px 8px;
      border-radius: 4px;
      font-weight: 600;
      white-space: nowrap;
    }}
    .status-ok {{ background: rgba(16, 185, 129, 0.15); color: var(--success); border: 1px solid var(--success); }}
    .status-warn {{ background: rgba(245, 158, 11, 0.15); color: var(--warning); border: 1px solid var(--warning); }}
    .status-error {{ background: rgba(239, 68, 68, 0.15); color: var(--danger); border: 1px solid var(--danger); }}
    .metric-values {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px 14px;
      margin-bottom: 12px;
      align-items: baseline;
    }}
    .metric-item {{
      display: flex;
      flex-direction: column;
      flex: 1 1 auto;
      min-width: 65px;
    }}
    .metric-val {{
      font-size: 1.25rem;
      font-weight: 700;
      color: #fff;
      white-space: nowrap;
      letter-spacing: -0.01em;
    }}
    .metric-lbl {{
      font-size: 0.7rem;
      color: var(--muted);
      text-transform: uppercase;
      font-weight: 600;
      letter-spacing: 0.03em;
      margin-top: 2px;
    }}
    .chart-box {{
      height: 180px;
      position: relative;
    }}
    .threshold-note {{
      font-size: 0.75rem;
      color: var(--muted);
      margin-top: 10px;
      border-top: 1px dashed var(--border);
      padding-top: 8px;
    }}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>K4-L3B Day 13 Monitoring &amp; LLMOps Dashboard</h1>
      <p style="color: var(--muted); font-size: 0.85rem; margin-top: 4px;">Contract: config/dashboard.yaml | Time Window: 60 mins | Refresh: 30s</p>
    </div>
    <div class="meta-tags">
      <span class="tag">Student: Le Thi Thuy Trang</span>
      <span class="tag">MSSV: 2A202602678</span>
      <span class="tag">Auto-refresh 30s</span>
    </div>
  </header>

  <div class="grid">
    <!-- Panel 1: Latency -->
    <div class="panel">
      <div class="panel-header">
        <div>
          <div class="panel-title">1. Latency percentiles and TTFT</div>
          <div class="panel-desc">Unit: ms | Source: data/logs.jsonl</div>
        </div>
        <span class="badge {p95_status}">Threshold: P95 &le; 3000ms</span>
      </div>
      <div class="metric-values">
        <div class="metric-item"><span class="metric-val">{data.get("p50", 0)}ms</span><span class="metric-lbl">P50</span></div>
        <div class="metric-item"><span class="metric-val" style="color: {var_p95_color(p95_val)}">{p95_val}ms</span><span class="metric-lbl">P95</span></div>
        <div class="metric-item"><span class="metric-val">{data.get("p99", 0)}ms</span><span class="metric-lbl">P99</span></div>
        <div class="metric-item"><span class="metric-val">{data.get("ttft_p95", 0)}ms</span><span class="metric-lbl">TTFT P95</span></div>
      </div>
      <div class="chart-box"><canvas id="latencyChart"></canvas></div>
      <div class="threshold-note">SLO threshold: P95 latency &le; 3000ms. Tail latency reflected via P99.</div>
    </div>

    <!-- Panel 2: Traffic -->
    <div class="panel">
      <div class="panel-header">
        <div>
          <div class="panel-title">2. Request traffic</div>
          <div class="panel-desc">Unit: requests_per_minute | Source: data/logs.jsonl</div>
        </div>
        <span class="badge status-ok">Threshold: Rate &ge; 1 req/min</span>
      </div>
      <div class="metric-values">
        <div class="metric-item"><span class="metric-val">{data.get("total_requests", 0)}</span><span class="metric-lbl">Total Requests</span></div>
      </div>
      <div class="chart-box"><canvas id="trafficChart"></canvas></div>
      <div class="threshold-note">Aggregated by 1-minute bucket from request_received events.</div>
    </div>

    <!-- Panel 3: Errors -->
    <div class="panel">
      <div class="panel-header">
        <div>
          <div class="panel-title">3. Error rate and retrieval success</div>
          <div class="panel-desc">Unit: percent (%) | Source: data/logs.jsonl</div>
        </div>
        <span class="badge {err_status}">Threshold: Error Rate &le; 2%</span>
      </div>
      <div class="metric-values">
        <div class="metric-item"><span class="metric-val" style="color: {var_err_color(err_val)}">{err_val}%</span><span class="metric-lbl">Error Rate</span></div>
        <div class="metric-item"><span class="metric-val" style="color: var(--success);">{data.get("retrieval_success_rate", 100)}%</span><span class="metric-lbl">Retrieval Success</span></div>
        <div class="metric-item"><span class="metric-val">{data.get("failed_requests", 0)}</span><span class="metric-lbl">Failed Count</span></div>
      </div>
      <div class="chart-box"><canvas id="errorChart"></canvas></div>
      <div class="threshold-note">Guardrail: error_rate &le; 2% and retrieval_success_rate &ge; 90%.</div>
    </div>

    <!-- Panel 4: Cost -->
    <div class="panel">
      <div class="panel-header">
        <div>
          <div class="panel-title">4. Cost over time</div>
          <div class="panel-desc">Unit: USD ($) | Source: data/logs.jsonl</div>
        </div>
        <span class="badge {cost_status}">Threshold: Total &le; $2.50</span>
      </div>
      <div class="metric-values">
        <div class="metric-item"><span class="metric-val">${cost_val:.6f}</span><span class="metric-lbl">Total Cost</span></div>
      </div>
      <div class="chart-box"><canvas id="costChart"></canvas></div>
      <div class="threshold-note">Calculated from tokens_in ($3/1M) and tokens_out ($15/1M).</div>
    </div>

    <!-- Panel 5: Tokens -->
    <div class="panel">
      <div class="panel-header">
        <div>
          <div class="panel-title">5. Input and output tokens</div>
          <div class="panel-desc">Unit: tokens | Source: data/logs.jsonl</div>
        </div>
        <span class="badge status-ok">Threshold: &le; 50,000 tokens</span>
      </div>
      <div class="metric-values">
        <div class="metric-item"><span class="metric-val">{data.get("tokens_in", 0)}</span><span class="metric-lbl">Input Tokens</span></div>
        <div class="metric-item"><span class="metric-val">{data.get("tokens_out", 0)}</span><span class="metric-lbl">Output Tokens</span></div>
        <div class="metric-item"><span class="metric-val">{data.get("tokens_in", 0) + data.get("tokens_out", 0)}</span><span class="metric-lbl">Total Tokens</span></div>
      </div>
      <div class="chart-box"><canvas id="tokenChart"></canvas></div>
      <div class="threshold-note">Sum of tokens per response_sent event.</div>
    </div>

    <!-- Panel 6: Quality -->
    <div class="panel">
      <div class="panel-header">
        <div>
          <div class="panel-title">6. Quality proxy</div>
          <div class="panel-desc">Unit: score_0_to_1 | Source: data/logs.jsonl</div>
        </div>
        <span class="badge {qual_status}">Threshold: Mean &ge; 0.75</span>
      </div>
      <div class="metric-values">
        <div class="metric-item"><span class="metric-val" style="color: {var_qual_color(qual_val)}">{qual_val:.2f} / 1.0</span><span class="metric-lbl">Avg Quality</span></div>
      </div>
      <div class="chart-box"><canvas id="qualityChart"></canvas></div>
      <div class="threshold-note">Heuristic score evaluating relevance, length, and redaction flags.</div>
    </div>
  </div>

  <script>
    const labels = {chart_labels};
    const latencies = {chart_latencies};
    const ttfts = {chart_ttfts};
    const costs = {chart_costs};

    // 1. Latency Chart
    new Chart(document.getElementById('latencyChart'), {{
      type: 'line',
      data: {{
        labels: labels,
        datasets: [
          {{ label: 'Latency (ms)', data: latencies, borderColor: '#38bdf8', backgroundColor: 'rgba(56, 189, 248, 0.1)', tension: 0.3 }},
          {{ label: 'TTFT (ms)', data: ttfts, borderColor: '#a78bfa', borderDash: [4, 4], tension: 0.3 }},
          {{ label: 'Threshold (3000ms)', data: Array(labels.length).fill(3000), borderColor: '#ef4444', borderDash: [6, 6], pointRadius: 0 }}
        ]
      }},
      options: {{ responsive: true, maintainAspectRatio: false, scales: {{ y: {{ beginAtZero: true }} }} }}
    }});

    // 2. Traffic Chart
    new Chart(document.getElementById('trafficChart'), {{
      type: 'bar',
      data: {{
        labels: {json.dumps(traffic_keys)},
        datasets: [{{ label: 'Requests / min', data: {json.dumps(traffic_vals)}, backgroundColor: '#38bdf8' }}]
      }},
      options: {{ responsive: true, maintainAspectRatio: false, scales: {{ y: {{ beginAtZero: true }} }} }}
    }});

    // 3. Error Chart
    new Chart(document.getElementById('errorChart'), {{
      type: 'doughnut',
      data: {{
        labels: ['Success', 'Errors'],
        datasets: [{{ data: [{data.get("total_requests", 0) - data.get("failed_requests", 0)}, {data.get("failed_requests", 0)}], backgroundColor: ['#10b981', '#ef4444'] }}]
      }},
      options: {{ responsive: true, maintainAspectRatio: false }}
    }});

    // 4. Cost Chart
    new Chart(document.getElementById('costChart'), {{
      type: 'line',
      data: {{
        labels: labels,
        datasets: [{{ label: 'Cost ($)', data: costs, borderColor: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.1)', tension: 0.3 }}]
      }},
      options: {{ responsive: true, maintainAspectRatio: false, scales: {{ y: {{ beginAtZero: true }} }} }}
    }});

    // 5. Token Chart
    new Chart(document.getElementById('tokenChart'), {{
      type: 'bar',
      data: {{
        labels: ['Tokens'],
        datasets: [
          {{ label: 'Input Tokens', data: [{data.get("tokens_in", 0)}], backgroundColor: '#38bdf8' }},
          {{ label: 'Output Tokens', data: [{data.get("tokens_out", 0)}], backgroundColor: '#818cf8' }}
        ]
      }},
      options: {{ responsive: true, maintainAspectRatio: false, scales: {{ x: {{ stacked: true }}, y: {{ stacked: true, beginAtZero: true }} }} }}
    }});

    // 6. Quality Chart
    new Chart(document.getElementById('qualityChart'), {{
      type: 'bar',
      data: {{
        labels: ['Quality Score'],
        datasets: [
          {{ label: 'Average Quality', data: [{qual_val}], backgroundColor: '#10b981' }},
          {{ label: 'Target Threshold (0.75)', data: [0.75], borderColor: '#f59e0b', type: 'line', borderDash: [6, 6] }}
        ]
      }},
      options: {{ responsive: true, maintainAspectRatio: false, scales: {{ y: {{ min: 0, max: 1 }} }} }}
    }});
  </script>
</body>
</html>
"""


def var_p95_color(val: float) -> str:
    return "#10b981" if val <= 3000 else "#ef4444"


def var_err_color(val: float) -> str:
    return "#10b981" if val <= 2.0 else "#ef4444"


def var_qual_color(val: float) -> str:
    return "#10b981" if val >= 0.75 else "#f59e0b"
