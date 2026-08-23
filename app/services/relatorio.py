"""Geração do relatório PDF de notificações e empréstimos do BiblioAvisa."""

from __future__ import annotations

from datetime import date, datetime
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.repositories.relatorios import buscar_dados_relatorio


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = PROJECT_ROOT / "reports"


def _texto(valor: object | None) -> str:
    if valor is None:
        return "-"
    return escape(str(valor))


def _data(valor: object | None) -> str:
    if isinstance(valor, datetime):
        return valor.strftime("%d/%m/%Y %H:%M")
    if isinstance(valor, date):
        return valor.strftime("%d/%m/%Y")
    return "-" if valor is None else _texto(valor)


def _paragrafo(valor: object | None, estilo: ParagraphStyle) -> Paragraph:
    return Paragraph(_texto(valor), estilo)


def _estilos() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle(
            "TituloBiblioAvisa",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "subtitulo": ParagraphStyle(
            "SubtituloBiblioAvisa",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            spaceBefore=8,
            spaceAfter=6,
        ),
        "normal": ParagraphStyle(
            "NormalBiblioAvisa",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
        ),
        "tabela": ParagraphStyle(
            "TabelaBiblioAvisa",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=9,
        ),
        "cabecalho": ParagraphStyle(
            "CabecalhoTabelaBiblioAvisa",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=9,
        ),
    }


def _tabela(cabecalhos: list[str], linhas: list[list[object]], larguras: list[float], estilos: dict[str, ParagraphStyle]) -> Table:
    dados: list[list[object]] = [
        [_paragrafo(item, estilos["cabecalho"]) for item in cabecalhos]
    ]
    for linha in linhas:
        dados.append([_paragrafo(item, estilos["tabela"]) for item in linha])

    tabela = Table(dados, colWidths=larguras, repeatRows=1, hAlign="LEFT")
    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8E8E8")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B5B5B5")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return tabela


def _rodape(canvas, documento) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.drawString(15 * mm, 8 * mm, "BiblioAvisa - relatório gerado automaticamente")
    canvas.drawRightString(282 * mm, 8 * mm, f"Página {documento.page}")
    canvas.restoreState()


def gerar_relatorio_pdf(
    data_inicio: date,
    data_fim: date,
    caminho_saida: str | Path | None = None,
) -> Path:
    """Consulta o PostgreSQL e gera um relatório PDF no período informado."""
    dados = buscar_dados_relatorio(data_inicio, data_fim)
    gerado_em = datetime.now()

    if caminho_saida is None:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        caminho = REPORTS_DIR / f"relatorio_biblioavisa_{gerado_em:%Y%m%d_%H%M%S}.pdf"
    else:
        caminho = Path(caminho_saida).expanduser().resolve()
        caminho.parent.mkdir(parents=True, exist_ok=True)

    estilos = _estilos()
    documento = SimpleDocTemplate(
        str(caminho),
        pagesize=landscape(A4),
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=14 * mm,
        bottomMargin=15 * mm,
        title="Relatório BiblioAvisa",
        author="BiblioAvisa",
    )

    elementos: list[object] = [
        Paragraph("Relatório BiblioAvisa", estilos["titulo"]),
        Paragraph(
            f"Período consultado: {_data(data_inicio)} a {_data(data_fim)}<br/>"
            f"Gerado em: {_data(gerado_em)}",
            estilos["normal"],
        ),
        Spacer(1, 5 * mm),
    ]

    mensagens = dados["mensagens"]
    elementos.append(Paragraph(f"Mensagens enviadas no período ({len(mensagens)})", estilos["subtitulo"]))
    if mensagens:
        linhas_mensagens = [
            [
                _data(item["data_mensagem"]),
                item["usuario_nome"],
                item["livro_titulo"] or "-",
                item["tipo"],
                item["status"],
                item["mensagem"],
            ]
            for item in mensagens
        ]
        elementos.append(
            _tabela(
                ["Data/hora", "Usuário", "Livro", "Tipo", "Status", "Mensagem"],
                linhas_mensagens,
                [28 * mm, 37 * mm, 45 * mm, 30 * mm, 22 * mm, 92 * mm],
                estilos,
            )
        )
    else:
        elementos.append(Paragraph("Nenhuma mensagem enviada no período informado.", estilos["normal"]))

    atrasados = dados["emprestimos_atrasados"]
    elementos.extend([Spacer(1, 5 * mm), Paragraph(f"Empréstimos atrasados ({len(atrasados)})", estilos["subtitulo"])])
    if atrasados:
        elementos.append(
            _tabela(
                ["ID", "Usuário", "Livro", "Empréstimo", "Vencimento", "Status"],
                [
                    [
                        item["id"],
                        item["usuario_nome"],
                        item["livro_titulo"],
                        _data(item["data_emprestimo"]),
                        _data(item["data_prevista_devolucao"]),
                        item["status"],
                    ]
                    for item in atrasados
                ],
                [16 * mm, 48 * mm, 70 * mm, 33 * mm, 33 * mm, 28 * mm],
                estilos,
            )
        )
    else:
        elementos.append(Paragraph("Nenhum empréstimo atrasado na data final do relatório.", estilos["normal"]))

    proximos = dados["emprestimos_proximos"]
    dias = dados["dias_proximo_vencimento"]
    elementos.extend(
        [
            Spacer(1, 5 * mm),
            Paragraph(
                f"Empréstimos com vencimento nos próximos {dias} dias ({len(proximos)})",
                estilos["subtitulo"],
            ),
        ]
    )
    if proximos:
        elementos.append(
            _tabela(
                ["ID", "Usuário", "Livro", "Empréstimo", "Vencimento", "Status"],
                [
                    [
                        item["id"],
                        item["usuario_nome"],
                        item["livro_titulo"],
                        _data(item["data_emprestimo"]),
                        _data(item["data_prevista_devolucao"]),
                        item["status"],
                    ]
                    for item in proximos
                ],
                [16 * mm, 48 * mm, 70 * mm, 33 * mm, 33 * mm, 28 * mm],
                estilos,
            )
        )
    else:
        elementos.append(Paragraph("Nenhum empréstimo próximo do vencimento nesse intervalo.", estilos["normal"]))

    documento.build(elementos, onFirstPage=_rodape, onLaterPages=_rodape)
    return caminho
