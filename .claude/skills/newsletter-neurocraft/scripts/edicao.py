#!/usr/bin/env python3
"""Ferramenta da newsletter mensal da Neurocraft.

Subcomandos:
  nova [AAAA-MM]        cria a pasta da edicao com esqueleto de pauta e janela de apuracao
  validar <pasta>       aplica as regras editoriais mecanicas sobre edicao.json
  render <pasta>        gera edicao.html (email) e edicao.md (arquivo) a partir de edicao.json

Sem dependencias externas: roda com Python 3.8+ puro.
"""

import argparse
import calendar
import csv
import html
import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

RAIZ = Path(__file__).resolve().parent.parent
CONFIG = RAIZ / "config" / "marcas.json"
TEMPLATE = RAIZ / "assets" / "template-email.html"
EDICOES = RAIZ / "edicoes"
RADAR = EDICOES / "radar.csv"
COLUNAS_RADAR = ["registrado_em", "url", "titulo", "fonte", "marca",
                 "status", "edicao", "data_item", "motivo"]

TIPOS = {"movimentos", "marca", "deepdive", "radar", "numeros", "agenda"}
TIPOS_COM_ITENS_FONTEADOS = {"movimentos", "marca", "radar"}
MESES = ["janeiro", "fevereiro", "marco", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]
MESES_EXIBICAO = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
                  "agosto", "setembro", "outubro", "novembro", "dezembro"]
LIMITE_ASSUNTO = 60
PALAVRAS_MIN, PALAVRAS_MAX = 900, 1400
LIMITE_HTML_BYTES = 100 * 1024


# ---------------------------------------------------------------- utilidades

def carregar_config():
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def mes_anterior(hoje=None):
    hoje = hoje or date.today()
    ano, mes = (hoje.year - 1, 12) if hoje.month == 1 else (hoje.year, hoje.month - 1)
    return "%04d-%02d" % (ano, mes)


def janela(rotulo):
    ano, mes = (int(p) for p in rotulo.split("-"))
    return date(ano, mes, 1), date(ano, mes, calendar.monthrange(ano, mes)[1])


def rotulo_por_extenso(rotulo):
    ano, mes = (int(p) for p in rotulo.split("-"))
    return "%s de %d" % (MESES_EXIBICAO[mes - 1], ano)


def ler_edicao(pasta):
    caminho = Path(pasta) / "edicao.json"
    if not caminho.exists():
        sys.exit("erro: %s nao encontrado" % caminho)
    return json.loads(caminho.read_text(encoding="utf-8")), caminho


def contar_palavras(dados):
    partes = [dados.get("editorial", "")]
    for secao in dados.get("secoes", []):
        partes.append(secao.get("titulo", ""))
        partes.extend(secao.get("corpo", []))
        for item in secao.get("itens", []):
            for chave in ("titulo", "resumo", "so_what", "rotulo", "quando", "onde"):
                partes.append(str(item.get(chave, "")))
    return len(re.findall(r"\S+", " ".join(partes)))


# -------------------------------------------------------------------- radar

RASTREADORES = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
                "fbclid", "gclid", "mc_cid", "mc_eid", "igshid", "ref", "originalSubdomain"}


def normalizar_url(url):
    """Chave de deduplicacao: sem esquema, sem www, sem rastreador, sem barra final.

    'https://WWW.Exemplo.com/Post/?utm_source=x' e 'http://exemplo.com/Post' viram a
    mesma chave. O caminho preserva maiusculas — ha servidores que as diferenciam.
    """
    partes = urlsplit(str(url).strip())
    host = partes.netloc.lower().removeprefix("www.")
    # O LinkedIn serve o mesmo post em subdominio de idioma (es./pt./br.). Regra estreita de
    # proposito: em outros dominios o subdominio costuma ser conteudo distinto de verdade
    # (br.hubspot.com nao e www.hubspot.com), e colapsar tudo geraria falso "ja visto".
    if host.endswith("linkedin.com"):
        host = "linkedin.com"
    caminho = partes.path.rstrip("/")
    query = "&".join(sorted(
        p for p in partes.query.split("&")
        if p and p.split("=")[0] not in RASTREADORES))
    return urlunsplit(("", host, caminho, query, "")).lstrip("/")


def carregar_radar():
    """Ultimo registro de cada url, indexado pela chave normalizada."""
    if not RADAR.exists():
        return {}
    with RADAR.open(encoding="utf-8", newline="") as f:
        return {normalizar_url(linha["url"]): linha
                for linha in csv.DictReader(f) if linha.get("url")}


def gravar_radar(novas):
    RADAR.parent.mkdir(parents=True, exist_ok=True)
    existia = RADAR.exists()
    with RADAR.open("a", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUNAS_RADAR)
        if not existia:
            escritor.writeheader()
        for linha in novas:
            escritor.writerow(linha)


def _registro(url, titulo, fonte, marca, status, edicao, data_item, motivo):
    return {"registrado_em": date.today().isoformat(), "url": url, "titulo": titulo,
            "fonte": fonte, "marca": marca, "status": status, "edicao": edicao,
            "data_item": data_item, "motivo": motivo}


def cmd_radar_sync(args):
    """Deriva o radar de uma edicao: itens publicados e cortes com url."""
    dados, _ = ler_edicao(args.pasta)
    rotulo = dados.get("edicao", "")
    conhecidas = carregar_radar()
    novas, ja_tinha = [], 0

    def juntar(url, titulo, fonte, marca, status, data_item, motivo):
        nonlocal ja_tinha
        chave = normalizar_url(url)
        if chave in conhecidas or any(normalizar_url(n["url"]) == chave for n in novas):
            ja_tinha += 1
            return
        novas.append(_registro(url, titulo, fonte, marca, status, rotulo, data_item, motivo))

    for secao in dados.get("secoes", []):
        marca = secao.get("marca", "")
        for item in secao.get("itens") or []:
            url = (item.get("fonte") or {}).get("url")
            if url:
                juntar(url, item.get("titulo") or item.get("rotulo", ""),
                       (item.get("fonte") or {}).get("nome", ""), marca,
                       "publicado", item.get("data", ""), "")
        for fonte in secao.get("fontes") or []:
            if fonte.get("url"):
                juntar(fonte["url"], secao.get("titulo", ""), fonte.get("nome", ""),
                       marca, "publicado", "", "")

    sem_url = 0
    for corte in dados.get("cortes") or []:
        if corte.get("url"):
            juntar(corte["url"], corte.get("item", ""), "", corte.get("marca", ""),
                   "cortado", "", corte.get("motivo", ""))
        else:
            sem_url += 1

    gravar_radar(novas)
    print("radar: %d novo(s), %d ja registrado(s) — %s" % (len(novas), ja_tinha, RADAR))
    if sem_url:
        print("AVISO  %d corte(s) sem 'url' ficaram de fora do radar; sem url nao ha "
              "deduplicacao e o item volta a ser avaliado no mes que vem" % sem_url)
    return 0


def cmd_radar_check(args):
    """Diz o que ja foi visto. Rodar ANTES de apurar."""
    conhecidas = carregar_radar()
    novos = 0
    for url in args.urls:
        linha = conhecidas.get(normalizar_url(url))
        if linha:
            print("JA VISTO  %s\n          %s · %s%s%s" % (
                url, linha["status"], linha["registrado_em"],
                " · edicao %s" % linha["edicao"] if linha["edicao"] else "",
                "\n          motivo: %s" % linha["motivo"] if linha["motivo"] else ""))
        else:
            novos += 1
            print("NOVO      %s" % url)
    print("---\n%d novo(s), %d ja visto(s)" % (novos, len(args.urls) - novos))
    return 0


def cmd_radar_list(args):
    conhecidas = carregar_radar()
    linhas = sorted(conhecidas.values(), key=lambda x: x["registrado_em"], reverse=True)
    if args.status:
        linhas = [x for x in linhas if x["status"] == args.status]
    if args.marca:
        linhas = [x for x in linhas if x["marca"] == args.marca]
    if args.desde:
        linhas = [x for x in linhas if x["registrado_em"] >= args.desde]
    for x in linhas[:args.limite]:
        print("%s  %-9s %-11s %s" % (x["registrado_em"], x["status"],
                                     x["marca"] or "-", x["titulo"][:70]))
        print("%22s%s" % ("", x["url"]))
    print("---\n%d registro(s)" % len(linhas))
    return 0


# --------------------------------------------------------------------- nova

def cmd_nova(args):
    rotulo = args.mes or mes_anterior()
    if not re.fullmatch(r"\d{4}-\d{2}", rotulo):
        sys.exit("erro: mes deve estar no formato AAAA-MM")
    inicio, fim = janela(rotulo)
    cfg = carregar_config()
    pasta = EDICOES / rotulo
    if pasta.exists() and not args.forcar:
        if args.se_preciso:
            print("edicao %s ja aberta: %s" % (rotulo, pasta))
            return 0
        sys.exit("erro: %s ja existe (use --forcar para sobrescrever o esqueleto)" % pasta)
    pasta.mkdir(parents=True, exist_ok=True)

    esqueleto = {
        "edicao": rotulo,
        "janela": {"inicio": inicio.isoformat(), "fim": fim.isoformat()},
        "status": "rascunho",
        "assunto": "",
        "preheader": "",
        "editorial": "",
        "secoes": [],
        "cta": {"texto": "", "url": ""},
        "cortes": [],
        "marcas_avaliadas": [m["id"] for m in cfg["marcas"] if m.get("ativa")],
    }
    (pasta / "edicao.json").write_text(
        json.dumps(esqueleto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    (pasta / "pauta.md").write_text(
        "# Pauta — %s\n\n"
        "Janela de apuracao: **%s a %s**\n\n"
        "## Candidatos\n\n"
        "| # | Item | Fonte | Impacto | Proximidade | Novidade | Evidencia | Total | Decisao |\n"
        "|---|------|-------|---------|-------------|----------|-----------|-------|---------|\n"
        "\n_Corte: total >= 8/12 E evidencia >= 2._\n" % (
            rotulo_por_extenso(rotulo), inicio.strftime("%d/%m/%Y"), fim.strftime("%d/%m/%Y")),
        encoding="utf-8")

    print("edicao criada: %s" % pasta)
    print("janela de apuracao: %s a %s" % (inicio.isoformat(), fim.isoformat()))
    print("marcas a avaliar: %s" % ", ".join(esqueleto["marcas_avaliadas"]))
    return 0


# ------------------------------------------------------------------ validar

def cmd_validar(args):
    dados, _ = ler_edicao(args.pasta)
    cfg = carregar_config()
    ativas = {m["id"] for m in cfg["marcas"] if m.get("ativa")}
    erros, avisos = [], []

    rotulo = dados.get("edicao", "")
    if not re.fullmatch(r"\d{4}-\d{2}", rotulo):
        erros.append("campo 'edicao' ausente ou fora do formato AAAA-MM")
        return _relatorio(erros, avisos, args)
    inicio, fim = janela(rotulo)

    for campo in ("assunto", "preheader", "editorial"):
        if not str(dados.get(campo, "")).strip():
            erros.append("campo obrigatorio vazio: %s" % campo)

    assunto = dados.get("assunto", "")
    if len(assunto) > LIMITE_ASSUNTO:
        erros.append("assunto com %d caracteres (limite %d)" % (len(assunto), LIMITE_ASSUNTO))
    if assunto and dados.get("preheader", "").strip().lower() == assunto.strip().lower():
        erros.append("preheader repete o assunto")

    cta = dados.get("cta") or {}
    if not cta.get("texto") or not cta.get("url"):
        erros.append("CTA incompleto: texto e url sao obrigatorios")
    if not str(cta.get("url", "")).startswith("http"):
        erros.append("CTA com url invalida: %r" % cta.get("url"))

    secoes = dados.get("secoes") or []
    if not secoes:
        erros.append("edicao sem secoes")

    vistos = {}
    for i, secao in enumerate(secoes):
        ref = "secao[%d]" % i
        tipo = secao.get("tipo")
        if tipo not in TIPOS:
            erros.append("%s: tipo invalido %r (validos: %s)" % (ref, tipo, ", ".join(sorted(TIPOS))))
            continue
        if not secao.get("titulo"):
            erros.append("%s: sem titulo" % ref)

        if tipo == "marca":
            marca = secao.get("marca")
            if marca not in ativas:
                erros.append("%s: marca %r nao existe ou esta inativa em config/marcas.json" % (ref, marca))
            if not secao.get("itens"):
                erros.append("%s: bloco da marca %r sem itens — pela regra do silencio, remova o bloco"
                             % (ref, marca))

        if tipo == "deepdive":
            corpo = secao.get("corpo") or []
            if not corpo:
                erros.append("%s: deepdive sem corpo" % ref)
            palavras = len(re.findall(r"\S+", " ".join(corpo)))
            if corpo and not 250 <= palavras <= 800:
                avisos.append("%s: deepdive com %d palavras (alvo 400-600)" % (ref, palavras))

        for j, item in enumerate(secao.get("itens") or []):
            iref = "%s.item[%d]" % (ref, j)
            if tipo == "numeros":
                if not item.get("valor") or not item.get("rotulo"):
                    erros.append("%s: numero precisa de 'valor' e 'rotulo'" % iref)
            elif not item.get("titulo"):
                erros.append("%s: sem titulo" % iref)

            if tipo in TIPOS_COM_ITENS_FONTEADOS:
                fonte = item.get("fonte") or {}
                url = str(fonte.get("url", ""))
                if not fonte.get("nome") or not url:
                    erros.append("%s: fonte incompleta (nome e url obrigatorios)" % iref)
                elif not url.startswith("http"):
                    erros.append("%s: url de fonte invalida: %r" % (iref, url))
                else:
                    vistos.setdefault(url, []).append(iref)

                if not item.get("so_what") and tipo == "movimentos":
                    erros.append("%s: sem 'so_what' — todo movimento precisa dizer o que muda para o leitor" % iref)

                bruta = item.get("data")
                if not bruta:
                    erros.append("%s: sem data" % iref)
                else:
                    try:
                        quando = date.fromisoformat(str(bruta))
                    except ValueError:
                        erros.append("%s: data %r fora do formato AAAA-MM-DD" % (iref, bruta))
                    else:
                        if not (inicio <= quando <= fim) and not item.get("contexto"):
                            erros.append(
                                "%s: data %s fora da janela %s..%s — marque \"contexto\": true "
                                "se for pano de fundo deliberado" % (iref, quando, inicio, fim))

            if tipo == "numeros" and not (item.get("fonte") or {}).get("url"):
                erros.append("%s: numero sem fonte" % iref)

    for url, refs in vistos.items():
        if len(refs) > 1:
            avisos.append("fonte repetida em %s: %s" % (", ".join(refs), url))

    palavras = contar_palavras(dados)
    if not PALAVRAS_MIN <= palavras <= PALAVRAS_MAX:
        avisos.append("edicao com %d palavras (alvo %d-%d)" % (palavras, PALAVRAS_MIN, PALAVRAS_MAX))

    cortes = dados.get("cortes") or []
    sem_url = [c.get("item", "?") for c in cortes if not c.get("url")]
    if sem_url:
        avisos.append("corte(s) sem 'url', que ficam fora do radar e voltam a ser avaliados "
                      "no mes que vem: %s" % "; ".join(x[:60] for x in sem_url))

    citadas = {s.get("marca") for s in secoes if s.get("tipo") == "marca"}
    justificadas = {c.get("marca") for c in cortes}
    for marca in sorted(ativas - citadas - justificadas):
        avisos.append("marca %r nao aparece na edicao nem em 'cortes' — registre o motivo do silencio" % marca)

    return _relatorio(erros, avisos, args, palavras)


def _relatorio(erros, avisos, args, palavras=None):
    for aviso in avisos:
        print("AVISO  %s" % aviso)
    for erro in erros:
        print("ERRO   %s" % erro)
    if palavras is not None:
        print("---\n%d palavras" % palavras)
    if erros:
        print("reprovado: %d erro(s), %d aviso(s)" % (len(erros), len(avisos)))
        return 1
    if avisos and args.estrito:
        print("reprovado no modo estrito: %d aviso(s)" % len(avisos))
        return 1
    print("aprovado%s" % (" com %d aviso(s)" % len(avisos) if avisos else ""))
    return 0


# ------------------------------------------------------------------- render

def e(texto):
    return html.escape(str(texto), quote=True)


def link(url, texto, cor="#0b6bcb"):
    return '<a href="%s" style="color:%s;text-decoration:underline;">%s</a>' % (e(url), cor, e(texto))


def bloco_titulo(texto):
    return ('<tr><td style="padding:28px 32px 8px 32px;">'
            '<h2 style="margin:0;font:600 13px/1.4 -apple-system,BlinkMacSystemFont,\'Segoe UI\',Arial,sans-serif;'
            'letter-spacing:.09em;text-transform:uppercase;color:#7c8798;">%s</h2></td></tr>' % e(texto))


def bloco_paragrafo(texto, tamanho=16):
    return ('<tr><td style="padding:0 32px 14px 32px;">'
            '<p style="margin:0;font:400 %dpx/1.62 -apple-system,BlinkMacSystemFont,\'Segoe UI\',Georgia,serif;'
            'color:#2b3440;">%s</p></td></tr>' % (tamanho, texto))


def bloco_item(item, mostrar_so_what=True):
    partes = ['<tr><td style="padding:0 32px 18px 32px;">',
              '<div style="border-left:3px solid #d8dee7;padding-left:14px;">',
              '<p style="margin:0 0 5px 0;font:600 16px/1.45 -apple-system,BlinkMacSystemFont,'
              '\'Segoe UI\',Arial,sans-serif;color:#121a24;">%s</p>' % e(item.get("titulo", ""))]
    if item.get("resumo"):
        partes.append('<p style="margin:0 0 7px 0;font:400 15px/1.6 -apple-system,BlinkMacSystemFont,'
                      '\'Segoe UI\',Arial,sans-serif;color:#3c4758;">%s</p>' % e(item["resumo"]))
    if mostrar_so_what and item.get("so_what"):
        partes.append('<p style="margin:0 0 7px 0;font:400 15px/1.6 -apple-system,BlinkMacSystemFont,'
                      '\'Segoe UI\',Arial,sans-serif;color:#121a24;">'
                      '<strong style="color:#0b6bcb;">E daí:</strong> %s</p>' % e(item["so_what"]))
    fonte = item.get("fonte") or {}
    if fonte.get("url"):
        rodape = link(fonte["url"], fonte.get("nome", "fonte"), "#6b7688")
        if item.get("data"):
            rodape += ' <span style="color:#98a2b3;">· %s</span>' % e(_data_br(item["data"]))
        if item.get("contexto"):
            rodape += ' <span style="color:#98a2b3;">· contexto</span>'
        partes.append('<p style="margin:0;font:400 13px/1.5 -apple-system,BlinkMacSystemFont,'
                      '\'Segoe UI\',Arial,sans-serif;color:#6b7688;">%s</p>' % rodape)
    partes.append("</div></td></tr>")
    return "".join(partes)


def _data_br(iso):
    try:
        return date.fromisoformat(str(iso)).strftime("%d/%m/%Y")
    except ValueError:
        return str(iso)


def render_secao(secao):
    tipo = secao.get("tipo")
    saida = [bloco_titulo(secao.get("titulo", ""))]

    if tipo == "deepdive":
        for paragrafo in secao.get("corpo") or []:
            saida.append(bloco_paragrafo(e(paragrafo)))
        fontes = secao.get("fontes") or []
        if fontes:
            links = " · ".join(link(f["url"], f.get("nome", f["url"]), "#6b7688") for f in fontes if f.get("url"))
            saida.append('<tr><td style="padding:0 32px 14px 32px;">'
                         '<p style="margin:0;font:400 13px/1.5 -apple-system,BlinkMacSystemFont,'
                         '\'Segoe UI\',Arial,sans-serif;color:#6b7688;">Fontes: %s</p></td></tr>' % links)
        return "".join(saida)

    if tipo == "numeros":
        celulas = []
        for item in secao.get("itens") or []:
            fonte = item.get("fonte") or {}
            rodape = link(fonte["url"], fonte.get("nome", "fonte"), "#6b7688") if fonte.get("url") else ""
            celulas.append(
                '<td width="33%%" valign="top" style="padding:0 8px;">'
                '<p style="margin:0;font:700 26px/1.15 -apple-system,BlinkMacSystemFont,'
                '\'Segoe UI\',Arial,sans-serif;color:#0b6bcb;">%s</p>'
                '<p style="margin:4px 0 0 0;font:400 14px/1.45 -apple-system,BlinkMacSystemFont,'
                '\'Segoe UI\',Arial,sans-serif;color:#3c4758;">%s</p>'
                '<p style="margin:4px 0 0 0;font:400 12px/1.4 -apple-system,BlinkMacSystemFont,'
                '\'Segoe UI\',Arial,sans-serif;color:#6b7688;">%s</p></td>'
                % (e(item.get("valor", "")), e(item.get("rotulo", "")), rodape))
        saida.append('<tr><td style="padding:0 24px 18px 24px;">'
                     '<table role="presentation" width="100%%" cellpadding="0" cellspacing="0" border="0">'
                     '<tr>%s</tr></table></td></tr>' % "".join(celulas))
        return "".join(saida)

    if tipo == "agenda":
        linhas = []
        for item in secao.get("itens") or []:
            titulo = link(item["url"], item.get("titulo", "")) if item.get("url") else e(item.get("titulo", ""))
            detalhe = " · ".join(x for x in (item.get("quando"), item.get("onde")) if x)
            linhas.append('<li style="margin:0 0 8px 0;font:400 15px/1.55 -apple-system,BlinkMacSystemFont,'
                          '\'Segoe UI\',Arial,sans-serif;color:#3c4758;">%s%s</li>'
                          % (titulo, (' <span style="color:#6b7688;">— %s</span>' % e(detalhe)) if detalhe else ""))
        saida.append('<tr><td style="padding:0 32px 14px 32px;">'
                     '<ul style="margin:0;padding-left:18px;">%s</ul></td></tr>' % "".join(linhas))
        return "".join(saida)

    if secao.get("chapeu"):
        saida.append(bloco_paragrafo('<em style="color:#3c4758;">%s</em>' % e(secao["chapeu"]), 15))
    for item in secao.get("itens") or []:
        saida.append(bloco_item(item, mostrar_so_what=True))
    return "".join(saida)


def render_markdown(dados, cfg):
    linhas = ["# %s" % dados.get("titulo") or "Newsletter Neurocraft — %s" % rotulo_por_extenso(dados["edicao"]),
              "", "**Assunto:** %s  " % dados.get("assunto", ""),
              "**Preheader:** %s" % dados.get("preheader", ""), "", dados.get("editorial", ""), ""]
    for secao in dados.get("secoes", []):
        linhas += ["## %s" % secao.get("titulo", ""), ""]
        if secao.get("chapeu"):
            linhas += ["_%s_" % secao["chapeu"], ""]
        for paragrafo in secao.get("corpo") or []:
            linhas += [paragrafo, ""]
        for item in secao.get("itens") or []:
            if secao.get("tipo") == "numeros":
                linhas.append("- **%s** — %s" % (item.get("valor", ""), item.get("rotulo", "")))
            else:
                linhas.append("### %s" % item.get("titulo", ""))
                if item.get("resumo"):
                    linhas += ["", item["resumo"]]
                if item.get("so_what"):
                    linhas += ["", "**E daí:** %s" % item["so_what"]]
            fonte = item.get("fonte") or {}
            if fonte.get("url"):
                linhas += ["", "_Fonte: [%s](%s)%s_" % (
                    fonte.get("nome", "fonte"), fonte["url"],
                    " · %s" % _data_br(item["data"]) if item.get("data") else "")]
            linhas.append("")
        for fonte in secao.get("fontes") or []:
            linhas.append("_Fonte: [%s](%s)_" % (fonte.get("nome", fonte.get("url", "")), fonte.get("url", "")))
        linhas.append("")
    cta = dados.get("cta") or {}
    if cta.get("texto"):
        linhas += ["---", "", "**[%s](%s)**" % (cta["texto"], cta.get("url", "")), ""]
    cortes = dados.get("cortes") or []
    if cortes:
        linhas += ["---", "", "## Cortes (não vai no e-mail)", ""]
        for corte in cortes:
            linhas.append("- **%s** — %s" % (corte.get("marca") or corte.get("item", "?"),
                                             corte.get("motivo", "")))
        linhas.append("")
    return "\n".join(linhas)


def cmd_render(args):
    dados, caminho = ler_edicao(args.pasta)
    cfg = carregar_config()
    pub = cfg["publicacao"]
    if not TEMPLATE.exists():
        sys.exit("erro: template nao encontrado em %s" % TEMPLATE)

    conteudo = "".join(render_secao(s) for s in dados.get("secoes", []))
    editorial = "".join(bloco_paragrafo(e(p))
                        for p in re.split(r"\n\s*\n", dados.get("editorial", "").strip()) if p)
    cta = dados.get("cta") or {}
    rotulo = dados.get("edicao", "")

    saida = (TEMPLATE.read_text(encoding="utf-8")
             .replace("{{ASSUNTO}}", e(dados.get("assunto", "")))
             .replace("{{PREHEADER}}", e(dados.get("preheader", "")))
             .replace("{{EDICAO}}", e(rotulo_por_extenso(rotulo) if rotulo else ""))
             .replace("{{EDITORIAL}}", editorial)
             .replace("{{CONTEUDO}}", conteudo)
             .replace("{{CTA_TEXTO}}", e(cta.get("texto", "")))
             .replace("{{CTA_URL}}", e(cta.get("url", "#")))
             .replace("{{REMETENTE}}", e(pub.get("remetente_nome", "")))
             .replace("{{REMETENTE_EMAIL}}", e(pub.get("remetente_email", "")))
             .replace("{{ANO}}", str(date.today().year)))

    destino = Path(args.pasta)
    (destino / "edicao.html").write_text(saida, encoding="utf-8")
    (destino / "edicao.md").write_text(render_markdown(dados, cfg), encoding="utf-8")

    tamanho = len(saida.encode("utf-8"))
    print("gerado: %s (%.1f KB)" % (destino / "edicao.html", tamanho / 1024))
    print("gerado: %s" % (destino / "edicao.md"))
    if tamanho > LIMITE_HTML_BYTES:
        print("AVISO  HTML acima de %d KB — o Gmail vai truncar a mensagem"
              % (LIMITE_HTML_BYTES // 1024))
        return 1
    return 0


# ---------------------------------------------------------------------- cli

def main():
    parser = argparse.ArgumentParser(description="Ferramenta da newsletter mensal da Neurocraft")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("nova", help="cria a pasta da edicao")
    p.add_argument("mes", nargs="?", help="AAAA-MM (padrao: mes anterior)")
    p.add_argument("--forcar", action="store_true")
    p.add_argument("--se-preciso", action="store_true", dest="se_preciso",
                   help="nao falha se a edicao ja existe (para o radar semanal)")
    p.set_defaults(func=cmd_nova)

    p = sub.add_parser("radar", help="memoria entre edicoes (deduplicacao)")
    rsub = p.add_subparsers(dest="acao", required=True)

    r = rsub.add_parser("check", help="o que ja foi visto — rodar ANTES de apurar")
    r.add_argument("urls", nargs="+")
    r.set_defaults(func=cmd_radar_check)

    r = rsub.add_parser("sync", help="registra itens e cortes de uma edicao no radar")
    r.add_argument("pasta")
    r.set_defaults(func=cmd_radar_sync)

    r = rsub.add_parser("list", help="lista o radar")
    r.add_argument("--status", choices=["publicado", "cortado", "pendente"])
    r.add_argument("--marca")
    r.add_argument("--desde", help="AAAA-MM-DD")
    r.add_argument("--limite", type=int, default=40)
    r.set_defaults(func=cmd_radar_list)

    p = sub.add_parser("validar", help="valida edicao.json")
    p.add_argument("pasta")
    p.add_argument("--estrito", action="store_true", help="trata avisos como erro")
    p.set_defaults(func=cmd_validar)

    p = sub.add_parser("render", help="gera edicao.html e edicao.md")
    p.add_argument("pasta")
    p.set_defaults(func=cmd_render)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
