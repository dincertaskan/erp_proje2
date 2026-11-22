from collections import defaultdict
from datetime import date, datetime, time, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.core.security import require_admin
from app.models.erp import Order, OrderItem, Product
from app.schemas.order_schema import ORDER_STATUSES

# Raporlar yalnızca yöneticilere açıktır
router = APIRouter(prefix="/reports", tags=["Reports"], dependencies=[Depends(require_admin)])

DEFAULT_RANGE_DAYS = 30
MAX_RANGE_DAYS = 366 * 3
DAILY_GRANULARITY_MAX_DAYS = 62  # Daha uzun aralıklar aylık gruplanır
TOP_LIMIT = 10
MONTH_NAMES = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]
CANCELLED = "İptal"


def _r(value: float) -> float:
    return round(float(value), 2)


def _pct_change(current: float, previous: float) -> Optional[float]:
    """Önceki döneme göre % değişim. Önceki dönem 0 ise karşılaştırma yapılamaz (None)."""
    if not previous:
        return None
    return round((current - previous) / previous * 100, 1)


def _item_cost(item: OrderItem) -> float:
    # Sipariş anındaki maliyet yoksa (eski siparişler) ürünün güncel maliyeti kullanılır
    if item.unit_cost is not None:
        unit_cost = float(item.unit_cost)
    elif item.product is not None:
        unit_cost = float(item.product.cost_price or 0)
    else:
        unit_cost = 0.0
    return unit_cost * item.quantity


def _load_orders(db: Session, start: date, end: date) -> list[Order]:
    start_dt = datetime.combine(start, time.min)
    end_dt = datetime.combine(end + timedelta(days=1), time.min)
    return (
        db.query(Order)
        .options(joinedload(Order.items).joinedload(OrderItem.product).joinedload(Product.category))
        .filter(Order.created_at >= start_dt, Order.created_at < end_dt)
        .all()
    )


def _summary(orders: list[Order]) -> dict:
    valid = [o for o in orders if o.order_status != CANCELLED]
    revenue = sum(float(o.total_price) for o in valid)
    cost = sum(_item_cost(i) for o in valid for i in o.items)
    profit = revenue - cost
    cancelled = len(orders) - len(valid)
    return {
        "revenue": _r(revenue),
        "order_count": len(valid),
        "total_order_count": len(orders),
        "cancelled_count": cancelled,
        "cancel_rate": round(cancelled / len(orders) * 100, 1) if orders else 0.0,
        "avg_order_value": _r(revenue / len(valid)) if valid else 0.0,
        "items_sold": sum(i.quantity for o in valid for i in o.items),
        "cost": _r(cost),
        "gross_profit": _r(profit),
        "profit_margin": round(profit / revenue * 100, 1) if revenue else 0.0,
    }


def _timeseries(orders: list[Order], start: date, end: date, daily: bool) -> list[dict]:
    buckets: dict = {}
    if daily:
        day = start
        while day <= end:
            buckets[day] = {"label": day.strftime("%d.%m"), "revenue": 0.0, "orders": 0}
            day += timedelta(days=1)
    else:
        y, m = start.year, start.month
        while (y, m) <= (end.year, end.month):
            buckets[(y, m)] = {"label": f"{MONTH_NAMES[m - 1]} {y}", "revenue": 0.0, "orders": 0}
            y, m = (y + 1, 1) if m == 12 else (y, m + 1)

    for o in orders:
        if o.order_status == CANCELLED or o.created_at is None:
            continue
        key = o.created_at.date() if daily else (o.created_at.year, o.created_at.month)
        if key in buckets:
            buckets[key]["revenue"] += float(o.total_price)
            buckets[key]["orders"] += 1

    return [{**b, "revenue": _r(b["revenue"])} for b in buckets.values()]


def _breakdowns(orders: list[Order]) -> dict:
    valid = [o for o in orders if o.order_status != CANCELLED]

    products = defaultdict(lambda: {"quantity": 0, "revenue": 0.0, "cost": 0.0})
    categories = defaultdict(lambda: {"quantity": 0, "revenue": 0.0})
    customers = defaultdict(lambda: {"order_count": 0, "revenue": 0.0})
    payments = defaultdict(lambda: {"order_count": 0, "revenue": 0.0})

    for o in valid:
        cust_key = ("id", o.customer_id) if o.customer_id else ("name", o.customer_name)
        customers[cust_key]["name"] = o.customer_name
        customers[cust_key]["order_count"] += 1
        customers[cust_key]["revenue"] += float(o.total_price)

        method = o.payment_method or "Belirtilmemiş"
        payments[method]["order_count"] += 1
        payments[method]["revenue"] += float(o.total_price)

        for item in o.items:
            product = item.product
            category_name = product.category.name if product and product.category else "Genel"

            p = products[item.product_id]
            p["name"] = product.name if product else "Bilinmeyen Ürün"
            p["category"] = category_name
            p["quantity"] += item.quantity
            p["revenue"] += float(item.total_price)
            p["cost"] += _item_cost(item)

            c = categories[category_name]
            c["quantity"] += item.quantity
            c["revenue"] += float(item.total_price)

    top_products = sorted(
        (
            {
                "product_id": pid,
                "name": p["name"],
                "category": p["category"],
                "quantity": p["quantity"],
                "revenue": _r(p["revenue"]),
                "profit": _r(p["revenue"] - p["cost"]),
                "profit_margin": round((p["revenue"] - p["cost"]) / p["revenue"] * 100, 1) if p["revenue"] else 0.0,
            }
            for pid, p in products.items()
        ),
        key=lambda x: x["revenue"],
        reverse=True,
    )[:TOP_LIMIT]

    category_sales = sorted(
        ({"name": name, "quantity": c["quantity"], "revenue": _r(c["revenue"])} for name, c in categories.items()),
        key=lambda x: x["revenue"],
        reverse=True,
    )

    top_customers = sorted(
        ({"name": c["name"], "order_count": c["order_count"], "revenue": _r(c["revenue"])} for c in customers.values()),
        key=lambda x: x["revenue"],
        reverse=True,
    )[:TOP_LIMIT]

    payment_methods = sorted(
        ({"method": m, "order_count": p["order_count"], "revenue": _r(p["revenue"])} for m, p in payments.items()),
        key=lambda x: x["revenue"],
        reverse=True,
    )

    # Durum dağılımı iptal edilenler dahil tüm siparişleri kapsar
    status_counts = {s: {"status": s, "count": 0, "amount": 0.0} for s in ORDER_STATUSES}
    for o in orders:
        entry = status_counts.setdefault(o.order_status, {"status": o.order_status, "count": 0, "amount": 0.0})
        entry["count"] += 1
        entry["amount"] += float(o.total_price)
    status_breakdown = [{**s, "amount": _r(s["amount"])} for s in status_counts.values()]

    return {
        "top_products": top_products,
        "category_sales": category_sales,
        "top_customers": top_customers,
        "payment_methods": payment_methods,
        "status_breakdown": status_breakdown,
    }


def _inventory(db: Session) -> dict:
    products = db.query(Product).options(joinedload(Product.category)).all()
    by_category = defaultdict(lambda: {"product_count": 0, "stock": 0, "cost_value": 0.0, "sale_value": 0.0})
    totals = {"product_count": 0, "stock": 0, "cost_value": 0.0, "sale_value": 0.0,
              "out_of_stock_count": 0, "critical_count": 0}

    for p in products:
        stock = p.stock or 0
        cost_value = stock * float(p.cost_price or 0)
        sale_value = stock * float(p.unit_price or 0)
        c = by_category[p.category.name if p.category else "Genel"]
        for target in (c, totals):
            target["product_count"] += 1
            target["stock"] += stock
            target["cost_value"] += cost_value
            target["sale_value"] += sale_value
        if stock <= 0:
            totals["out_of_stock_count"] += 1
        if stock <= (p.min_stock or 0):
            totals["critical_count"] += 1

    categories = sorted(
        (
            {
                "name": name,
                "product_count": c["product_count"],
                "stock": c["stock"],
                "cost_value": _r(c["cost_value"]),
                "sale_value": _r(c["sale_value"]),
                "potential_profit": _r(c["sale_value"] - c["cost_value"]),
            }
            for name, c in by_category.items()
        ),
        key=lambda x: x["cost_value"],
        reverse=True,
    )

    return {
        **{k: (_r(v) if isinstance(v, float) else v) for k, v in totals.items()},
        "potential_profit": _r(totals["sale_value"] - totals["cost_value"]),
        "categories": categories,
    }


@router.get("/sales")
def get_sales_report(
    start: Optional[date] = Query(None, description="Başlangıç tarihi (YYYY-AA-GG)"),
    end: Optional[date] = Query(None, description="Bitiş tarihi (YYYY-AA-GG)"),
    db: Session = Depends(get_db),
):
    """Seçilen tarih aralığının satış, kârlılık ve stok raporunu döner."""
    end = end or date.today()
    start = start or end - timedelta(days=DEFAULT_RANGE_DAYS - 1)
    if start > end:
        raise HTTPException(status_code=400, detail="Başlangıç tarihi bitiş tarihinden sonra olamaz.")

    days = (end - start).days + 1
    if days > MAX_RANGE_DAYS:
        raise HTTPException(status_code=400, detail="Rapor aralığı en fazla 3 yıl olabilir.")

    # Karşılaştırma için aynı uzunlukta bir önceki dönem
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=days - 1)

    orders = _load_orders(db, start, end)
    summary = _summary(orders)
    previous = _summary(_load_orders(db, prev_start, prev_end))
    daily = days <= DAILY_GRANULARITY_MAX_DAYS

    return {
        "period": {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "days": days,
            "granularity": "daily" if daily else "monthly",
            "previous_start": prev_start.isoformat(),
            "previous_end": prev_end.isoformat(),
        },
        "summary": summary,
        "previous": previous,
        "changes": {
            "revenue": _pct_change(summary["revenue"], previous["revenue"]),
            "order_count": _pct_change(summary["order_count"], previous["order_count"]),
            "avg_order_value": _pct_change(summary["avg_order_value"], previous["avg_order_value"]),
            "gross_profit": _pct_change(summary["gross_profit"], previous["gross_profit"]),
        },
        "timeseries": _timeseries(orders, start, end, daily),
        **_breakdowns(orders),
        "inventory": _inventory(db),
    }
