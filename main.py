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
    
# Soal 3: Customer di Atas Rata-Rata Belanja (Subquery)

@app.get("/reports/customer-above-average")
def customer_above_average():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT nama, total_belanja
        FROM (
            SELECT
                c.id,
                c.nama,
                SUM(o.jumlah * p.harga) AS total_belanja
            FROM customers c
            JOIN orders o ON o.customer_id = c.id
            JOIN products p ON p.id = o.product_id
            GROUP BY c.id, c.nama
        ) AS customer_totals
        WHERE total_belanja > (
            SELECT AVG(total_per_customer)
            FROM (
                SELECT SUM(o.jumlah * p.harga) AS total_per_customer
                FROM orders o
                JOIN products p ON p.id = o.product_id
                GROUP BY o.customer_id
            )
        )
        ORDER BY total_belanja DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
    
# Soal 4: Produk Terlaris per Kategori (CTE)

@app.get("/reports/top-product-by-category")
def top_product_by_category():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        WITH product_sales AS (
            SELECT
                p.kategori,
                p.nama_produk,
                SUM(o.jumlah) AS total_terjual
            FROM products p
            JOIN orders o ON o.product_id = p.id
            GROUP BY p.id, p.kategori, p.nama_produk
        ),
        ranked_sales AS (
            SELECT
                kategori,
                nama_produk,
                total_terjual,
                RANK() OVER (
                    PARTITION BY kategori
                    ORDER BY total_terjual DESC
                ) AS peringkat
            FROM product_sales
        )
        SELECT kategori, nama_produk, total_terjual
        FROM ranked_sales
        WHERE peringkat = 1
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
    
# Soal 5: Klasifikasi Customer (CTE + CASE Statement)

@app.get("/reports/customer-level")
def customer_level():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        WITH customer_totals AS (
            SELECT
                c.nama,
                SUM(o.jumlah * p.harga) AS total_belanja
            FROM customers c
            JOIN orders o ON o.customer_id = c.id
            JOIN products p ON p.id = o.product_id
            GROUP BY c.id, c.nama
        )
        SELECT
            nama,
            total_belanja,
            CASE
                WHEN total_belanja > 5000000 THEN 'VIP'
                WHEN total_belanja BETWEEN 1000000 AND 5000000 THEN 'Regular'
                ELSE 'Basic'
            END AS level_customer
        FROM customer_totals
        ORDER BY total_belanja DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
    

# Tantangan Tambahan 1: Produk yang Belum Pernah Dibeli

@app.get("/reports/unsold-products")
def unsold_products():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, p.nama_produk, p.kategori, p.harga
        FROM products p
        LEFT JOIN orders o ON o.product_id = p.id
        WHERE o.id IS NULL
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# Tantangan Tambahan 2: Kategori dengan Total Penjualan Tertinggi

@app.get("/reports/top-category")
def top_category():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            p.kategori,
            SUM(o.jumlah * p.harga) AS total_penjualan
        FROM products p
        JOIN orders o ON o.product_id = p.id
        GROUP BY p.kategori
        ORDER BY total_penjualan DESC
        LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="No sales data found")
    return dict(row)
    

# Tantangan Tambahan 3: Customer Beli Lebih dari Satu Jenis Produk

@app.get("/reports/multi-product-customers")
def multi_product_customers():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            c.nama,
            COUNT(DISTINCT o.product_id) AS jumlah_jenis_produk
        FROM customers c
        JOIN orders o ON o.customer_id = c.id
        GROUP BY c.id, c.nama
        HAVING COUNT(DISTINCT o.product_id) > 1
        ORDER BY jumlah_jenis_produk DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
