# TREND_FILE_SECURITY_DEPLOYMENT.md

# Trend Vision One – File Security (Containerized Scanner)

## Descripción

En esta demo se ha desplegado Trend Vision One File Security en modo contenerizado dentro de Kubernetes.

Esto permite analizar archivos en tiempo real sin depender de APIs externas, utilizando un scanner interno accesible por gRPC.

---

## Arquitectura desplegada

Namespace:

visionone-filesecurity

Componentes principales:

- scanner (gRPC endpoint)
- management-service
- backend-communicator
- scan-cache
- prometheus-agent

---

## Despliegue

El despliegue se ha realizado en Kubernetes utilizando el modelo contenerizado de Trend Vision One File Security.

Pasos generales realizados:

1. Crear namespace:
   kubectl create namespace visionone-filesecurity

2. Crear secrets requeridos por Trend:
   - token-secret
   - device-token-secret

3. Añadir el repositorio Helm oficial:
   helm repo add visionone-filesecurity https://trendmicro.github.io/visionone-file-security-helm/
   helm repo update

4. Instalar el scanner:
   helm install my-release visionone-filesecurity/visionone-filesecurity -n visionone-filesecurity

---

## Verificación

Comandos utilizados:

kubectl get pods -n visionone-filesecurity
kubectl get svc -n visionone-filesecurity
kubectl get secret -n visionone-filesecurity

Servicio principal utilizado por la demo:

my-release-visionone-filesecurity-scanner

Puerto:

50051 (gRPC)

---

## Integración con el backend

El backend FastAPI se conecta al scanner mediante DNS interno de Kubernetes:

my-release-visionone-filesecurity-scanner.visionone-filesecurity.svc.cluster.local:50051

---

## Variables de entorno utilizadas

En el backend se usan estas variables:

- FILE_SECURITY_API_KEY
- FILE_SECURITY_HOST

Ejemplo:

FILE_SECURITY_HOST=my-release-visionone-filesecurity-scanner.visionone-filesecurity.svc.cluster.local:50051

---

## Implementación en Python

Se utiliza el SDK de Python basado en amaas.grpc.

Flujo implementado:

1. Inicializar canal contra el scanner
2. Ejecutar scan_file
3. Cerrar canal
4. Parsear JSON devuelto

Ejemplo simplificado:

import amaas.grpc

channel = amaas.grpc.init(
    host="my-release-visionone-filesecurity-scanner.visionone-filesecurity.svc.cluster.local:50051",
    api_key="YOUR_API_KEY",
    enable_tls=False
)

result = amaas.grpc.scan_file(channel, file_path)
amaas.grpc.quit(channel)

---

## Flujo funcional de la demo

1. Usuario sube un archivo desde el frontend
2. El backend lo guarda en:
   /data/uploads/incoming
3. El backend envía el archivo al scanner
4. Trend File Security devuelve un JSON con:
   - scanId
   - malwareCount
   - fileTypeName
   - fileSHA1
   - fileSHA256
   - scannerVersion
5. El backend clasifica:
   - clean -> /data/uploads/clean
   - malicious -> /data/uploads/quarantine

---

## Resultado mostrado en UI

La UI muestra:

- Nombre de archivo
- Veredicto
- Destino final
- Tipo de fichero
- Malware detectado
- Scan ID
- Versión del scanner
- SHA256
- Tiempo de análisis
- Origen del escaneo

---

## Beneficios del enfoque contenerizado

- El análisis se ejecuta dentro del cluster
- Baja latencia
- Mayor control del tráfico
- Arquitectura más adecuada para entornos regulados
- Escalabilidad y separación de componentes
