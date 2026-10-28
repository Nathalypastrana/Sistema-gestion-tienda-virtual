#!/usr/bin/env bash
# Levanta los 3 microservicios, cada uno en su propio proceso.
cd "$(dirname "$0")"
for par in productos:8001 clientes:8002 pedidos:8003; do
  nombre=${par%%:*}; puerto=${par##*:}
  python3 -m uvicorn main:app --app-dir "$nombre" --port "$puerto" > "$nombre.log" 2>&1 &
  echo $! > "$nombre.pid"
  echo "$nombre en http://localhost:$puerto/docs"
done
