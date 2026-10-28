# Tienda virtual – Microservicios (FastAPI)

| Servicio  | Puerto | Endpoints |
|-----------|--------|-----------|
| Productos | 8001   | GET /productos, GET /productos/{id}, POST /productos |
| Clientes  | 8002   | GET /clientes, GET /clientes/{id}, POST /clientes |
| Pedidos   | 8003   | GET /pedidos, GET /pedidos/{id}, POST /pedidos, POST /pedidos/reintentar |

Todos tienen `GET /health` y documentación Swagger en `/docs`. Datos en listas en memoria.

## Ejecutar
```bash
pip install -r requirements.txt
./iniciar.sh      # levanta los 3 servicios
./probar.sh       # pruebas + simulación de caída de Productos
```
Para apagar uno a mano: `kill $(cat productos.pid)`.

## Tolerancia a fallos
Pedidos llama a Productos y Clientes por HTTP con timeout de 2 s y 2 reintentos.
Si alguno no responde, el pedido queda `PENDIENTE_VALIDACION` (no se pierde) y se
revalida con `POST /pedidos/reintentar`. Consultar pedidos, clientes y productos
nunca depende de otro servicio.
