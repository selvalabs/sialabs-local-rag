# Local AI

## Objetivo

Demonstrar um fluxo de IA aplicada sem depender de APIs externas. O projeto pode rodar em modo mock/hash para validação e em modo Ollama para IA local real.

## Modo demo

```env
LLM_PROVIDER=mock
EMBEDDING_PROVIDER=hash
```

Vantagens:

- CI determinístico;
- demo rápida;
- não exige GPU;
- recrutador consegue avaliar arquitetura sem baixar modelos.

Limitação: embeddings por hash não são semanticamente equivalentes a modelos reais.

## Modo Ollama

```env
LLM_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=gemma4:e2b
OLLAMA_EMBED_MODEL=embeddinggemma
```

Comandos sugeridos:

```powershell
ollama pull gemma4:e2b
ollama pull embeddinggemma
```

## Boas práticas

- Não exponha a porta do Ollama publicamente.
- Use o modo mock/hash para CI.
- Mantenha modelos configuráveis por `.env`.
- Documente limites de hardware ao gravar demo.
- Mostre fontes recuperadas para reduzir aparência de “caixa-preta”.

## Por que isso é relevante para recrutamento

O projeto demonstra que IA aplicada não é apenas chamada de API. A implementação cobre:

- provider abstraction;
- tratamento de erro de runtime local;
- separação entre embedding e geração;
- fallback para CI;
- prompt contextualizado;
- resposta com fontes;
- persistência e recuperação.

