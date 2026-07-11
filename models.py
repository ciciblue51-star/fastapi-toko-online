from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    nama_produk: str
    kategori: str
    harga: int = Field(gt=0, description="Harga harus lebih dari 0")


class ProductUpdate(BaseModel):
    nama_produk: str
    kategori: str
    harga: int = Field(gt=0, description="Harga harus lebih dari 0")


class ProductResponse(BaseModel):
    id: int
    nama_produk: str
    kategori: str
    harga: int
