"""Microservicio de CLIENTES (puerto 8002) - administra los clientes."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Microservicio de Clientes")

clientes = [
    {"id": 1, "nombre": "Ana Pérez", "email": "ana@correo.com"},
    {"id": 2, "nombre": "Luis Gómez", "email": "luis@correo.com"},
]


class ClienteIn(BaseModel):
    nombre: str = Field(min_length=1)
    email: str = Field(min_length=3)


@app.get("/health")
def health():
    return {"servicio": "clientes", "estado": "ok"}


@app.get("/clientes")
def listar_clientes():
    return clientes


@app.get("/clientes/{cliente_id}")
def obtener_cliente(cliente_id: int):
    for c in clientes:
        if c["id"] == cliente_id:
            return c
    raise HTTPException(status_code=404, detail="Cliente no encontrado")


@app.post("/clientes", status_code=201)
def registrar_cliente(datos: ClienteIn):
    nuevo = {"id": max((c["id"] for c in clientes), default=0) + 1, **datos.model_dump()}
    clientes.append(nuevo)
    return nuevo
