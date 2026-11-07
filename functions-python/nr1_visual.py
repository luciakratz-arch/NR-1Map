# -*- coding: utf-8 -*-
"""
NR-1 Map — visual compartilhado dos documentos em PDF (cabeçalho, rodapé, bloco de título e trilha do fluxo GRO).
Usado por todos os geradores para que os documentos tenham a mesma cara. Só desenha; não calcula nada de risco.
"""
import os
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Flowable

ESCURO = colors.HexColor("#241B35")
VERDE = colors.HexColor("#12A06F")
VERDE_ESC = colors.HexColor("#0A6E4F")
ROXO = colors.HexColor("#7B00C4")
CINZA = colors.HexColor("#6B7280")
LINHA = colors.HexColor("#E5E1EE")
FUNDO = colors.HexColor("#F7F5FB")

PASSOS = ["Inventário", "Avaliação", "Plano de ação", "Acompanhamento"]
RODAPE = "NR-1 Map  ·  Alinhado à NR-1 (Portaria MTE 1.419/2024)"

_AQUI = os.path.dirname(os.path.abspath(__file__))
LOGO_PADRAO = os.path.join(_AQUI, "logo_nr1map.png")   # logo nova (fundo claro, fundo branco)


def _desenhar_logo(c, caminho, x, y, w, h, ancora):
    """Desenha uma logo dentro da caixa (x, y, w, h) sem distorcer. Falha em silêncio."""
    if not caminho or not os.path.exists(caminho):
        return False
    try:
        c.drawImage(ImageReader(caminho), x, y, width=w, height=h, preserveAspectRatio=True, anchor=ancora, mask="auto")
        return True
    except Exception:
        return False


def cabecalho_rodape(c, doc, titulo_curto, empresa, logo_parceiro=None, logo_empresa=None, rodape=None, linha_extra=None):
    """Cabeçalho + rodapé. Primeira página: logos grandes e linha verde. Demais: faixa enxuta com o título corrido."""
    w, h = A4
    ML = 18 * mm
    c.saveState()
    primeira = doc.page == 1
    esq = logo_parceiro if (logo_parceiro and os.path.exists(logo_parceiro)) else LOGO_PADRAO
    if primeira:
        _desenhar_logo(c, esq, ML, h - 24 * mm, 44 * mm, 14 * mm, "sw")
        _desenhar_logo(c, logo_empresa, w - ML - 46 * mm, h - 28 * mm, 46 * mm, 19 * mm, "se")
        c.setStrokeColor(VERDE); c.setLineWidth(1.6); c.line(ML, h - 31 * mm, w - ML, h - 31 * mm)
    else:
        _desenhar_logo(c, esq, ML, h - 17 * mm, 28 * mm, 9 * mm, "sw")
        c.setFont("Helvetica", 7.8); c.setFillColor(CINZA)
        c.drawRightString(w - ML, h - 13.5 * mm, (titulo_curto + "  ·  " + (empresa or "")).strip(" ·"))
        c.setStrokeColor(VERDE); c.setLineWidth(1.0); c.line(ML, h - 20 * mm, w - ML, h - 20 * mm)
    c.setStrokeColor(LINHA); c.setLineWidth(0.6); c.line(ML, 17 * mm, w - ML, 17 * mm)
    c.setFont("Helvetica", 7.6); c.setFillColor(CINZA)
    c.drawString(ML, 12.5 * mm, rodape or RODAPE)
    c.drawRightString(w - ML, 12.5 * mm, "Página %d" % doc.page)
    if linha_extra and not primeira:
        c.setFont("Helvetica", 6.8); c.drawCentredString(w / 2, 8 * mm, linha_extra)
    c.restoreState()


class BlocoTitulo(Flowable):
    """Título do documento: etiqueta do instrumento, título, subtítulo, cartão com empresa/referência e trilha do fluxo GRO."""

    def __init__(self, titulo, subtitulo, empresa, referencia, instrumento=None, extra=None, largura=None):
        Flowable.__init__(self)
        self.titulo, self.subtitulo, self.empresa, self.referencia = titulo, subtitulo, empresa or "", referencia or ""
        self.instrumento, self.extra = instrumento, extra   # instrumento: 1 a 4 (ou None, sem trilha)
        self.altura = 56 * mm if instrumento else 40 * mm

    def wrap(self, aw, ah):
        self.aw = aw
        return aw, self.altura

    def draw(self):
        c, W = self.canv, self.aw
        y = self.altura
        c.setFont("Helvetica-Bold", 8); c.setFillColor(VERDE_ESC)
        kicker = ("INSTRUMENTO %d DE 4  ·  FLUXO GRO  ·  PGR (NR-1)" % self.instrumento) if self.instrumento else "NR-1 MAP  ·  PGR (NR-1)"
        c.drawString(0, y - 3 * mm, kicker)
        c.setFont("Helvetica-Bold", 22); c.setFillColor(ESCURO)
        c.drawString(0, y - 12 * mm, self.titulo)
        c.setFont("Helvetica", 12.5); c.setFillColor(ROXO)
        c.drawString(0, y - 19 * mm, self.subtitulo)
        top = y - 24 * mm
        c.setFillColor(FUNDO); c.setStrokeColor(LINHA); c.setLineWidth(0.6)
        c.roundRect(0, top - 13 * mm, W, 13 * mm, 3 * mm, fill=1, stroke=1)

        def dado(x, rot, val, maxw):
            c.setFont("Helvetica", 7); c.setFillColor(CINZA); c.drawString(x, top - 4.8 * mm, rot.upper())
            c.setFont("Helvetica-Bold", 9.4); c.setFillColor(ESCURO)
            while val and c.stringWidth(val, "Helvetica-Bold", 9.4) > maxw and len(val) > 4:
                val = val[:-2]
            c.drawString(x, top - 9.6 * mm, val)
        if self.extra:
            dado(5 * mm, "Empresa", self.empresa, W * 0.46)
            dado(W * 0.52, "Referência", self.referencia, W * 0.18)
            dado(W * 0.72, self.extra[0], self.extra[1], W * 0.26)
        else:
            dado(5 * mm, "Empresa", self.empresa, W * 0.62)
            dado(W * 0.68, "Referência", self.referencia, W * 0.30)
        if self.instrumento:
            ty = top - 13 * mm - 3 * mm
            gap = 4 * mm
            pw = (W - 3 * gap) / 4
            for i, nome in enumerate(PASSOS):
                x = i * (pw + gap)
                atual = (i + 1 == self.instrumento)
                c.setFillColor(VERDE if atual else FUNDO); c.setStrokeColor(VERDE if atual else LINHA)
                c.roundRect(x, ty - 7.5 * mm, pw, 7.5 * mm, 2.4 * mm, fill=1, stroke=1)
                c.setFillColor(colors.white if atual else CINZA)
                c.setFont("Helvetica-Bold" if atual else "Helvetica", 8.4)
                c.drawCentredString(x + pw / 2, ty - 5 * mm, "%d  %s" % (i + 1, nome))


_MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]


def mes_ano_pt(dt=None):
    """'novembro de 2026' (o strftime('%B') do servidor sai em inglês)."""
    import datetime
    dt = dt or datetime.datetime.now()
    return "%s de %d" % (_MESES[dt.month - 1], dt.year)
