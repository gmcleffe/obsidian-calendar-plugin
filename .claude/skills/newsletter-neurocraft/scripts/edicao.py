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
VETOS = RAIZ / "config" / "vetos.json"
TEMPLATE = RAIZ / "assets" / "template-email.html"
EDICOES = RAIZ / "edicoes"
RADAR = EDICOES / "radar.csv"
COLUNAS_RADAR = ["registrado_em", "url", "titulo", "fonte", "marca",
                 "status", "edicao", "data_item", "motivo"]

TIPOS = {"mapa", "grafico", "movimentos", "marca", "deepdive", "radar", "numeros", "agenda"}
TIPOS_COM_ITENS_FONTEADOS = {"movimentos", "marca", "radar"}
MESES = ["janeiro", "fevereiro", "marco", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]
MESES_EXIBICAO = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
                  "agosto", "setembro", "outubro", "novembro", "dezembro"]
LIMITE_ASSUNTO = 60
# Formato curto e visual, preferencia de Guilherme Cleffe em 08/10/2026 (era 900-1400).
PALAVRAS_MIN, PALAVRAS_MAX = 600, 1000
DEEPDIVE_MIN, DEEPDIVE_MAX = 150, 450
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


MESES_CURTOS = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


def rotulo_curto_envio(dados):
    """Cabecalho mostra o mes de ENVIO (revisao de 10/11/2026): a edicao de outubro sai em novembro."""
    envio = str(dados.get("envio") or "")
    try:
        quando = date.fromisoformat(envio)
        ano, mes = quando.year, quando.month
    except ValueError:
        ano, mes = (int(x) for x in dados.get("edicao", "1970-01").split("-"))
        ano, mes = (ano + 1, 1) if mes == 12 else (ano, mes + 1)
    return "%s %d" % (MESES_CURTOS[mes - 1], ano)


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
        partes.extend(secao.get("passos", []))
        partes.append(secao.get("destaque", ""))
        partes.append(secao.get("centro", ""))
        partes.append(secao.get("legenda", ""))
        for ramo in secao.get("ramos", []):
            partes.append(ramo.get("titulo", ""))
            partes.extend(ramo.get("pontos", []))
        for item in secao.get("itens", []):
            for chave in ("titulo", "resumo", "so_what", "rotulo", "quando", "onde"):
                partes.append(str(item.get(chave, "")))
            for cartao in item.get("cartoes", []):
                partes.append(cartao.get("titulo", ""))
                partes.extend(cartao.get("pontos", []))
    return len(re.findall(r"\S+", " ".join(partes)))


def carregar_vetos():
    if not VETOS.exists():
        return []
    return json.loads(VETOS.read_text(encoding="utf-8")).get("termos", [])


def textos_publicos(dados):
    """Tudo o que o leitor pode ver: o JSON inteiro menos o que fica na casa."""
    internos = {"cortes", "marcas_avaliadas", "status", "janela", "edicao"}

    def andar(no):
        if isinstance(no, dict):
            for chave, valor in no.items():
                if chave not in internos:
                    yield from andar(valor)
        elif isinstance(no, list):
            for valor in no:
                yield from andar(valor)
        elif isinstance(no, str):
            yield no
    return list(andar(dados))


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
    novas, ja_tinha, corrigidas, vistas = [], 0, 0, set()

    def juntar(url, titulo, fonte, marca, status, data_item, motivo):
        nonlocal ja_tinha, corrigidas
        chave = normalizar_url(url)
        # Uma url por rodada: a mesma fonte pode sustentar varios cortes com motivos
        # diferentes, e vale o primeiro. Sem isso o sync alterna entre eles a cada vez.
        if chave in vistas:
            ja_tinha += 1
            return
        vistas.add(chave)
        conhecida = conhecidas.get(chave)
        # Registro de outra edicao e historia: nao se reescreve. Da mesma edicao, a
        # pauta pode ter mudado depois do primeiro sync (item publicado que acabou
        # cortado na revisao). O radar e so-acrescimo e a ultima linha vale, entao a
        # correcao entra como linha nova.
        if conhecida and (conhecida["edicao"] != rotulo
                          or (conhecida["status"], conhecida["motivo"]) == (status, motivo)):
            ja_tinha += 1
            return
        if conhecida:
            corrigidas += 1
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
    print("radar: %d novo(s), %d corrigido(s), %d ja registrado(s) — %s"
          % (len(novas) - corrigidas, corrigidas, ja_tinha, RADAR))
    orfaos = [linha for chave, linha in conhecidas.items()
              if linha["edicao"] == rotulo and chave not in vistas]
    if orfaos:
        print("AVISO  %d registro(s) desta edicao no radar nao aparecem mais na edicao, nem "
              "publicados nem em cortes — registre o corte com a url:" % len(orfaos))
        for linha in orfaos:
            print("       %s · %s" % (linha["status"], linha["url"]))
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
    # O prefixo fixo ("[Neurocraft.ai newsletter]") nao conta no limite. Passar do limite e aviso,
    # nao erro: o editor ja enviou assunto mais longo de proposito (09/11/2026).
    prefixo = cfg["publicacao"].get("prefixo_assunto", "")
    miolo = assunto[len(prefixo):].strip() if prefixo and assunto.startswith(prefixo) else assunto
    if len(miolo) > LIMITE_ASSUNTO:
        avisos.append("assunto com %d caracteres sem o prefixo (alvo ate %d)" % (len(miolo), LIMITE_ASSUNTO))
    if prefixo and not assunto.startswith(prefixo):
        avisos.append("assunto sem o prefixo fixo %r" % prefixo)
    if assunto and dados.get("preheader", "").strip().lower() == assunto.strip().lower():
        erros.append("preheader repete o assunto")

    cta = dados.get("cta") or {}
    if not cta.get("texto") or not cta.get("url"):
        erros.append("CTA incompleto: texto e url sao obrigatorios")
    # mailto: vale quando o CTA e "responda este e-mail" (preferencia de 09/11/2026).
    if not str(cta.get("url", "")).startswith(("http", "mailto:")):
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
            corpo = (secao.get("passos") or []) + (secao.get("corpo") or [])
            if not corpo:
                erros.append("%s: deepdive sem corpo" % ref)
            palavras = len(re.findall(r"\S+", " ".join(corpo + [secao.get("destaque", "")])))
            if corpo and not DEEPDIVE_MIN <= palavras <= DEEPDIVE_MAX:
                avisos.append("%s: deepdive com %d palavras (alvo %d-%d)"
                              % (ref, palavras, DEEPDIVE_MIN, DEEPDIVE_MAX))

        if tipo == "grafico":
            # Grafico redesenhado pela casa a partir de dado publico: a imagem mora na pasta
            # da edicao e o credito vai na legenda e dentro da propria imagem.
            # Preferencia de 10/11/2026: barras em HTML ('barras') no lugar de imagem hospedada.
            barras = secao.get("barras") or []
            img = secao.get("imagem", "")
            if barras:
                for k, barra in enumerate(barras):
                    if not barra.get("rotulo") or not isinstance(barra.get("valor"), (int, float)):
                        erros.append("%s.barra[%d]: precisa de 'rotulo' e 'valor' numerico" % (ref, k))
            elif not img:
                erros.append("%s: grafico sem 'barras' nem 'imagem'" % ref)
            elif not (Path(args.pasta) / img).is_file():
                erros.append("%s: imagem %r nao existe na pasta da edicao" % (ref, img))
            if img and not barras and not secao.get("alt"):
                erros.append("%s: grafico sem 'alt' — o texto alternativo e o que le quem bloqueia imagem" % ref)
            fonte = secao.get("fonte") or {}
            if not fonte.get("nome") or not str(fonte.get("url", "")).startswith("http"):
                erros.append("%s: grafico sem fonte (nome e url)" % ref)

        if tipo == "mapa":
            # O mapa resume a edicao; nao traz fato proprio, entao nao leva fonte.
            # Cada ponto precisa estar sustentado por um item fonteado mais abaixo.
            ramos = secao.get("ramos") or []
            if not secao.get("centro"):
                erros.append("%s: mapa sem 'centro'" % ref)
            if not 2 <= len(ramos) <= 4:
                erros.append("%s: mapa com %d ramos (use 2 a 4)" % (ref, len(ramos)))
            for k, ramo in enumerate(ramos):
                pontos = ramo.get("pontos") or []
                if not ramo.get("titulo") or not 1 <= len(pontos) <= 4:
                    erros.append("%s.ramo[%d]: precisa de 'titulo' e de 1 a 4 'pontos'" % (ref, k))
                for ponto in pontos:
                    if len(ponto) > 90:
                        avisos.append("%s.ramo[%d]: ponto com %d caracteres — mapa pede frase curta"
                                      % (ref, k, len(ponto)))

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

                g = item.get("grafico") or {}
                if g and (not g.get("barras") or not (g.get("fonte") or {}).get("url")):
                    erros.append("%s: grafico do item precisa de 'barras' e 'fonte'" % iref)

                for extra in item.get("links_extras") or []:
                    if not extra.get("nome") or not str(extra.get("url", "")).startswith("http"):
                        erros.append("%s: link extra precisa de 'nome' e url http" % iref)

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

    # Link colado do Gmail para o Outlook vira google.com/url?q=... e expira (envio de 09/11/2026).
    for texto in textos_publicos(dados):
        if re.search(r"(?i)https?://(www\.)?google\.[a-z.]+/url\?", texto):
            erros.append("link passa por redirecionador do Google: %s" % texto[:80])

    cortes = dados.get("cortes") or []
    sem_url = [c.get("item", "?") for c in cortes if not c.get("url")]
    if sem_url:
        avisos.append("corte(s) sem 'url', que ficam fora do radar e voltam a ser avaliados "
                      "no mes que vem: %s" % "; ".join(x[:60] for x in sem_url))

    # Veto vale para edicao em producao. Edicao ja enviada e registro historico.
    if dados.get("status") != "enviada":
        publico = "\n".join(textos_publicos(dados))
        for veto in carregar_vetos():
            if re.search(r"(?i)\b%s\b" % re.escape(veto["termo"]), publico):
                erros.append("termo vetado na edicao: %r (desde %s, %s: %s)" % (
                    veto["termo"], veto.get("desde", "?"), veto.get("quem", "?"), veto.get("motivo", "")))

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


# Paleta e componentes da identidade visual revisada por Marcos de Almeida (10/11/2026).
# Referencia: edicoes/2026-10/revisao-marcos.html.
CORES = {
    "azul":    {"forte": "#0B6BCB", "texto": "#0B6BCB", "fundo": "#EAF3FE", "barra": "#5CB8FF", "trilho": "#D6E8FB", "stat": "#5CB8FF"},
    "dourado": {"forte": "#E8B84A", "texto": "#A87512", "fundo": "#FFF6E0", "barra": "#E8B84A", "trilho": "#F7E7BE", "stat": "#F6D77B"},
    "laranja": {"forte": "#E8590C", "texto": "#C2410C", "fundo": "#FFEDE6", "barra": "#FF8A4C", "trilho": "#FBDCCB", "stat": "#FF8A4C"},
    "verde":   {"forte": "#0E9F86", "texto": "#0B7A67", "fundo": "#E3F7F3", "barra": "#3FD9B5", "trilho": "#C9EFE6", "stat": "#3FD9B5"},
}
ORDEM_CORES = ["azul", "dourado", "laranja", "verde"]
TINTA = "#0A1630"
TEXTO = "#33415C"
TEXTO_CARTAO = "#24324A"
CINZA = "#7A869C"


def cor(nome, indice=0):
    return CORES.get(nome) or CORES[ORDEM_CORES[indice % len(ORDEM_CORES)]]


def link(url, texto, cor_link="#0B6BCB", negrito=False):
    peso = "font-weight:600;" if negrito else ""
    return '<a href="%s" style="color:%s;%stext-decoration:underline;">%s</a>' % (e(url), cor_link, peso, e(texto))


def _linha(conteudo, topo=30, base=6):
    return ('<tr><td class="px" style="padding:%dpx 36px %dpx 36px;">%s</td></tr>' % (topo, base, conteudo))


def rotulo_pequeno(texto, cor_texto="#1B3F8B"):
    return ('<p style="margin:0 0 4px 0;font-size:12px;font-weight:bold;letter-spacing:1.5px;'
            'text-transform:uppercase;color:%s;">%s</p>' % (cor_texto, e(texto)))


def pilula(texto, c):
    # Dourado e claro demais para texto branco: a pilula dourada leva texto escuro.
    tinta = TINTA if c is CORES["dourado"] else "#FFFFFF"
    return ('<div style="display:inline-block;background:%s;color:%s;font-size:11px;font-weight:bold;'
            'letter-spacing:1.2px;text-transform:uppercase;padding:4px 10px;border-radius:4px;">%s</div>'
            % (c["forte"], tinta, e(texto)))


def titulo_h2(texto, topo=12):
    return ('<h2 style="margin:%dpx 0 10px 0;font-size:22px;line-height:28px;color:%s;">%s</h2>'
            % (topo, TINTA, e(texto)))


def paragrafo(texto, tamanho=15):
    return ('<p style="margin:0 0 14px 0;font-size:%dpx;line-height:24px;color:%s;">%s</p>'
            % (tamanho, TEXTO, texto))


def caixa_e_dai(texto, c):
    return ('<table role="presentation" width="100%%" cellpadding="0" cellspacing="0" border="0" '
            'style="background:#F3F7FD;border-radius:8px;margin:0 0 4px 0;"><tr>'
            '<td style="padding:14px 18px;font-size:14px;line-height:22px;color:%s;">'
            '<strong style="color:%s;">&#128073; E daí?</strong> %s</td></tr></table>'
            % (TEXTO_CARTAO, c["texto"], e(texto)))


def linhas_de_fonte(item, c):
    """Fonte principal com data e links extras (podcast, PDF, pagina do programa)."""
    fonte = item.get("fonte") or {}
    linhas = []
    if fonte.get("url"):
        txt = "&#128279; " + link(fonte["url"], fonte.get("nome", "fonte"), c["texto"], True)
        if item.get("data"):
            txt += " &middot; %s" % e(_data_br(item["data"]))
        linhas.append(txt)
    for extra in item.get("links_extras") or []:
        if extra.get("url"):
            icone = e(extra.get("icone", "")) or "&#128279;"
            linhas.append("%s %s" % (icone, link(extra["url"], extra.get("nome", extra["url"]), c["texto"], True)))
    if not linhas:
        return ""
    return ('<p style="margin:12px 0 0 0;font-size:13px;line-height:22px;color:%s;">%s</p>'
            % (CINZA, "<br>".join(linhas)))


def cartoes(cards, c_padrao=None):
    """Grade de cartoes em duas colunas; empilha no celular (classe .stack)."""
    celulas = []
    for i, card in enumerate(cards):
        c = cor(card.get("cor"), i) if c_padrao is None else c_padrao
        titulo = ((e(card["icone"]) + " ") if card.get("icone") else "") + e(card.get("titulo", ""))
        corpo = card.get("html") or "<br>".join("&#9656; %s" % e(p) for p in card.get("pontos") or [])
        celulas.append(
            '<td class="stack" width="50%%" valign="top" style="padding:8px;">'
            '<table role="presentation" width="100%%" cellpadding="0" cellspacing="0" border="0" '
            'style="background:%s;border-left:5px solid %s;border-radius:10px;"><tr><td style="padding:16px 18px;">'
            '<p style="margin:0 0 8px 0;font-size:14px;font-weight:800;color:%s;">%s</p>'
            '<p style="margin:0;font-size:14px;line-height:22px;color:%s;">%s</p>'
            '</td></tr></table></td>' % (c["fundo"], c["forte"], c["texto"], titulo, TEXTO_CARTAO, corpo))
    linhas = "".join("<tr>%s</tr>" % "".join(celulas[i:i + 2] +
                                             (['<td class="stack" width="50%"></td>'] if len(celulas[i:i + 2]) == 1 else []))
                     for i in range(0, len(celulas), 2))
    return ('<table role="presentation" width="100%%" cellpadding="0" cellspacing="0" border="0">%s</table>' % linhas)


def _data_br(iso):
    try:
        return date.fromisoformat(str(iso)).strftime("%d/%m/%Y")
    except ValueError:
        return str(iso)


def render_mapa(secao):
    """Mapa mental: rotulo, tese do mes como titulo e ramos em cartoes coloridos."""
    cabeca = rotulo_pequeno(secao.get("titulo", "")) + titulo_h2(secao.get("centro", ""), 0)
    grade = cartoes(secao.get("ramos") or [])
    return (_linha(cabeca, 32, 8) +
            '<tr><td class="px" style="padding:0 28px 8px 28px;">%s</td></tr>' % grade)


def render_barras(secao, c):
    """Grafico de barras em HTML puro: nao depende de imagem hospedada nem de bloqueio de imagem."""
    maximo = max([float(b.get("valor", 0)) for b in secao.get("barras") or []] + [100.0])
    blocos = []
    for b in secao.get("barras") or []:
        pct = max(1, min(99, round(float(b.get("valor", 0)) * 100 / maximo)))
        rotulo_valor = e(b.get("texto") or ("%s%%" % b.get("valor")))
        # Barra curta demais para caber o numero: o numero vai no trilho.
        if pct >= 12:
            cheia = ('<td width="%d%%" style="background:%s;height:22px;border-radius:4px 0 0 4px;font-size:12px;'
                     'font-weight:bold;color:#FFFFFF;padding-left:8px;">%s</td>' % (pct, c["barra"], rotulo_valor))
            vazia = ('<td width="%d%%" style="background:%s;height:22px;border-radius:0 4px 4px 0;">&nbsp;</td>'
                     % (100 - pct, c["trilho"]))
        else:
            cheia = ('<td width="%d%%" style="background:%s;height:22px;border-radius:4px 0 0 4px;">&nbsp;</td>'
                     % (pct, c["texto"]))
            vazia = ('<td width="%d%%" style="background:%s;height:22px;border-radius:0 4px 4px 0;font-size:12px;'
                     'font-weight:bold;color:%s;padding-left:8px;">%s</td>' % (100 - pct, c["trilho"], c["texto"], rotulo_valor))
        blocos.append('<tr><td style="padding:6px 20px 10px 20px;">'
                      '<p style="margin:0 0 4px 0;font-size:13px;color:%s;">%s</p>'
                      '<table role="presentation" width="100%%" cellpadding="0" cellspacing="0" border="0"><tr>%s%s</tr></table>'
                      '</td></tr>' % (TEXTO, e(b.get("rotulo", "")), cheia, vazia))
    titulo = ('<tr><td style="padding:18px 20px 6px 20px;font-size:12px;font-weight:bold;letter-spacing:1px;'
              'text-transform:uppercase;color:%s;">%s</td></tr>' % (c["texto"], e(secao.get("titulo", ""))))
    return ('<table role="presentation" width="100%%" cellpadding="0" cellspacing="0" border="0" '
            'style="background:%s;border-radius:10px;">%s%s<tr><td style="height:8px;line-height:8px;">&nbsp;</td></tr></table>'
            % (c["fundo"], titulo, "".join(blocos)))


def render_item(item, c, mostrar_so_what=True, nivel_titulo=True):
    partes = []
    if nivel_titulo and item.get("titulo"):
        partes.append('<h3 style="margin:6px 0 8px 0;font-size:17px;line-height:24px;color:%s;">%s</h3>'
                      % (TINTA, e(item["titulo"])))
    if item.get("cartoes"):
        partes.append(cartoes(item["cartoes"], c))
    elif item.get("resumo"):
        partes.append(paragrafo(e(item["resumo"])))
    if item.get("grafico"):
        # Grafico logo depois do fato que ele mostra, antes do "e dai" (revisao de 10/11/2026).
        g = item["grafico"]
        fonte = g.get("fonte") or {}
        legenda = e(g.get("legenda", ""))
        if fonte.get("url"):
            legenda += (" " if legenda else "") + "Fonte: " + link(fonte["url"], fonte.get("nome", "fonte"), CINZA)
        partes.append(render_barras(g, c) +
                      '<p style="margin:6px 0 14px 0;font-size:11px;color:%s;">%s</p>' % (CINZA, legenda))
    if mostrar_so_what and item.get("so_what"):
        partes.append(caixa_e_dai(item["so_what"], c))
    partes.append(linhas_de_fonte(item, c))
    return "".join(partes)


def render_secao(secao, indice=0):
    tipo = secao.get("tipo")
    c = cor(secao.get("cor"), indice)

    if tipo == "mapa":
        return render_mapa(secao)

    if tipo == "numeros":
        # Faixa de numeros em fundo escuro (stat strip). Fonte e obrigatoria e vai na legenda.
        itens = secao.get("itens") or []
        largura = 100 // max(len(itens), 1)
        celulas, fontes = [], []
        for i, item in enumerate(itens):
            ci = cor(item.get("cor"), i)
            borda = "border-left:1px solid #22355E;" if i else ""
            celulas.append(
                '<td class="stack" width="%d%%" align="center" style="padding:20px 10px;%s">'
                '<div class="stat" style="font-size:38px;font-weight:800;color:%s;line-height:42px;">%s</div>'
                '<div style="font-size:12px;line-height:17px;color:#C9D6EE;">%s</div></td>'
                % (largura, borda, ci["stat"], e(item.get("valor", "")), e(item.get("rotulo", ""))))
            fonte = item.get("fonte") or {}
            if fonte.get("url"):
                fontes.append(link(fonte["url"], fonte.get("nome", "fonte"), CINZA))
        rodape = ('<p style="margin:6px 0 0 0;font-size:11px;color:%s;">Fontes: %s</p>'
                  % (CINZA, " &middot; ".join(fontes))) if fontes else ""
        return _linha('<table role="presentation" width="100%%" cellpadding="0" cellspacing="0" border="0" '
                      'style="background:%s;border-radius:12px;"><tr>%s</tr></table>%s'
                      % (TINTA, "".join(celulas), rodape), 20, 20)

    cabeca = (pilula(secao["rotulo"], c) + titulo_h2(secao.get("titulo", ""))) if secao.get("rotulo") \
        else titulo_h2(secao.get("titulo", ""), 0)

    if tipo == "grafico":
        fonte = secao.get("fonte") or {}
        legenda = e(secao.get("legenda", ""))
        if fonte.get("url"):
            legenda += (" " if legenda else "") + "Fonte: " + link(fonte["url"], fonte.get("nome", "fonte"), CINZA)
        if secao.get("barras"):
            corpo = render_barras(secao, c)
        else:
            corpo = ('<img src="%s" width="568" alt="%s" style="display:block;width:100%%;max-width:568px;'
                     'height:auto;border:0;border-radius:6px;">' % (e(secao.get("imagem", "")), e(secao.get("alt", ""))))
        return _linha(corpo + '<p style="margin:6px 0 0 0;font-size:11px;color:%s;">%s</p>' % (CINZA, legenda), 4, 14)

    if tipo == "deepdive":
        # Secao da casa (oferta, metodo): cartao com passos numerados e condicao em destaque.
        partes = []
        for n, passo in enumerate(secao.get("passos") or [], 1):
            partes.append(
                '<tr><td width="48" valign="top" style="padding:0 0 16px 0;"><div style="width:36px;height:36px;'
                'line-height:36px;border-radius:18px;background:%s;color:#F6D77B;text-align:center;font-weight:800;'
                'font-size:16px;">%d</div></td><td valign="top" style="padding:0 0 16px 0;font-size:15px;'
                'line-height:23px;color:%s;">%s</td></tr>' % (TINTA, n, TEXTO, e(passo)))
        passos = ('<table role="presentation" width="100%%" cellpadding="0" cellspacing="0" border="0">%s</table>'
                  % "".join(partes)) if partes else ""
        extra = []
        if secao.get("destaque"):
            extra.append('<table role="presentation" width="100%%" cellpadding="0" cellspacing="0" border="0" '
                         'style="background:%s;border-radius:8px;margin:0 0 14px 0;"><tr>'
                         '<td style="padding:14px 18px;font-size:14px;line-height:22px;color:#FFFFFF;">%s</td></tr></table>'
                         % (TINTA, e(secao["destaque"])))
        for p in secao.get("corpo") or []:
            extra.append('<p style="margin:0 0 10px 0;font-size:14px;line-height:22px;color:%s;">%s</p>' % (TEXTO, e(p)))
        fontes = secao.get("fontes") or []
        if fontes:
            links = " &middot; ".join(link(f["url"], f.get("nome", f["url"]), CINZA) for f in fontes if f.get("url"))
            extra.append('<p style="margin:0;font-size:12px;line-height:20px;color:%s;">Fontes: %s</p>' % (CINZA, links))
        cartao = ('<table role="presentation" width="100%%" cellpadding="0" cellspacing="0" border="0" '
                  'style="background:#FFF9EC;border:1px solid #F1D99A;border-radius:12px;">'
                  '<tr><td style="padding:24px 24px 4px 24px;">%s</td></tr>'
                  '<tr><td style="padding:0 24px;">%s</td></tr>'
                  '<tr><td style="padding:4px 24px 20px 24px;">%s</td></tr></table>'
                  % (cabeca, passos, "".join(extra)))
        return _linha(cartao)

    if tipo == "agenda":
        linhas = []
        for item in secao.get("itens") or []:
            titulo = link(item["url"], item.get("titulo", ""), c["texto"], True) if item.get("url") else e(item.get("titulo", ""))
            detalhe = " &middot; ".join(e(x) for x in (item.get("quando"), item.get("onde")) if x)
            linhas.append('<li style="margin:0 0 8px 0;font-size:15px;line-height:24px;color:%s;">%s%s</li>'
                          % (TEXTO, titulo, (' <span style="color:%s;">— %s</span>' % (CINZA, detalhe)) if detalhe else ""))
        return _linha(cabeca + '<ul style="margin:0;padding-left:18px;">%s</ul>' % "".join(linhas))

    partes = [cabeca]
    if secao.get("chapeu"):
        partes.append(paragrafo('<em>%s</em>' % e(secao["chapeu"])))
    itens = secao.get("itens") or []
    for item in itens:
        # Item unico cujo titulo repete o da secao nao ganha subtitulo.
        partes.append(render_item(item, c, True, not (len(itens) == 1 and item.get("titulo") == secao.get("titulo"))))
    return _linha("".join(partes))


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
        if secao.get("tipo") == "grafico":
            fonte = secao.get("fonte") or {}
            linhas += ["![%s](%s)" % (secao.get("alt", ""), secao.get("imagem", "")), "",
                       "_%s Fonte: [%s](%s)_" % (secao.get("legenda", ""), fonte.get("nome", ""), fonte.get("url", "")), ""]
        if secao.get("tipo") == "mapa":
            linhas += ["**%s**" % secao.get("centro", ""), ""]
            for ramo in secao.get("ramos") or []:
                linhas.append("- **%s**" % ramo.get("titulo", ""))
                linhas += ["  - %s" % p for p in ramo.get("pontos") or []]
            linhas.append("")
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

    conteudo = "".join(render_secao(s, i) for i, s in enumerate(dados.get("secoes", [])))
    editorial = "".join(
        '<p style="margin:0 0 18px 0;font-size:15px;line-height:24px;color:#C9D6EE;">%s</p>' % e(p)
        for p in re.split(r"\n\s*\n", dados.get("editorial", "").strip()) if p)
    cta = dados.get("cta") or {}
    rotulo = dados.get("edicao", "")
    marca = pub.get("marca_visual") or {}

    chapeu = dados.get("chapeu", "")
    chapeu_html = ('<div style="display:inline-block;background:#E8B84A;color:#0A1630;font-size:11px;font-weight:bold;'
                   'letter-spacing:1.5px;text-transform:uppercase;padding:5px 10px;border-radius:20px;">%s</div>'
                   % e(chapeu)) if chapeu else ""
    subtitulo = dados.get("subtitulo", "")
    subtitulo_html = ('<p style="margin:0 0 20px 0;font-size:20px;line-height:28px;color:#F6D77B;font-weight:700;">%s</p>'
                      % e(subtitulo)) if subtitulo else ""
    # O mesmo CTA pode aparecer no topo e no fim: uma acao, dois pontos de clique.
    cta_topo = ""
    if cta.get("texto_topo"):
        cta_topo = ('<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>'
                    '<td style="border-radius:8px;background:#E8B84A;"><a href="%s" style="display:inline-block;'
                    'padding:14px 24px;font-size:15px;font-weight:bold;color:#0A1630;text-decoration:none;">%s</a>'
                    '</td></tr></table>' % (e(cta.get("url", "#")), e(cta["texto_topo"])))
    pergunta = ""
    if cta.get("pergunta"):
        pergunta += ('<p style="margin:0 0 6px 0;font-size:22px;line-height:28px;font-weight:800;color:#FFFFFF;">%s</p>'
                     % e(cta["pergunta"]))
    if cta.get("apoio"):
        pergunta += ('<p style="margin:0 0 18px 0;font-size:14px;line-height:22px;color:#C9D6EE;">%s</p>'
                     % e(cta["apoio"]))
    tagline = pub.get("tagline", "")

    saida = (TEMPLATE.read_text(encoding="utf-8")
             .replace("{{ASSUNTO}}", e(dados.get("assunto", "")))
             .replace("{{PREHEADER}}", e(dados.get("preheader", "")))
             .replace("{{EDICAO_CURTA}}", e(rotulo_curto_envio(dados)))
             .replace("{{MARCA}}", e(marca.get("nome", pub.get("remetente_nome", ""))))
             .replace("{{MARCA_SUFIXO}}", e(marca.get("sufixo", "")))
             .replace("{{CHAPEU}}", chapeu_html)
             .replace("{{TITULO_HERO}}", e(dados.get("titulo_hero") or dados.get("assunto", "")))
             .replace("{{SUBTITULO}}", subtitulo_html)
             .replace("{{EDITORIAL}}", editorial)
             .replace("{{CTA_TOPO}}", cta_topo)
             .replace("{{CONTEUDO}}", conteudo)
             .replace("{{CTA_PERGUNTA}}", pergunta)
             .replace("{{CTA_TEXTO}}", e(cta.get("texto", "")))
             .replace("{{CTA_URL}}", e(cta.get("url", "#")))
             .replace("{{SITE_URL}}", e(marca.get("site", "")))
             .replace("{{SITE_ROTULO}}", e(marca.get("site_rotulo", "")))
             .replace("{{REMETENTE}}", e(pub.get("remetente_nome", "")))
             .replace("{{TAGLINE}}", (" &middot; " + e(tagline)) if tagline else "")
             .replace("{{REMETENTE_EMAIL}}", e(pub.get("remetente_email", "")))
             .replace("{{ANO}}", str(date.today().year)))

    sobras = re.findall(r"\{\{[A-Z_]+\}\}", saida)
    if sobras:
        sys.exit("erro: placeholders nao preenchidos no template: %s" % ", ".join(sorted(set(sobras))))

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
