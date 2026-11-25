-- CÓPIA DE TESTE do schema da fila (docs/mer/modelo-dados.md §4), usada só quando o
-- database/schema/02_fila.sql do Dev A ainda não existe. Não é migration do sistema.

CREATE TABLE contadores_senha (
  data        DATE NOT NULL,
  tipo        ENUM('SP','SG','SE') NOT NULL,
  ultimo_seq  INT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (data, tipo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE fila_estado (                      -- uma linha por dia; é o "cadeado" da chamada
  data         DATE NOT NULL PRIMARY KEY,
  ultimo_tipo  ENUM('SP','SG','SE') NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE senhas (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  numero          CHAR(12) NOT NULL,            -- YYMMDD-PPSQ
  data_emissao    DATE NOT NULL,
  tipo            ENUM('SP','SG','SE') NOT NULL,
  sequencia       SMALLINT UNSIGNED NOT NULL,
  estado          ENUM('EMITIDA','AGUARDANDO','CHAMADA','CHAMADA_NOVAMENTE',
                       'EM_ATENDIMENTO','ATENDIDA','NAO_COMPARECEU') NOT NULL,
  motivo_descarte ENUM('ABANDONO','FIM_EXPEDIENTE') NULL,
  emitida_em      DATETIME NOT NULL,
  UNIQUE KEY uq_senhas_numero (numero),
  UNIQUE KEY uq_senhas_dia_tipo_seq (data_emissao, tipo, sequencia),
  KEY ix_senhas_fila (data_emissao, estado, tipo, sequencia),
  CONSTRAINT ck_senhas_seq CHECK (sequencia BETWEEN 1 AND 999),
  CONSTRAINT ck_senhas_motivo CHECK (
    (estado = 'NAO_COMPARECEU' AND motivo_descarte IS NOT NULL) OR
    (estado <> 'NAO_COMPARECEU' AND motivo_descarte IS NULL))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE senha_historico (
  id               BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  senha_id         BIGINT UNSIGNED NOT NULL,
  estado_anterior  ENUM('EMITIDA','AGUARDANDO','CHAMADA','CHAMADA_NOVAMENTE',
                        'EM_ATENDIMENTO','ATENDIDA','NAO_COMPARECEU') NULL,
  estado_novo      ENUM('EMITIDA','AGUARDANDO','CHAMADA','CHAMADA_NOVAMENTE',
                        'EM_ATENDIMENTO','ATENDIDA','NAO_COMPARECEU') NOT NULL,
  usuario_id       INT UNSIGNED NULL,
  origem           ENUM('TOTEM','ATENDENTE','SISTEMA') NOT NULL,
  ocorrido_em      DATETIME NOT NULL,
  KEY ix_hist_senha (senha_id, ocorrido_em),
  CONSTRAINT fk_hist_senha   FOREIGN KEY (senha_id)   REFERENCES senhas(id),
  CONSTRAINT fk_hist_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE chamadas (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  senha_id        BIGINT UNSIGNED NOT NULL,
  guiche_id       INT UNSIGNED NOT NULL,
  usuario_id      INT UNSIGNED NOT NULL,
  numero_chamada  TINYINT UNSIGNED NOT NULL,    -- 1 ou 2
  chamada_em      DATETIME NOT NULL,
  UNIQUE KEY uq_chamada_senha_num (senha_id, numero_chamada),
  KEY ix_chamadas_recentes (chamada_em),
  CONSTRAINT ck_chamada_num CHECK (numero_chamada IN (1,2)),
  CONSTRAINT fk_chamada_senha   FOREIGN KEY (senha_id)   REFERENCES senhas(id),
  CONSTRAINT fk_chamada_guiche  FOREIGN KEY (guiche_id)  REFERENCES guiches(id),
  CONSTRAINT fk_chamada_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE atendimentos (
  id                   BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  senha_id             BIGINT UNSIGNED NOT NULL,
  guiche_id            INT UNSIGNED NOT NULL,
  usuario_id           INT UNSIGNED NOT NULL,
  iniciado_em          DATETIME NOT NULL,
  finalizado_em        DATETIME NULL,
  duracao_simulada_seg INT UNSIGNED NOT NULL,   -- TM sorteado (RN-07)
  UNIQUE KEY uq_atend_senha (senha_id),
  CONSTRAINT ck_atend_fim CHECK (finalizado_em IS NULL OR finalizado_em >= iniciado_em),
  CONSTRAINT fk_atend_senha   FOREIGN KEY (senha_id)   REFERENCES senhas(id),
  CONSTRAINT fk_atend_guiche  FOREIGN KEY (guiche_id)  REFERENCES guiches(id),
  CONSTRAINT fk_atend_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
