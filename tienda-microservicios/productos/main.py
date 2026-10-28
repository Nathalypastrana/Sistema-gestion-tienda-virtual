"""Microservicio de PRODUCTOS (puerto 8001) - administra el catálogo."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Microservicio de Productos")

# Lista en memoria (en un sistema real: base de datos propia del servicio)
productos = [
    {"id": 1, "nombre": "Camiseta", "precio": 35000.0, "stock": 50},
    {"id": 2, "nombre": "Zapatos", "precio": 120000.0, "stock": 20},
]


class ProductoIn(BaseModel):
    nombre: str = Field(min_length=1)
    precio: float = Field(gt=0)
    stock: int = Field(ge=0)


@app.get("/health")
def health():
    return {"servicio": "productos", "estado": "ok"}


@app.get("/productos")
def listar_productos():
    return productos


@app.get("/productos/{producto_id}")
def obtener_producto(producto_id: int):
    for p in productos:
        if p["id"] == producto_id:
            return p
    raise HTTPException(status_code=404, detail="Producto no encontrado")


@app.post("/productos", status_code=201)
def registrar_producto(datos: ProductoIn):
    nuevo = {"id": max((p["id"] for p in productos), default=0) + 1, **datos.model_dump()}
    productos.append(nuevo)
    return nuevo
