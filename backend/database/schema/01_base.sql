-- 01_base.sql (Dev B): usuários, guichês e log de acesso. Aplicado por `python -m database.seed`
-- (ou database.migrar), que registra cada arquivo em `schema_migracoes` e nunca o repete.

CREATE TABLE usuarios (
  id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nome        VARCHAR(100) NOT NULL,
  email       VARCHAR(150) NOT NULL,
  senha_hash  VARCHAR(255) NOT NULL,
  perfil      ENUM('ATENDENTE','GESTOR') NOT NULL,
  ativo       TINYINT(1) NOT NULL DEFAULT 1,
  criado_em   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  -- RN-13: no máximo um GESTOR ativo. A coluna vale 1 só para gestor ativo (senão NULL, que o
  -- UNIQUE aceita repetido); assim o próprio banco impede o segundo gestor, mesmo numa corrida.
  gestor_ativo TINYINT GENERATED ALWAYS AS (CASE WHEN perfil = 'GESTOR' AND ativo = 1 THEN 1 ELSE NULL END) STORED,
  UNIQUE KEY uq_usuarios_email (email),
  UNIQUE KEY uq_gestor_unico (gestor_ativo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE guiches (
  id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  numero      SMALLINT UNSIGNED NOT NULL,
  ativo       TINYINT(1) NOT NULL DEFAULT 1,
  usuario_id  INT UNSIGNED NULL,                -- atendente que ocupa agora
  UNIQUE KEY uq_guiches_numero (numero),
  UNIQUE KEY uq_guiches_usuario (usuario_id),   -- um atendente, um guichê (RN-11)
  CONSTRAINT fk_guiches_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE log_acesso (
  id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  usuario_id  INT UNSIGNED NULL,
  acao        VARCHAR(60) NOT NULL,
  recurso     VARCHAR(150) NULL,
  ip          VARCHAR(45) NULL,
  resultado   ENUM('SUCESSO','NEGADO','FALHA') NOT NULL,
  ocorrido_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY ix_log_usuario_data (usuario_id, ocorrido_em),
  CONSTRAINT fk_log_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
