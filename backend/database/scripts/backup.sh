#!/usr/bin/env bash
# Backup do MySQL do Docker Compose: um .sql.gz por execução, com retenção em dias.
# Uso (a partir de qualquer pasta):  backend/database/scripts/backup.sh
# Agendar (cron, 02:00 todo dia):    0 2 * * * /caminho/do/repo/backend/database/scripts/backup.sh
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
DESTINO="${BACKUP_DIR:-$RAIZ/backups}"
RETENCAO_DIAS="${BACKUP_RETENCAO_DIAS:-7}"
ARQUIVO="$DESTINO/nassau_tickets_$(date +%Y%m%d_%H%M%S).sql.gz"

mkdir -p "$DESTINO"
cd "$RAIZ"

# As credenciais vêm das variáveis MYSQL_* do próprio contêiner (nada de senha na linha de comando).
docker compose exec -T db sh -c \
  'MYSQL_PWD="$MYSQL_PASSWORD" mysqldump --single-transaction --routines -u"$MYSQL_USER" "$MYSQL_DATABASE"' \
  | gzip > "$ARQUIVO"

# Garante que o arquivo não está vazio antes de apagar backups antigos.
[ -s "$ARQUIVO" ] || { echo "Backup vazio: $ARQUIVO" >&2; rm -f "$ARQUIVO"; exit 1; }

find "$DESTINO" -name 'nassau_tickets_*.sql.gz' -mtime +"$RETENCAO_DIAS" -delete
echo "Backup criado: $ARQUIVO"
