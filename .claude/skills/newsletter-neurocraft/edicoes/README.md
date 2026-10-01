# Edições

Uma pasta por edição, no formato `AAAA-MM/`:

| Arquivo | O que é |
|---|---|
| `edicao.json` | Fonte da verdade. Tudo é gerado a partir daqui. |
| `pauta.md` | Candidatos avaliados, notas na régua e decisões de corte. Registro de auditoria. |
| `edicao.html` | E-mail renderizado, usado no rascunho do Gmail. Gerado. |
| `edicao.md` | Versão de arquivo, legível em diff. Gerada. |

`edicao.html` e `edicao.md` são gerados — edite sempre o JSON e rode `render` de novo.

## `radar.csv` — memória entre edições

Registro append-only de tudo que já passou pelo agente: url, título, fonte, marca, status
(`publicado` ou `cortado`), edição, data e motivo do corte.

Existe para uma coisa só: **impedir que o mesmo item seja reavaliado do zero todo mês.** Item
cortado em agosto por ser notícia velha continua velho em setembro, e reavaliá-lo é desperdício
que o leitor acaba percebendo na forma de conteúdo repetido.

```bash
edicao.py radar check <url>...      # antes de apurar: já vimos isso?
edicao.py radar sync edicoes/AAAA-MM # depois de publicar: registra a edição inteira
edicao.py radar list --desde 2026-08-01
```

O radar é **derivado** do `edicao.json` — nunca editado à mão. `sync` é idempotente. A
deduplicação normaliza a URL: ignora `www.`, subdomínio de idioma do LinkedIn, parâmetros de
rastreamento e barra final.

Corte sem `url` não entra no radar e volta a ser avaliado no mês seguinte. O validador avisa.

## Histórico

| Edição | Assunto | Situação |
|---|---|---|
| `2026-08` | Agosto votou: agente com humano no comando | Rascunho no Gmail, aguardando revisão. **Referência canônica de estilo** — leia antes de escrever a próxima. |
