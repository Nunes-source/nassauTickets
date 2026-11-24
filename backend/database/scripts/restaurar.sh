#!/usr/bin/env bash
# Restaura um backup (.sql.gz) no MySQL do Docker Compose. ATENÇÃO: sobrescreve os dados atuais.
# Uso: backend/database/scripts/restaurar.sh caminho/do/backup.sql.gz
set -euo pipefail

[ $# -eq 1 ] && [ -f "$1" ] || { echo "Uso: $0 arquivo.sql.gz" >&2; exit 1; }
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$RAIZ"

gunzip -c "$1" | docker compose exec -T db sh -c \
  'MYSQL_PWD="$MYSQL_PASSWORD" mysql -u"$MYSQL_USER" "$MYSQL_DATABASE"'
echo "Restauração concluída a partir de: $1"
