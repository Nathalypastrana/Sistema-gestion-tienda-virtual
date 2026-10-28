#!/usr/bin/env bash
# Pruebas de las API y de tolerancia a fallos.
cd "$(dirname "$0")"
J='-H Content-Type:application/json'
t() { echo; echo "### $1"; }

t "1. Todo funcionando: crear producto, cliente y pedido"
curl -s -X POST localhost:8001/productos $J -d '{"nombre":"Gorra","precio":25000,"stock":10}'; echo
curl -s -X POST localhost:8002/clientes $J -d '{"nombre":"Marta Ruiz","email":"marta@correo.com"}'; echo
curl -s -X POST localhost:8003/pedidos $J -d '{"cliente_id":1,"producto_id":1,"cantidad":2}'; echo

t "2. Validaciones: stock insuficiente y cliente inexistente"
curl -s -X POST localhost:8003/pedidos $J -d '{"cliente_id":1,"producto_id":1,"cantidad":999}'; echo
curl -s -X POST localhost:8003/pedidos $J -d '{"cliente_id":99,"producto_id":1,"cantidad":1}'; echo

t "3. CAÍDA: se apaga el servicio de PRODUCTOS"
kill "$(cat productos.pid)"; sleep 1
echo "productos:"; curl -s -m 3 localhost:8001/health || echo " -> sin conexión (esperado)"
echo "clientes (debe seguir):"; curl -s localhost:8002/clientes; echo
echo "pedidos - consultar (debe seguir):"; curl -s localhost:8003/pedidos; echo
echo "pedidos - crear con productos caído (queda pendiente, no se pierde):"
curl -s -X POST localhost:8003/pedidos $J -d '{"cliente_id":2,"producto_id":1,"cantidad":1}'; echo

t "4. RECUPERACIÓN: se vuelve a levantar PRODUCTOS y se reintentan pendientes"
python3 -m uvicorn main:app --app-dir productos --port 8001 > productos.log 2>&1 &
echo $! > productos.pid
sleep 3
echo "productos de nuevo:"; curl -s localhost:8001/health; echo
curl -s -X POST localhost:8003/pedidos/reintentar; echo
