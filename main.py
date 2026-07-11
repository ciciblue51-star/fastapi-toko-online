from fastapi import FastAPI, HTTPException
from database import init_db, get_connection
from models import ProductCreate, ProductUpdate, ProductResponse

app = FastAPI(title="Toko Online API")


@app.on_event("startup")
def on_startup():
    init_db()

# Soal 1: CRUD Dasar untuk Products

@app.post("/products", response_model=ProductResponse)
def create_product(product: ProductCreate):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO products (nama_produk, kategori, harga) VALUES (?, ?, ?)",
        (product.nama_produk, product.kategori, product.harga),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return {**product.dict(), "id": new_id}


@app.get("/products", response_model=list[ProductResponse])
def get_all_products():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    row = cursor.fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return dict(row)


@app.put("/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, product: ProductUpdate):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    row = cursor.fetchone()
    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Product not found")

    cursor.execute(
        "UPDATE products SET nama_produk = ?, kategori = ?, harga = ? WHERE id = ?",
        (product.nama_produk, product.kategori, product.harga, product_id),
    )
    conn.commit()
    conn.close()
    return {**product.dict(), "id": product_id}


@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    row = cursor.fetchone()
    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Product not found")

    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    return {"message": "Product deleted successfully"}     
    
# Soal 2: Total Belanja Customers (JOIN + SUM)

@app.get("/reports/customer-total")
def customer_total():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            c.nama,
            SUM(o.jumlah * p.harga) AS total_belanja
        FROM customers c
        JOIN orders o ON o.customer_id = c.id
        JOIN products p ON p.id = o.product_id
        GROUP BY c.id, c.nama
        ORDER BY total_belanja DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
    
