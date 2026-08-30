# Edições

Uma pasta por edição, no formato `AAAA-MM/`:

| Arquivo | O que é |
|---|---|
| `edicao.json` | Fonte da verdade. Tudo é gerado a partir daqui. |
| `pauta.md` | Candidatos avaliados e suas notas na régua. Registro de auditoria. |
| `edicao.html` | E-mail renderizado, usado no rascunho do Gmail. Gerado. |
| `edicao.md` | Versão de arquivo, legível em diff. Gerada. |

`edicao.html` e `edicao.md` são gerados — edite sempre o JSON e rode `render` de novo.

**`2026-08/` é uma edição-referência**, montada apenas com fatos públicos verificados para
servir de gabarito de formato. Ela não foi enviada. As seções ausentes são ausentes de
propósito: não havia material verificado que passasse na régua, e é assim que a regra do
silêncio se parece na prática — inclusive nos `cortes`, que explicam por que Bizmetric e
Vexta ficaram de fora.
