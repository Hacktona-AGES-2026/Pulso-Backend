# Banco de dados (PostgreSQL)

Schema essencial para o Desafio 1: a fila cirúrgica e os eventos do dataset como entrada, a fila priorizada como saída. Testado no PostgreSQL 16.

## Como carregar

```bash
createdb pulso
psql -d pulso -f db/schema.sql -f db/seed.sql
```

O `schema.sql` apaga e recria as tabelas, então dá para rodar de novo quando quiser.

Para regerar o `seed.sql` depois de mudar os CSVs ou as regras de limpeza (só usa a biblioteca padrão do Python):

```bash
python db/gerar_seed.py
```

## Tabelas

| Tabela | Linhas | De onde vem |
| --- | --- | --- |
| `especialidade` | 14 | `procedimentos.csv` |
| `hospital` | 3 | **sintético**: Hospital Sao Lucas + 2 regionais |
| `medico` | 28 | **sintético**: 2 por especialidade |
| `procedimento` | 23 | `procedimentos.csv` |
| `swalis_classe` | 5 | `referencias/swalis.csv` |
| `paciente` | 907 | `fila_cirurgica.csv` (dados do paciente) |
| `solicitacao` | 941 | `fila_cirurgica.csv` (uma linha por pedido de cirurgia) |
| `evento_clinico` | 1.490 | `eventos_clinicos.csv` |
| `fila_priorizada` | 897 | uma linha por solicitação ativa: posição antes e depois do Pulso + justificativa |

A view `solicitacao_ativa` traz só as solicitações ativas (897), com `dias_em_fila` e `oncologico` (CID começando com C) já calculados a partir da data de referência, 23/10/2026.

### `fila_priorizada`

| Coluna | O que é | Quem preenche |
| --- | --- | --- |
| `posicao_inicial` | posição pelo método atual: prioridade manual (alta, media, baixa, vazia) e, dentro dela, data de entrada | o seed |
| `posicao_final` | posição depois do Pulso | o motor |
| `justificativa` | motivo da posição final | o motor, junto com a `posicao_final` |

O entregável do case sai direto daqui:

```sql
SELECT solicitacao_id, posicao_final AS posicao, justificativa
FROM fila_priorizada ORDER BY posicao_final;
```

`posicao_inicial - posicao_final` é quantas posições o paciente subiu com o Pulso.

## Decisões de limpeza

- **Nada é apagado.** Toda solicitação entra, com `status`:
  - `ativa`: 897
  - `duplicata`: 22. É o mesmo paciente e procedimento de outra solicitação; fica ativa a mais antiga, que tem os eventos e o tempo de espera real, e a coluna `duplicata_de` aponta para ela.
  - `saiu`: 22. É desistência ou cirurgia em outro serviço, por contato telefônico ou observação; o motivo fica em `motivo_status`.
- **"Não deseja mais operar no momento"** sem contato registrado continua `ativa`. São 2 casos, entre eles uma colecistite aguda (`SOL-2024-00061`): a desistência precisa ser confirmada antes de sair da fila.
- **Normalizações:**
  - CID sem ponto e em maiúsculas (`K40.9` → `K409`);
  - prioridade em minúsculas e sem acento;
  - município com a grafia mais comum (62 grafias → 38 municípios);
  - comorbidades viram uma lista (`{HAS,DM2}`), e "nenhuma" vira lista vazia.
- **Fora da carga:** as flags manuais (`flag_oncologico`, `flag_diabetico`, `flag_piora_clinica`) e o `dias_em_fila`. As flags erram com frequência e são recalculadas a partir do CID e dos eventos; o `dias_em_fila` é calculado na view.
- **Eventos descartados:** 9 órfãos (de solicitações que não existem na fila) e 6 duplicados exatos. Os IDs estão listados no topo do `seed.sql`.
- **Médico solicitante:** sorteado com semente fixa entre os médicos da especialidade do procedimento, porque o dataset não informa quem pediu a cirurgia.

O dataset fica em `ideas/data/dataset/`.
