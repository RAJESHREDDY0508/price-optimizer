# Dynamic E-Commerce Price Optimization Engine (MVP)

A minimal, production-style price optimization service you can run with Docker Compose:
- **pricing-api** (FastAPI) — returns an optimized price per SKU
- **frontend** (Flask) — tiny UI to test inputs and see optimized price
- **Postgres** — SKU baselines (base price, cost, inventory, competitor price)
- **Redis** — short-term cache to reduce compute/DB load

> This is an MVP blueprint designed to be extended with real models, MLflow, Airflow/Prefect, and Kubernetes later.

---

## 🧭 Architecture

```mermaid
flowchart LR
  U[User] --> FE[Frontend (Flask)]
  FE --> API[Pricing API (FastAPI)]
  API --> R[(Redis)]
  API --> PG[(Postgres)]
...diagram...

