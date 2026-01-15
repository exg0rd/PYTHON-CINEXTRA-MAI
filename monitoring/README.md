# Cinema Platform Monitoring

## Overview

This directory contains monitoring configuration for the Cinema Platform using Prometheus and Grafana.

## Components

### Prometheus (`prometheus.yml`)
Collects metrics from:
- Backend API (FastAPI) - port 8000
- Redis - port 6379
- MinIO - port 9000
- PostgreSQL - port 5432
- Celery Workers - port 9540

### Grafana
Visualizes metrics with pre-configured dashboards.

## Dashboard Features

The Cinema Platform Dashboard includes:

### 1. API Response Time Panel
- **Average Response Time**: Mean response time across all requests
- **95th Percentile**: 95% of requests complete within this time
- **99th Percentile**: 99% of requests complete within this time

### 2. Current Avg Response Time Gauge
- Real-time average response time
- Color-coded thresholds:
  - Green: < 0.5s
  - Yellow: 0.5s - 1s
  - Red: > 1s

### 3. Request Rate Gauge
- Current requests per second
- Shows system load

### 4. Response Time by Endpoint
- Breakdown of response times per API endpoint
- Helps identify slow endpoints

### 5. HTTP Status Rates
- Success rate (2xx responses)
- Error rate (5xx responses)
- Percentage-based visualization

### 6. Celery Task Status
- Successful tasks
- Failed tasks
- Pending tasks

### 7. MinIO Storage Usage
- Storage usage per bucket
- Tracks video, thumbnail, and manifest storage

## Access

After starting the system:

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3002
  - Username: `admin`
  - Password: `admin`

## Setup

### 1. Start Monitoring Services

```bash
# Start all services including monitoring
./start-full-system.sh

# Or start only monitoring
./start-monitoring.sh
```

### 2. Access Grafana

1. Open http://localhost:3002
2. Login with admin/admin
3. Navigate to Dashboards → Cinema Platform Dashboard

### 3. Verify Data Source

1. Go to Configuration → Data Sources
2. Verify Prometheus is connected
3. URL should be: `http://prometheus:9090`

## Metrics Endpoints

### Backend API
```
GET http://localhost:8000/metrics
```

Returns Prometheus-formatted metrics including:
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request duration histogram
- `http_requests_in_progress` - Current active requests

### Example Metrics
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",path="/api/movies",status="200"} 1234

# HELP http_request_duration_seconds HTTP request duration
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{le="0.1"} 100
http_request_duration_seconds_bucket{le="0.5"} 450
http_request_duration_seconds_bucket{le="1.0"} 890
```

## Useful Prometheus Queries

### Response Time Queries

```promql
# Average response time (last 5 minutes)
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])

# 95th percentile response time
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# 99th percentile response time
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

# Response time by endpoint
rate(http_request_duration_seconds_sum{path=~"/api/.*"}[5m]) / rate(http_request_duration_seconds_count{path=~"/api/.*"}[5m])
```

### Request Rate Queries

```promql
# Total requests per second
rate(http_requests_total[5m])

# Requests per second by status code
rate(http_requests_total{status="200"}[5m])

# Error rate percentage
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100
```

### Celery Queries

```promql
# Tasks in queue
celery_tasks_total{state="pending"}

# Task success rate
rate(celery_tasks_total{state="success"}[5m])

# Task failure rate
rate(celery_tasks_total{state="failure"}[5m])
```

## Alerts

Alert rules are defined in `alert_rules.yml`:

- High error rate (>5%)
- Slow response time (>1s)
- Low disk space (<10%)
- Failed Celery tasks

## Troubleshooting

### Dashboard Not Loading

1. Check Grafana logs:
```bash
sudo docker logs cinema_grafana
```

2. Verify dashboard file exists:
```bash
ls -la monitoring/grafana/dashboards/cinema-dashboard.json
```

3. Restart Grafana:
```bash
sudo docker restart cinema_grafana
```

### No Data in Panels

1. Check Prometheus targets: http://localhost:9090/targets
2. Verify backend is exporting metrics: http://localhost:8000/metrics
3. Check Prometheus logs:
```bash
sudo docker logs cinema_prometheus
```

### Metrics Not Updating

1. Verify scrape interval in `prometheus.yml` (default: 15s)
2. Check if backend is running
3. Verify network connectivity between containers

## Customization

### Adding New Panels

1. Edit `cinema-dashboard.json`
2. Add new panel configuration
3. Restart Grafana or wait for auto-reload (10s)

### Modifying Thresholds

Edit the `thresholds` section in panel configuration:

```json
"thresholds": {
  "mode": "absolute",
  "steps": [
    {"color": "green", "value": null},
    {"color": "yellow", "value": 0.5},
    {"color": "red", "value": 1}
  ]
}
```

### Adding New Metrics

1. Add metric export in backend code
2. Update `prometheus.yml` if needed
3. Create new panel in Grafana dashboard

## Best Practices

1. **Monitor regularly**: Check dashboards daily
2. **Set up alerts**: Configure alert notifications
3. **Track trends**: Look for patterns over time
4. **Optimize slow endpoints**: Use response time data to identify bottlenecks
5. **Capacity planning**: Monitor storage and resource usage

## Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [PromQL Basics](https://prometheus.io/docs/prometheus/latest/querying/basics/)
