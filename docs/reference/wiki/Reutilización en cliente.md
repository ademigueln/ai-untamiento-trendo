> Referencia histórica importada. Para operar la demo, consulta [el recorrido vigente](../../overview/OPERACION_DEMO.md).

# Reutilización en cliente

## Objetivo de esta página

Esta página resume cómo reutilizar el patrón de la demo en proyectos reales de cliente.

No se trata de clonar literalmente la demo, sino de identificar qué piezas son trasladables casi sin cambios y cuáles deben adaptarse al contexto del cliente.

---

## Qué se puede reutilizar directamente

## 1. Patrón de protección conversacional con AI Guard

La secuencia:

1. validar input
2. llamar al modelo
3. validar output

es reutilizable casi de forma literal.

Ventajas:
- desacopla seguridad del modelo
- no obliga a modificar el proveedor LLM
- funciona con diferentes prompts y asistentes

Aplicable a:
- chatbots corporativos
- copilotos internos
- asistentes de atención al cliente
- interfaces de búsqueda conversacional

---

## 2. Patrón documental con zona de staging

La lógica:

- incoming
- clean
- quarantine

también es muy reutilizable.

Ventajas:
- evita aceptar automáticamente el documento
- define una fase técnica de admisión
- permite auditoría clara del flujo

Aplicable a:
- portales de atención ciudadana
- onboarding documental
- portales de proveedores
- tramitación interna
- sistemas de expedientes

---

## 3. Patrón de bootstrap reproducible

La separación entre:

- plantilla de secrets
- secrets locales renderizados
- script de despliegue completo

también es reutilizable.

Ventajas:
- acelera PoCs
- reduce errores de despliegue
- permite arrancar entornos de laboratorio de forma homogénea

---

## Qué suele cambiar en cliente

## 1. Identidad visual y frontend
Normalmente cambiarán:
- branding
- textos
- navegación
- módulos visibles
- indicadores del dashboard

Esto no afecta a la lógica de seguridad.

## 2. Proveedor LLM
La demo usa OpenAI, pero el patrón soporta otros proveedores.

Se puede adaptar a:
- Azure OpenAI
- modelos on-prem
- otros proveedores cloud
- gateways corporativos

AI Guard sigue siendo válido como patrón siempre que el backend mantenga la secuencia de validación.

## 3. Almacenamiento documental
En la demo se usa almacenamiento local montado en volumen.

En cliente es habitual pasar a:
- S3
- NFS
- almacenamiento corporativo
- repositorios documentales internos

El patrón no cambia: solo cambia el backend de almacenamiento.

## 4. Auditoría y logging
En cliente suele ser necesario:
- auditoría persistente
- trazabilidad de eventos
- integración con SIEM
- métricas operativas

La demo ya tiene una base, pero normalmente esto se ampliaría.

## 5. Modelo de despliegue
La demo usa Kubernetes local.

En cliente puede cambiar a:
- Kubernetes corporativo
- OpenShift
- AKS / EKS / GKE
- entorno híbrido
- on-prem regulado

El patrón Helm + namespaces + secrets se mantiene, aunque con naming y prácticas distintas.

---

## Cómo pensar la adopción en cliente

## Caso 1. Cliente con chatbot ya existente
No hace falta reescribir el chatbot.

Se puede introducir AI Guard en el backend actual, encapsulando el patrón:

- guard input
- model call
- guard output

Este es probablemente el caso de adopción más sencillo.

## Caso 2. Cliente con portal documental
Se puede introducir File Security como capa de admisión documental.

No hace falta rehacer toda la lógica de negocio:
- basta con insertar un paso de scan antes de aceptar el documento

## Caso 3. Cliente con plataforma nueva
Aquí sí se puede reutilizar la demo como blueprint casi completo:
- backend pattern
- frontend reference
- namespaces
- Helm
- scripts de bootstrap

---

## Qué conviene aislar como componentes reutilizables

A medio plazo, si se quisiera convertir esta demo en acelerador interno, tendría sentido separar:

### AI Guard module
Un pequeño módulo reusable con:
- `inspect_prompt`
- `inspect_output`
- `call_trend_ai_guard`

### File Security module
Un módulo reusable con:
- `scan_file`
- parseo de respuesta
- clasificación incoming/clean/quarantine

### Deployment pack
Un pack reusable con:
- plantilla de secrets
- script de bootstrap
- script de troubleshooting
- manifests base

---

## Riesgos de reutilización a tener en cuenta

## 1. Asumir que el scanner siempre está listo
En entorno de cliente puede haber onboarding, redes o policies que lo compliquen.

## 2. Asumir que el modelo responde siempre
La demo mostró claramente que una API key inválida puede romper solo parte del flujo.

## 3. Confundir error visible con causa raíz
En cliente es clave separar:
- error frontend
- error backend
- error AI Guard
- error LLM
- error scanner

## 4. No definir bien el tratamiento documental
No basta con escanear. Hay que decidir:
- qué hacer con clean
- qué hacer con malicious
- qué hacer con error
- cómo notificar al usuario

---

## Recomendaciones para un proyecto real

## Recomendación 1
Mantener AI Guard como capa explícita del backend, no incrustada de forma difusa por el código.

## Recomendación 2
Mantener una zona de staging documental y no aceptar ficheros en negocio sin inspección previa.

## Recomendación 3
Separar claramente secrets, despliegue y lógica de negocio.

## Recomendación 4
Añadir observabilidad desde el principio:
- eventos
- métricas
- errores clasificados
- trazas de onboarding

## Recomendación 5
Preparar scripts de validación funcional post-despliegue.
No basta con que los pods estén running.

---

## Mensaje clave para cliente

Lo más valioso de esta demo no es el UI ni el caso municipal.

Lo valioso es el patrón:

- proteger la entrada conversacional
- proteger la salida conversacional
- proteger la entrada documental
- proteger el pipeline de entrega

Ese patrón es el que se puede trasladar a múltiples sectores:

- administración pública
- banca
- seguros
- industria
- utilities
- sanidad
- retail

---

## Conclusión

Esta demo debe entenderse como un blueprint de referencia, no como un producto cerrado.

Lo que se reutiliza no es tanto la estética ni el caso de uso concreto, sino la estructura técnica:

- backend como orquestador
- AI Guard antes y después del LLM
- File Security como control de admisión documental
- despliegue automatizado
- troubleshooting por síntomas

Ese enfoque sí es directamente aprovechable en proyectos reales.