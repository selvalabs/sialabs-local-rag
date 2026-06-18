# API

A documentação interativa fica disponível em `http://localhost:8000/docs`.

## Endpoints

### `GET /health`

Verifica disponibilidade da API.

### `GET /api/config`

Retorna configuração pública segura:

- provider de LLM;
- modelo de LLM;
- provider de embeddings;
- modelo de embeddings;
- top K;
- tamanho e overlap de chunks.

Não retorna variáveis sensíveis.

### `POST /api/documents`

Cria documento por texto colado.

```json
{
  "title": "Documento de demonstração",
  "content": "Texto com conteúdo suficiente para indexação.",
  "source_type": "manual"
}
```

### `POST /api/documents/upload`

Recebe arquivo `.txt`, `.md` ou `.markdown` UTF-8. Limite do MVP: 1 MB.

### `GET /api/documents`

Lista documentos indexados.

### `DELETE /api/documents/{document_id}`

Remove documento e chunks associados.

### `POST /api/chat`

Consulta a base local.

```json
{
  "question": "Quais tecnologias o projeto demonstra?",
  "top_k": 5
}
```

Retorna:

- resposta;
- fontes recuperadas;
- score de similaridade;
- provider/modelo usado;
- latência em milissegundos.

## Erros esperados

| Status | Caso |
| --- | --- |
| 409 | documento duplicado |
| 413 | upload maior que o limite |
| 415 | extensão não suportada |
| 422 | payload inválido ou arquivo não UTF-8 |
| 503 | Ollama indisponível ou erro de provider |

<!-- PDF_INGESTION_SECTION_START -->
## PDF ingestion

`POST /api/documents/upload` accepts:

- `.txt`
- `.md`
- `.markdown`
- `.pdf`

For PDFs, the backend extracts selectable text and indexes the extracted content using the existing RAG pipeline.

Limitations:

- scanned PDFs are not OCR-processed;
- images are not extracted;
- tables are not reconstructed;
- password-protected or damaged PDFs return a validation error.
<!-- PDF_INGESTION_SECTION_END -->
