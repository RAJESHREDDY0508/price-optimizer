# services/pricing-api/app/main.py
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict

app = FastAPI(title="Dynamic E-Commerce Price Optimization Engine (MVP)",
              version="1.0.0",
              description="Simple pricing API that combines baseline data, a dummy ML model, and business rules to suggest prices.")


# ------------------------------
# In-memory baseline "store"
# ------------------------------
# You can later replace this with Postgres (or any DB).
SKU_BASELINES: Dict[str, Dict] = {
    # Example seed
    "SKU123": {
        "base_price": 100.0,
        "cost": 70.0,
        "inventory": 800,
        "competitor_price": 110.0,
        "seasonality": 1.0
    }
}


# ------------------------------
# Dummy model
# ------------------------------
class DummyModel:
    """
    Very basic pricing logic:
    - Adds a small premium if competitor > base, otherwise applies a small discount.
    - Small discount if inventory is high (clearance pressure).
    """
    def predict_price(self, base_price: float, competitor_price: float, inventory: int) -> float:
        premium = 0.05 if competitor_price > base_price else -0.03
        inv_disc = -0.05 if inventory > 500 else 0.0
        return base_price * (1 + premium + inv_disc)


MODEL = DummyModel()


# ------------------------------
# Business rules
# ------------------------------
DEFAULT_RULES = {
    "min_margin_pct": 0.12,               # minimum margin on top of cost
    "max_above_competitor_pct": 0.15,     # cap relative to competitor
    "clearance_inventory": 1000,          # if inventory above this, push price down
    "clearance_discount_pct": 0.10,       # 10% off base price when in clearance
    # Optional "min_price" / "max_price" keys can be added per SKU if needed
}


def apply_rules(
    predicted_price: float,
    base: Dict,
    rules: Dict,
    competitor_price: Optional[float]
) -> float:
    price = predicted_price

    # Enforce minimum margin floor
    min_margin = rules.get("min_margin_pct", 0.12)
    min_price = max(base["cost"] * (1 + min_margin), rules.get("min_price", 0.0))
    price = max(price, min_price)

    # Cap relative to competitor if provided
    if competitor_price is not None:
        cap = rules.get("max_above_competitor_pct", 0.15)
        price = min(price, competitor_price * (1 + cap))

    # Clearance behavior if inventory high
    if base.get("inventory", 0) > rules.get("clearance_inventory", 1000):
        price = min(price, base["base_price"] * (1 - rules.get("clearance_discount_pct", 0.10)))

    # Optional hard max cap
    if "max_price" in rules:
        price = min(price, rules["max_price"])

    return round(float(price), 2)


# ------------------------------
# Request/Response models
# ------------------------------
class PriceQuery(BaseModel):
    sku: str = Field(..., description="Product SKU")
    competitor_price: Optional[float] = Field(None, ge=0, description="Latest competitor price (optional)")


class UpsertBaseline(BaseModel):
    sku: str
    base_price: float = Field(..., ge=0)
    cost: float = Field(..., ge=0)
    inventory: int = Field(0, ge=0)
    competitor_price: Optional[float] = Field(None, ge=0)
    seasonality: float = Field(1.0, ge=0)


# ------------------------------
# Endpoints
# ------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/price")
def get_price(
    sku: str = Query(..., description="Product SKU"),
    competitor_price: Optional[float] = Query(default=None, ge=0, description="Latest competitor price (optional)")
):
    """
    GET /price?sku=SKU123&competitor_price=109
    Returns: {"sku": "...", "price": 123.45}
    """
    base = SKU_BASELINES.get(sku)
    if not base:
        raise HTTPException(status_code=404, detail=f"SKU '{sku}' not found. Upsert it via POST /baseline first.")

    comp = competitor_price if competitor_price is not None else base.get("competitor_price", base["base_price"])
    predicted = MODEL.predict_price(
        base_price=base["base_price"],
        competitor_price=comp,
        inventory=base.get("inventory", 0),
    )
    price = apply_rules(predicted, base, DEFAULT_RULES, competitor_price)
    return {"sku": sku, "price": price}


@app.post("/price")
def post_price(payload: PriceQuery):
    """
    POST /price
    body: {"sku": "SKU123", "competitor_price": 109}
    """
    base = SKU_BASELINES.get(payload.sku)
    if not base:
        raise HTTPException(status_code=404, detail=f"SKU '{payload.sku}' not found. Upsert it via POST /baseline first.")

    comp = payload.competitor_price if payload.competitor_price is not None else base.get("competitor_price", base["base_price"])
    predicted = MODEL.predict_price(
        base_price=base["base_price"],
        competitor_price=comp,
        inventory=base.get("inventory", 0),
    )
    price = apply_rules(predicted, base, DEFAULT_RULES, payload.competitor_price)
    return {"sku": payload.sku, "price": price}


@app.post("/baseline")
def upsert_baseline(payload: UpsertBaseline):
    """
    Upsert baseline data for a SKU (simulate a DB).
    """
    SKU_BASELINES[payload.sku] = payload.model_dump()
    return {"status": "ok", "message": f"Baseline upserted for {payload.sku}"}


# ------------------------------
# Local dev entrypoint
# ------------------------------
# Run with: uvicorn app.main:app --reload --port 8080
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)

