"""Microservicio de PEDIDOS (puerto 8003) - gestiona pedidos y su estado.

Tolerancia a fallos:
- Llama a Productos y Clientes por HTTP con timeout corto y reintentos.
- Si alguno no responde, el pedido NO se pierde: queda en estado
  PENDIENTE_VALIDACION y se puede revalidar luego con POST /pedidos/reintentar.
- Consultar pedidos nunca depende de otros servicios.
"""
import os

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

PRODUCTOS_URL = os.getenv("PRODUCTOS_URL", "http://localhost:8001")
CLIENTES_URL = os.getenv("CLIENTES_URL", "http://localhost:8002")
TIMEOUT = 2.0
REINTENTOS = 2

app = FastAPI(title="Microservicio de Pedidos")

pedidos: list[dict] = []


class PedidoIn(BaseModel):
    cliente_id: int
    producto_id: int
    cantidad: int = Field(gt=0)


class ServicioNoDisponible(Exception):
    def __init__(self, servicio: str):
        self.servicio = servicio


def consultar(url: str, servicio: str):
    """GET con reintentos. Devuelve el JSON, None si 404; lanza ServicioNoDisponible si falla la red."""
    for _ in range(REINTENTOS):
        try:
            r = httpx.get(url, timeout=TIMEOUT)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.json()
        except (httpx.TransportError, httpx.HTTPStatusError):
            continue
    raise ServicioNoDisponible(servicio)


def validar(pedido: dict):
    """Valida cliente y producto. Actualiza el estado del pedido según el resultado."""
    try:
        cliente = consultar(f"{CLIENTES_URL}/clientes/{pedido['cliente_id']}", "clientes")
        producto = consultar(f"{PRODUCTOS_URL}/productos/{pedido['producto_id']}", "productos")
    except ServicioNoDisponible as e:
        pedido["estado"] = "PENDIENTE_VALIDACION"
        pedido["detalle"] = f"Servicio '{e.servicio}' no disponible; se reintentará"
        return

    if cliente is None:
        pedido["estado"], pedido["detalle"] = "RECHAZADO", "Cliente no existe"
    elif producto is None:
        pedido["estado"], pedido["detalle"] = "RECHAZADO", "Producto no existe"
    elif producto["stock"] < pedido["cantidad"]:
        pedido["estado"], pedido["detalle"] = "RECHAZADO", "Stock insuficiente"
    else:
        pedido["estado"], pedido["detalle"] = "CONFIRMADO", "Pedido validado"
        pedido["producto_nombre"] = producto["nombre"]
        pedido["total"] = producto["precio"] * pedido["cantidad"]


@app.get("/health")
def health():
    return {"servicio": "pedidos", "estado": "ok"}


@app.get("/pedidos")
def listar_pedidos():
    return pedidos


@app.get("/pedidos/{pedido_id}")
def obtener_pedido(pedido_id: int):
    for p in pedidos:
        if p["id"] == pedido_id:
            return p
    raise HTTPException(status_code=404, detail="Pedido no encontrado")


@app.post("/pedidos", status_code=201)
def registrar_pedido(datos: PedidoIn):
    pedido = {"id": len(pedidos) + 1, **datos.model_dump(), "estado": "PENDIENTE_VALIDACION", "detalle": ""}
    validar(pedido)
    pedidos.append(pedido)
    return pedido


@app.post("/pedidos/reintentar")
def reintentar_pendientes():
    """Revalida los pedidos que quedaron pendientes por caída de otro servicio."""
    pendientes = [p for p in pedidos if p["estado"] == "PENDIENTE_VALIDACION"]
    for p in pendientes:
        validar(p)
    return {"revisados": len(pendientes), "pedidos": pendientes}
