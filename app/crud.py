from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session
from app import models, schemas


def get_product(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()


def get_products(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Product).offset(skip).limit(limit).all()


def create_product(db: Session, product: schemas.ProductCreate):
    db_product = models.Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def create_order(db: Session, order: schemas.OrderCreate):
    # Проверка наличия достаточного количества товара на складе
    for item in order.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if product is None or product.quantity < item.quantity:
            raise HTTPException(status_code=400, detail=f"Not enough stock for product ID: {item.product_id}")

    # Создание заказа
    db_order = models.Order(status=order.status, creation_date=datetime.utcnow())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    # Добавление элементов заказа и уменьшение количества товара на складе
    for item in order.items:
        db_order_item = models.OrderItem(order_id=db_order.id, product_id=item.product_id, quantity=item.quantity)
        db.add(db_order_item)

        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if product:
            product.quantity -= item.quantity
            db.commit()
            db.refresh(product)

    db.commit()
    db.refresh(db_order)
    return db_order


def get_order(db: Session, order_id: int):
    return db.query(models.Order).filter(models.Order.id == order_id).first()


def get_orders(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Order).offset(skip).limit(limit).all()


def update_order_status(db: Session, order_id: int, status: str):
    db_order = get_order(db, order_id)
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    db_order.status = status
    db.commit()
    db.refresh(db_order)
    return db_order
