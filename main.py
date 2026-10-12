
import os
from decimal import Decimal

from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, Numeric
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker, Session

app = FastAPI(title="Product Display Application")
templates = Jinja2Templates(directory="templates")

DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username=os.getenv("DB_USERNAME", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "3306")),
    database=os.getenv("DB_NAME", "product_db"),
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    image_url = Column(String(500), nullable=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


Base.metadata.create_all(bind=engine)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={},
    )


@app.get("/products", response_class=HTMLResponse)
def products(request: Request, db: Session = Depends(get_db)):
    product_list = db.query(Product).order_by(Product.id).all()

    return templates.TemplateResponse(
        request=request,
        name="product.html",
        context={"products": product_list},
    )


@app.post("/products/add")
def add_product(
    name: str = Form(..., min_length=1, max_length=100),
    price: Decimal = Form(..., gt=0),
    image_url: str = Form("", max_length=500),
    db: Session = Depends(get_db),
):
    clean_name = name.strip()
    clean_image_url = image_url.strip()

    if not clean_name:
        raise HTTPException(
            status_code=400,
            detail="Product name cannot be empty",
        )

    if clean_image_url and not clean_image_url.startswith(
        ("https://", "http://")
    ):
        raise HTTPException(
            status_code=400,
            detail="Image URL must start with http:// or https://",
        )

    new_product = Product(
        name=clean_name,
        price=price,
        image_url=clean_image_url or None,
    )

    db.add(new_product)
    db.commit()

    return RedirectResponse(url="/products", status_code=303)
