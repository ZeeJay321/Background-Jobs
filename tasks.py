import csv
from sqlalchemy.exc import IntegrityError
import uuid
from datetime import datetime
from celery_config import celery
from sqlalchemy import func
from database import SessionLocal
from models import Order, OrderItem, OrderSummary, Product, ProductVariant


@celery.task(name="tasks.get_order_summary")
def get_order_summary_task():
    db = SessionLocal()
    try:
        last_summary = db.query(OrderSummary).order_by(OrderSummary.createdAt.desc()).first()

        if last_summary:
            last_summary_time = last_summary.createdAt
            print(f"📅 Last summary created at: {last_summary_time}")

            new_orders_query = db.query(Order).filter(Order.createdAt > last_summary_time)
            new_order_items_query = (
                db.query(OrderItem)
                .join(Order, OrderItem.orderId == Order.id)
                .filter(Order.createdAt > last_summary_time)
            )

            new_total_orders = new_orders_query.count()
            new_total_products = db.query(func.coalesce(func.sum(OrderItem.quantity), 0))\
                .join(Order, OrderItem.orderId == Order.id)\
                .filter(Order.createdAt > last_summary_time)\
                .scalar() or 0
            new_total_amount = db.query(func.coalesce(func.sum(Order.amount), 0.0))\
                .filter(Order.createdAt > last_summary_time)\
                .scalar() or 0.0

            print(
                f"🆕 New since last summary -> orders: {new_total_orders}, "
                f"products: {new_total_products}, amount: {new_total_amount}"
            )

            if new_total_orders > 0 or new_total_products > 0 or new_total_amount > 0:
                new_summary = OrderSummary(
                    id=str(uuid.uuid4()),
                    totalOrders=last_summary.totalOrders + new_total_orders,
                    totalProductsInOrders=last_summary.totalProductsInOrders + new_total_products,
                    totalOrderAmount=last_summary.totalOrderAmount + new_total_amount
                )
                db.add(new_summary)
                db.commit()
                print(f"✅ Created incremental OrderSummary: {new_summary.id}")
            else:
                print("ℹ️ No new orders since last summary. Skipping creation.")

        else:
            print("🆕 No previous summary found. Creating initial summary.")
            total_orders = db.query(func.count(Order.id)).scalar() or 0
            total_products = db.query(func.coalesce(func.sum(OrderItem.quantity), 0)).scalar() or 0
            total_amount = db.query(func.coalesce(func.sum(Order.amount), 0.0)).scalar() or 0.0

            new_summary = OrderSummary(
                id=str(uuid.uuid4()),
                totalOrders=total_orders,
                totalProductsInOrders=total_products,
                totalOrderAmount=total_amount
            )
            db.add(new_summary)
            db.commit()
            print(f"✅ Created initial OrderSummary: {new_summary.id}")

        return {"status": "success"}

    except Exception as e:
        db.rollback()
        print("❌ Error while saving order summary:", str(e))
        raise
    finally:
        db.close()


@celery.task(name="tasks.import_products_from_csv")
def import_products_from_csv(csv_path: str):
    """
    Import Products and Variants from CSV.

    CSV STRUCTURE:
    product_index,title,color,colorCode,size,img,price,stock
    """

    db = SessionLocal()
    imported_count = 0
    skipped_count = 0
    products_cache = {}
    chunk = 400

    print(f"📂 Starting product import from: {csv_path}")

    try:
        with open(csv_path, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for i, row in enumerate(reader, start=1):
                try:
                    product_index = row.get("product_index")
                    title = row.get("title", "").strip()

                    if not product_index:
                        raise ValueError("product_index is required")

                    product = products_cache.get(product_index)

                    if not product:
                        product = Product(
                            id=str(uuid.uuid4()),
                            title=title,
                            createdAt=datetime.utcnow(),
                            updatedAt=datetime.utcnow(),
                        )
                        db.add(product)
                        db.commit()
                        products_cache[product_index] = product

                    variant = ProductVariant(
                        id=str(uuid.uuid4()),
                        productId=product.id,
                        color=row.get("color", "").strip(),
                        colorCode=row.get("colorCode") or None,
                        size=row.get("size") or "M",
                        img=row.get("img", "").strip(),
                        price=float(row.get("price") or 0),
                        stock=int(row.get("stock") or 0),
                        createdAt=datetime.utcnow(),
                        updatedAt=datetime.utcnow(),
                    )

                    db.add(variant)
                    db.commit()
                    imported_count += 1

                    if i % chunk == 0:
                        print(f"✅ Imported {i} rows so far...")

                except IntegrityError as e:
                    db.rollback()
                    skipped_count += 1
                    print(f"⚠️ Skipped row {i} — IntegrityError: {e.orig}")

                except Exception as e:
                    db.rollback()
                    skipped_count += 1
                    print(f"❌ Error at row {i}: {str(e)}")


        print(f"🎉 Import complete! Imported: {imported_count}, Skipped: {skipped_count}")
        return {"imported": imported_count, "skipped": skipped_count}

    except FileNotFoundError:
        print(f"❌ File not found: {csv_path}")
        return {"error": "CSV file not found"}

    except Exception as e:
        db.rollback()
        print(f"❌ Unexpected error during import: {str(e)}")
        raise

    finally:
        db.close()