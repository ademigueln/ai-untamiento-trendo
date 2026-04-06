#!/bin/bash

set -euo pipefail

ENV_FILE=".env.demo.local"
DEPLOY_SCRIPT="./scripts/desplegar_demo_full.sh"

TOKENS=(
  "OPENAI_API_KEY"
  "TREND_API_KEY"
  "FILE_SECURITY_API_KEY"
  "FILE_SECURITY_REGISTRATION_TOKEN"
)

detect_os() {
  case "$(uname -s)" in
    Darwin) OS_TYPE="mac" ;;
    Linux) OS_TYPE="linux" ;;
    *) OS_TYPE="unknown" ;;
  esac
}

print_header() {
  echo "=============================================="
  echo "  Actualización de tokens + despliegue demo"
  echo "=============================================="
  echo
}

require_env_file() {
  if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: no existe $ENV_FILE"
    exit 1
  fi
}

show_tokens() {
  echo "Variables críticas disponibles:"
  for i in "${!TOKENS[@]}"; do
    echo "  $((i+1))) ${TOKENS[$i]}"
  done
  echo
}

update_env_var() {
  local var_name="$1"
  local new_value="$2"

  awk -v key="$var_name" -v val="$new_value" '
    BEGIN { replaced=0 }
    $0 ~ "^" key "=" {
      print key "=\"" val "\""
      replaced=1
      next
    }
    { print }
    END {
      if (replaced == 0) {
        print key "=\"" val "\""
      }
    }
  ' "$ENV_FILE" > "${ENV_FILE}.tmp" && mv "${ENV_FILE}.tmp" "$ENV_FILE"
}

read_token_value() {
  local var_name="$1"
  local new_value=""
  local mode=""

  echo "¿Cómo quieres introducir el valor para $var_name?"
  echo "  1) Pegar manualmente en terminal"
  if [ "$OS_TYPE" = "mac" ]; then
    echo "  2) Leer desde portapapeles (pbpaste)"
  fi
  echo -n "Selecciona opción: "
  read -r mode

  if [ "$mode" = "2" ] && [ "$OS_TYPE" = "mac" ]; then
    new_value="$(pbpaste)"
    if [ -z "${new_value:-}" ]; then
      echo "ERROR: el portapapeles está vacío"
      exit 1
    fi
  else
    echo "Pega el valor para $var_name y pulsa Enter:"
    read -rs new_value
    echo
    if [ -z "${new_value:-}" ]; then
      echo "ERROR: valor vacío para $var_name"
      exit 1
    fi
  fi

  TOKEN_VALUE_RESULT="$new_value"
}

prompt_for_tokens() {
  show_tokens
  echo "Selecciona uno o varios números separados por espacios."
  echo "Ejemplo: 1 4"
  echo "Pulsa Enter sin escribir nada si no quieres cambiar ninguno."
  read -r selection
  echo

  if [ -z "${selection:-}" ]; then
    echo "No se han modificado tokens."
    echo
    return
  fi

  for idx in $selection; do
    if ! [[ "$idx" =~ ^[0-9]+$ ]]; then
      echo "Selección inválida: $idx"
      exit 1
    fi

    if [ "$idx" -lt 1 ] || [ "$idx" -gt "${#TOKENS[@]}" ]; then
      echo "Selección fuera de rango: $idx"
      exit 1
    fi

    local var_name="${TOKENS[$((idx-1))]}"
    read_token_value "$var_name"
    update_env_var "$var_name" "$TOKEN_VALUE_RESULT"

    echo "Actualizado: $var_name"
    echo
  done
}

validate_env_vars() {
  echo "Validando variables críticas en $ENV_FILE ..."
  for var in "${TOKENS[@]}"; do
    if ! grep -q "^${var}=" "$ENV_FILE"; then
      echo "ERROR: falta $var en $ENV_FILE"
      exit 1
    fi
  done
  echo "OK: todas las variables críticas existen"
  echo
}

suggest_broken_token_from_logs() {
  echo
  echo "Intentando detectar causa probable en logs..."
  echo

  if kubectl get pods -n trendo-demo >/dev/null 2>&1; then
    local backend_pod=""
    backend_pod="$(kubectl get pods -n trendo-demo -l app=backend -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)"
    if [ -n "${backend_pod:-}" ]; then
      local backend_logs=""
      backend_logs="$(kubectl logs -n trendo-demo "$backend_pod" --tail=200 2>/dev/null || true)"

      if echo "$backend_logs" | grep -qi "invalid_api_key"; then
        echo "Posible causa detectada: OPENAI_API_KEY inválida o caducada."
      fi

      if echo "$backend_logs" | grep -qi "authenticationerror"; then
        echo "Posible causa detectada: problema de autenticación contra OpenAI."
      fi
    fi
  fi

  if kubectl get pods -n visionone-filesecurity >/dev/null 2>&1; then
    local bc_pod=""
    bc_pod="$(kubectl get pods -n visionone-filesecurity -l app.kubernetes.io/component=backend-communicator -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)"
    if [ -n "${bc_pod:-}" ]; then
      local bc_logs=""
      bc_logs="$(kubectl logs -n visionone-filesecurity "$bc_pod" -c init-token --tail=200 2>/dev/null || true)"

      if echo "$bc_logs" | grep -qi "token expired"; then
        echo "Posible causa detectada: FILE_SECURITY_REGISTRATION_TOKEN expirado."
      fi

      if echo "$bc_logs" | grep -qi "Invalid token"; then
        echo "Posible causa detectada: FILE_SECURITY_REGISTRATION_TOKEN inválido."
      fi
    fi
  fi

  echo
  echo "Puedes volver a ejecutar este script y actualizar el token problemático."
}

run_deploy() {
  echo "Lanzando despliegue completo..."
  echo

  if ! "$DEPLOY_SCRIPT"; then
    echo
    echo "El despliegue ha fallado."
    suggest_broken_token_from_logs
    exit 1
  fi
}

main() {
  detect_os
  print_header
  require_env_file
  prompt_for_tokens
  validate_env_vars
  run_deploy

  echo
  echo "Despliegue completado correctamente."
}

main "$@"
