-- Pulso · schema PostgreSQL (essencial para o Desafio 1)
--
-- Entrada: a fila cirúrgica, os eventos durante a espera e os catálogos do dataset.
-- Saída:   a fila priorizada (posição + justificativa), que é o entregável do case.
-- Hospital e médico não existem no dataset: são gerados de forma sintética pelo seed.
--
-- Uso: psql -d pulso -f db/schema.sql -f db/seed.sql

BEGIN;

DROP VIEW IF EXISTS solicitacao_ativa;
DROP TABLE IF EXISTS fila_priorizada, evento_clinico, solicitacao, paciente,
    medico, procedimento, hospital, especialidade, swalis_classe CASCADE;

-- Catálogos ------------------------------------------------------------------

CREATE TABLE especialidade (
    id   smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome text NOT NULL UNIQUE
);

CREATE TABLE hospital (
    id        smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome      text    NOT NULL UNIQUE,
    municipio text    NOT NULL,
    uf        char(2) NOT NULL DEFAULT 'RS'
);

CREATE TABLE medico (
    id               integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome             text     NOT NULL,
    crm              text     NOT NULL UNIQUE,
    especialidade_id smallint NOT NULL REFERENCES especialidade (id),
    hospital_id      smallint NOT NULL REFERENCES hospital (id)
);

CREATE TABLE procedimento (
    id                text     PRIMARY KEY CHECK (id ~ '^PROC[0-9]{3}$'),
    nome              text     NOT NULL,
    especialidade_id  smallint NOT NULL REFERENCES especialidade (id),
    porte             text     NOT NULL CHECK (porte IN ('pequeno', 'medio', 'grande', 'especial')),
    risco_cirurgico   smallint NOT NULL CHECK (risco_cirurgico BETWEEN 1 AND 5),
    duracao_media_min smallint NOT NULL CHECK (duracao_media_min > 0),
    necessita_uti     text     NOT NULL CHECK (necessita_uti IN ('sim', 'nao', 'eventual'))
);

-- Referência opcional do case (classes de urgência com prazo máximo)
CREATE TABLE swalis_classe (
    classe            text     PRIMARY KEY CHECK (classe IN ('A1', 'A2', 'B', 'C', 'D')),
    descricao         text     NOT NULL,
    prazo_maximo_dias smallint NOT NULL CHECK (prazo_maximo_dias > 0),
    exemplos          text
);

-- Fila -----------------------------------------------------------------------

CREATE TABLE paciente (
    id                    text     PRIMARY KEY CHECK (id ~ '^PAC-[0-9]{5}$'),
    nome                  text     NOT NULL,
    sexo                  char(1)  NOT NULL CHECK (sexo IN ('F', 'M')),
    idade                 smallint NOT NULL CHECK (idade BETWEEN 0 AND 120),  -- na data de referência
    municipio             text     NOT NULL,                                  -- grafia normalizada
    uf                    char(2)  NOT NULL DEFAULT 'RS',
    distancia_hospital_km smallint CHECK (distancia_hospital_km >= 0),
    comorbidades          text[]   NOT NULL DEFAULT '{}'                      -- 'nenhuma' vira {}
);

CREATE TABLE solicitacao (
    id                             text     PRIMARY KEY CHECK (id ~ '^SOL-[0-9]{4}-[0-9]{5}$'),
    paciente_id                    text     NOT NULL REFERENCES paciente (id),
    procedimento_id                text     NOT NULL REFERENCES procedimento (id),
    hospital_id                    smallint NOT NULL REFERENCES hospital (id),
    medico_solicitante_id          integer  NOT NULL REFERENCES medico (id),

    -- Diagnóstico: CID sempre normalizado (maiúsculas, sem ponto). C* = neoplasia maligna.
    cid_principal                  text     NOT NULL CHECK (cid_principal ~ '^[A-Z][0-9]{2,3}$'),
    cid_descricao                  text     NOT NULL,
    cid_secundario                 text     CHECK (cid_secundario ~ '^[A-Z][0-9]{2,3}$'),

    -- Estado clínico na inclusão (vazio = não informado)
    asa                            smallint CHECK (asa BETWEEN 1 AND 4),
    intensidade_dor_eva            smallint CHECK (intensidade_dor_eva BETWEEN 0 AND 10),
    limitacao_funcional            text     CHECK (limitacao_funcional IN ('nenhuma', 'leve', 'moderada', 'grave')),
    justificativa_clinica          text     NOT NULL,
    observacoes                    text,

    data_entrada_fila              date     NOT NULL,

    -- Prioridade manual de hoje: só serve como baseline de comparação
    prioridade_regulacao           text     CHECK (prioridade_regulacao IN ('alta', 'media', 'baixa')),
    data_ultima_revisao_prioridade date     NOT NULL,

    -- Preparo pré-operatório (opcional no case)
    hba1c_ultima                   numeric(3, 1) CHECK (hba1c_ultima BETWEEN 3 AND 20),
    data_hba1c_ultima              date,
    avaliacao_pre_anestesica       text     NOT NULL CHECK (avaliacao_pre_anestesica IN ('realizada', 'pendente', 'vencida')),
    exames_pre_op_validos          boolean  NOT NULL,

    -- Limpeza: nada é apagado, só marcado
    status                         text     NOT NULL DEFAULT 'ativa' CHECK (status IN ('ativa', 'duplicata', 'saiu')),
    duplicata_de                   text     REFERENCES solicitacao (id),
    motivo_status                  text,

    CHECK (data_ultima_revisao_prioridade >= data_entrada_fila),
    CHECK ((hba1c_ultima IS NULL) = (data_hba1c_ultima IS NULL)),
    CHECK ((status = 'duplicata') = (duplicata_de IS NOT NULL)),
    CHECK ((status = 'ativa') = (motivo_status IS NULL))
);

CREATE INDEX solicitacao_paciente_idx ON solicitacao (paciente_id);
CREATE INDEX solicitacao_status_idx ON solicitacao (status);

CREATE TABLE evento_clinico (
    id             text     PRIMARY KEY CHECK (id ~ '^EVT-[0-9]{6}$'),
    solicitacao_id text     NOT NULL REFERENCES solicitacao (id),
    data_evento    date     NOT NULL,
    tipo_evento    text     NOT NULL,
    resultado      text     NOT NULL,
    valor_numerico numeric(4, 1),  -- HbA1c em % ou dias de internação
    descricao      text     NOT NULL,
    origem         text     NOT NULL,

    CHECK (
        CASE tipo_evento
            WHEN 'biopsia'              THEN resultado IN ('positivo', 'negativo', 'inconclusivo')
            WHEN 'hba1c'                THEN resultado = 'resultado' AND valor_numerico IS NOT NULL
            WHEN 'pronto_socorro'       THEN resultado IN ('atendido_liberado', 'observacao')
            WHEN 'internacao'           THEN resultado = 'alta' AND valor_numerico IS NOT NULL
            WHEN 'exame_imagem'         THEN resultado IN ('estavel', 'progressao')
            WHEN 'consulta_reavaliacao' THEN resultado IN ('piora', 'estavel', 'melhora')
            WHEN 'contato_telefonico'   THEN resultado IN ('atendeu', 'nao_atendeu', 'relata_piora', 'relata_melhora',
                                                           'informou_cirurgia_outro_servico', 'desistiu')
            WHEN 'falta'                THEN resultado IN ('consulta', 'exame', 'avaliacao_pre_anestesica')
            ELSE false
        END
    ),
    CHECK (valor_numerico IS NULL OR tipo_evento IN ('hba1c', 'internacao'))
);

CREATE INDEX evento_solicitacao_data_idx ON evento_clinico (solicitacao_id, data_evento);

-- Saída ----------------------------------------------------------------------

-- O entregável do case: uma linha por solicitação ativa, com posição e justificativa
CREATE TABLE fila_priorizada (
    solicitacao_id text        PRIMARY KEY REFERENCES solicitacao (id),
    posicao        integer     NOT NULL UNIQUE CHECK (posicao > 0),
    justificativa  text        NOT NULL CHECK (justificativa <> ''),
    classe_swalis  text        REFERENCES swalis_classe (classe),
    gerada_em      timestamptz NOT NULL DEFAULT now()
);

-- Fila ativa com os campos derivados que a priorização usa o tempo todo.
-- 23/10/2026 é a data de referência do dataset.
CREATE VIEW solicitacao_ativa AS
SELECT s.*,
       DATE '2026-10-23' - s.data_entrada_fila AS dias_em_fila,
       s.cid_principal LIKE 'C%'               AS oncologico
FROM solicitacao s
WHERE s.status = 'ativa';

COMMIT;
