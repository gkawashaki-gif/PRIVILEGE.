from flask import Flask, request, redirect, send_file, session
import pandas as pd
from datetime import datetime
from urllib.parse import quote
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os
import uuid
import math

app = Flask(__name__)
app.secret_key = "privilege_chave_secreta_2026"

# Cada cliente terá um pedido separado
PEDIDOS_POR_SESSAO = {}

WHATSAPP_NUMERO = "5515998401570"
VALOR_METRO_LINEAR = 2.90

# Chapa padrão informada por você
CHAPA_COMPRIMENTO_MM = 2750
CHAPA_LARGURA_MM = 1850

chapas = [
    "Branco TX 6mm",
    "Branco TX 15mm",
    "Branco TX 18mm",
    "Anticua Guararapes 15mm",
    "Anticua Guararapes 18mm",
    "Carvalho Natural 15mm",
    "Carvalho Natural 18mm",
    "Palha Trema Duratex 18mm",
    "Bento Arauco 18mm"
]

fitas = [
    "Nenhuma",
    "Branco TX",
    "Anticua Guararapes",
    "Carvalho Natural",
    "Bento Arauco"
]


def obter_sessao_id():
    if "pedido_id" not in session:
        session["pedido_id"] = str(uuid.uuid4())
    return session["pedido_id"]


def obter_pedidos():
    pedido_id = obter_sessao_id()
    if pedido_id not in PEDIDOS_POR_SESSAO:
        PEDIDOS_POR_SESSAO[pedido_id] = []
    return PEDIDOS_POR_SESSAO[pedido_id]


def calcular_metro_linear_item(item):
    # perímetro da peça * quantidade
    perimetro_mm = (item["Comprimento"] + item["Largura"]) * 2
    metros = (perimetro_mm / 1000) * item["Quantidade"]
    return round(metros, 2)


def calcular_valor_item(item):
    return round(calcular_metro_linear_item(item) * VALOR_METRO_LINEAR, 2)


def calcular_area_item_m2(item):
    area_mm2 = item["Comprimento"] * item["Largura"] * item["Quantidade"]
    area_m2 = area_mm2 / 1_000_000
    return round(area_m2, 4)


def area_chapa_m2():
    return (CHAPA_COMPRIMENTO_MM * CHAPA_LARGURA_MM) / 1_000_000


def calcular_totais(pedidos):
    total_metros = 0
    total_valor = 0
    total_area_m2 = 0

    for item in pedidos:
        total_metros += calcular_metro_linear_item(item)
        total_valor += calcular_valor_item(item)
        total_area_m2 += calcular_area_item_m2(item)

    total_metros = round(total_metros, 2)
    total_valor = round(total_valor, 2)
    total_area_m2 = round(total_area_m2, 4)

    chapa_area = area_chapa_m2()
    chapas_necessarias = math.ceil(total_area_m2 / chapa_area) if total_area_m2 > 0 else 0

    return total_metros, total_valor, total_area_m2, round(chapa_area, 4), chapas_necessarias


@app.route("/")
def home():
    pedidos = obter_pedidos()

    lista = ""
    for i, p in enumerate(pedidos):
        ml = calcular_metro_linear_item(p)
        valor = calcular_valor_item(p)
        area = calcular_area_item_m2(p)

        lista += f"""
        <div style='border-bottom:1px solid #555; padding:10px 0; text-align:left;'>
            <b>{p['Material']}</b><br>
            {p['Comprimento']} x {p['Largura']} mm | Qtd: {p['Quantidade']}<br>
            Fitas: Sup={p['Fita Superior']}, Inf={p['Fita Inferior']}, Esq={p['Fita Esquerda']}, Dir={p['Fita Direita']}<br>
            Metro linear: {ml:.2f} m | Valor: R$ {valor:.2f} | Área: {area:.4f} m²
            <div style="margin-top:6px;">
                <a href='/remover/{i}' style='color:#d4af37; text-decoration:none;'>❌ Remover</a>
            </div>
        </div>
        """

    total_metros, total_valor, total_area, chapa_area, chapas_necessarias = calcular_totais(pedidos)

    op_chapas = "".join([f"<option value='{c}'>{c}</option>" for c in chapas])
    op_fitas = "".join([f"<option value='{f}'>{f}</option>" for f in fitas])

    return f"""
    <html>
    <head>
        <title>Privilege Marcenaria</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #0f2e2e;
                color: white;
                text-align: center;
                margin: 0;
                padding: 20px;
            }}
            .box {{
                background: rgba(0,0,0,0.72);
                width: 95%;
                max-width: 650px;
                margin: 0 auto;
                padding: 24px;
                border-radius: 18px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.35);
            }}
            img {{
                width: 210px;
                max-width: 70%;
                margin-bottom: 10px;
                border-radius: 12px;
            }}
            select, input {{
                width: 92%;
                padding: 12px;
                margin: 6px 0;
                border-radius: 8px;
                border: none;
                box-sizing: border-box;
            }}
            button {{
                background: #d4af37;
                color: #111;
                padding: 12px 16px;
                border: none;
                margin-top: 12px;
                cursor: pointer;
                border-radius: 8px;
                font-weight: bold;
            }}
            .secao {{
                margin-top: 18px;
                text-align: left;
            }}
            .secao h3 {{
                text-align: center;
                color: #d4af37;
                margin-bottom: 8px;
            }}
            .acoes {{
                display: flex;
                gap: 10px;
                justify-content: center;
                flex-wrap: wrap;
                margin-top: 16px;
            }}
            .resumo {{
                margin-top: 16px;
                background: rgba(255,255,255,0.06);
                padding: 14px;
                border-radius: 10px;
                text-align: left;
                line-height: 1.7;
            }}
            .obs {{
                font-size: 12px;
                color: #d7d7d7;
                text-align: center;
                margin-top: 8px;
            }}
        </style>
    </head>
    <body>
        <div class="box">
            <img src="/logo.png" alt="Privilege Marcenaria">

            <form action="/add" method="post">
                <select name="material" required>
                    <option value="">Selecione a chapa</option>
                    {op_chapas}
                </select>

                <input name="comprimento" placeholder="Comprimento (mm)" type="number" min="1" max="{CHAPA_COMPRIMENTO_MM}" required>
                <input name="largura" placeholder="Largura (mm)" type="number" min="1" max="{CHAPA_LARGURA_MM}" required>
                <input name="quantidade" placeholder="Quantidade" type="number" min="1" required>

                <div class="secao">
                    <h3>Fitas de Borda</h3>

                    Superior:
                    <select name="fita_sup">{op_fitas}</select>

                    Inferior:
                    <select name="fita_inf">{op_fitas}</select>

                    Esquerda:
                    <select name="fita_esq">{op_fitas}</select>

                    Direita:
                    <select name="fita_dir">{op_fitas}</select>
                </div>

                <div class="obs">
                    Tamanho máximo permitido da peça: {CHAPA_COMPRIMENTO_MM} mm x {CHAPA_LARGURA_MM} mm
                </div>

                <button type="submit">Adicionar Peça</button>
            </form>

            <div class="secao">
                <h3>Peças do Pedido</h3>
                {lista if lista else "<p style='text-align:center;'>Nenhuma peça adicionada ainda.</p>"}
            </div>

            <div class="resumo">
                <b>Total metro linear:</b> {total_metros:.2f} m<br>
                <b>Valor por metro linear:</b> R$ {VALOR_METRO_LINEAR:.2f}<br>
                <b>Total do pedido:</b> R$ {total_valor:.2f}<br>
                <b>Área total das peças:</b> {total_area:.4f} m²<br>
                <b>Área de uma chapa ({CHAPA_COMPRIMENTO_MM} x {CHAPA_LARGURA_MM} mm):</b> {chapa_area:.4f} m²<br>
                <b>Chapas necessárias (estimativa):</b> {chapas_necessarias}
            </div>

            <div class="acoes">
                <a href="/finalizar"><button type="button">Pedido Pronto</button></a>
                <a href="/limpar"><button type="button">Limpar Pedido</button></a>
            </div>
        </div>
    </body>
    </html>
    """


@app.route("/logo.png")
def logo():
    return send_file("logo.png")


@app.route("/add", methods=["POST"])
def add():
    pedidos = obter_pedidos()

    comp = int(request.form["comprimento"])
    larg = int(request.form["largura"])
    qtd = int(request.form["quantidade"])

    if comp > CHAPA_COMPRIMENTO_MM or larg > CHAPA_LARGURA_MM:
        return f"""
        <html>
        <body style="font-family:Arial; background:#0f2e2e; color:white; text-align:center; padding:40px;">
            <div style="background:rgba(0,0,0,0.72); max-width:520px; margin:auto; padding:24px; border-radius:18px;">
                <h2 style="color:#ff6b6b;">Medida inválida</h2>
                <p>O tamanho máximo permitido é:</p>
                <p><b>{CHAPA_COMPRIMENTO_MM} mm x {CHAPA_LARGURA_MM} mm</b></p>
                <a href="/" style="display:inline-block; margin-top:15px; background:#d4af37; color:#111; padding:12px 18px; border-radius:8px; text-decoration:none; font-weight:bold;">Voltar</a>
            </div>
        </body>
        </html>
        """

    pedidos.append({
        "Material": request.form["material"],
        "Comprimento": comp,
        "Largura": larg,
        "Quantidade": qtd,
        "Fita Superior": request.form["fita_sup"],
        "Fita Inferior": request.form["fita_inf"],
        "Fita Esquerda": request.form["fita_esq"],
        "Fita Direita": request.form["fita_dir"]
    })

    return redirect("/")


@app.route("/remover/<int:id>")
def remover(id):
    pedidos = obter_pedidos()
    if 0 <= id < len(pedidos):
        pedidos.pop(id)
    return redirect("/")


@app.route("/limpar")
def limpar():
    pedido_id = obter_sessao_id()
    PEDIDOS_POR_SESSAO[pedido_id] = []
    return redirect("/")


@app.route("/excel")
def excel():
    pedidos = obter_pedidos()
    if not pedidos:
        return "Nenhum pedido para exportar."

    dados = []
    for item in pedidos:
        ml = calcular_metro_linear_item(item)
        valor = calcular_valor_item(item)
        area = calcular_area_item_m2(item)

        linha = item.copy()
        linha["Metro Linear (m)"] = ml
        linha["Valor (R$)"] = valor
        linha["Área (m²)"] = area
        dados.append(linha)

    total_metros, total_valor, total_area, chapa_area, chapas_necessarias = calcular_totais(pedidos)

    resumo = pd.DataFrame([{
        "Total Metro Linear (m)": total_metros,
        "Valor por Metro Linear (R$)": VALOR_METRO_LINEAR,
        "Total Pedido (R$)": total_valor,
        "Área Total (m²)": total_area,
        "Área Chapa (m²)": chapa_area,
        "Chapas Necessárias (estimativa)": chapas_necessarias
    }])

    arquivo = BytesIO()
    with pd.ExcelWriter(arquivo, engine="openpyxl") as writer:
        pd.DataFrame(dados).to_excel(writer, index=False, sheet_name="Pedido")
        resumo.to_excel(writer, index=False, sheet_name="Resumo")
    arquivo.seek(0)

    nome = f"pedido_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(
        arquivo,
        as_attachment=True,
        download_name=nome,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.route("/pdf")
def pdf():
    pedidos = obter_pedidos()
    if not pedidos:
        return "Nenhum pedido para exportar."

    total_metros, total_valor, total_area, chapa_area, chapas_necessarias = calcular_totais(pedidos)

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    largura, altura = A4

    y = altura - 50
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(40, y, "Privilege Marcenaria - Resumo do Pedido")
    y -= 25

    pdf.setFont("Helvetica", 10)
    pdf.drawString(40, y, f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    y -= 25

    for i, item in enumerate(pedidos, start=1):
        ml = calcular_metro_linear_item(item)
        valor = calcular_valor_item(item)
        area = calcular_area_item_m2(item)

        linhas = [
            f"{i}. {item['Material']}",
            f"   Medidas: {item['Comprimento']} x {item['Largura']} mm | Qtd: {item['Quantidade']}",
            f"   Fitas: Sup={item['Fita Superior']} | Inf={item['Fita Inferior']} | Esq={item['Fita Esquerda']} | Dir={item['Fita Direita']}",
            f"   Metro linear: {ml:.2f} m | Valor: R$ {valor:.2f} | Área: {area:.4f} m²"
        ]

        for linha in linhas:
            if y < 80:
                pdf.showPage()
                y = altura - 50
                pdf.setFont("Helvetica", 10)
            pdf.drawString(40, y, linha)
            y -= 15

        y -= 8

    if y < 130:
        pdf.showPage()
        y = altura - 50

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(40, y, "Resumo Geral")
    y -= 18

    pdf.setFont("Helvetica", 10)
    pdf.drawString(40, y, f"Total metro linear: {total_metros:.2f} m")
    y -= 15
    pdf.drawString(40, y, f"Valor por metro linear: R$ {VALOR_METRO_LINEAR:.2f}")
    y -= 15
    pdf.drawString(40, y, f"Total do pedido: R$ {total_valor:.2f}")
    y -= 15
    pdf.drawString(40, y, f"Área total das peças: {total_area:.4f} m²")
    y -= 15
    pdf.drawString(40, y, f"Área da chapa ({CHAPA_COMPRIMENTO_MM} x {CHAPA_LARGURA_MM} mm): {chapa_area:.4f} m²")
    y -= 15
    pdf.drawString(40, y, f"Chapas necessárias (estimativa por área): {chapas_necessarias}")
    y -= 25
    pdf.drawString(40, y, "Observação: a quantidade de chapas é estimada por área.")
    y -= 15
    pdf.drawString(40, y, "O número exato pode variar conforme o plano de corte no MaxCut.")

    pdf.save()
    buffer.seek(0)

    nome = f"pedido_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return send_file(
        buffer,
        as_attachment=True,
        download_name=nome,
        mimetype="application/pdf"
    )


@app.route("/finalizar")
def finalizar():
    pedidos = obter_pedidos()
    if not pedidos:
        return "Nenhum pedido."

    total_metros, total_valor, total_area, chapa_area, chapas_necessarias = calcular_totais(pedidos)

    linhas = [
        "Pedido Privilege:",
        ""
    ]

    for i, p in enumerate(pedidos, start=1):
        linhas.append(
            f"{i}. {p['Material']} | {p['Comprimento']} x {p['Largura']} mm | "
            f"Qtd: {p['Quantidade']} | "
            f"Fitas: Sup={p['Fita Superior']}, Inf={p['Fita Inferior']}, "
            f"Esq={p['Fita Esquerda']}, Dir={p['Fita Direita']}"
        )

    linhas += [
        "",
        f"Total metro linear: {total_metros:.2f} m",
        f"Total do pedido: R$ {total_valor:.2f}",
        f"Área total das peças: {total_area:.4f} m²",
        f"Chapas necessárias (estimativa): {chapas_necessarias}"
    ]

    texto = quote("\n".join(linhas))
    link = f"https://wa.me/{WHATSAPP_NUMERO}?text={texto}"

    return f"""
    <html>
    <head>
        <title>Pedido pronto</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #0f2e2e;
                color: white;
                text-align: center;
                padding: 30px;
            }}
            .box {{
                background: rgba(0,0,0,0.72);
                max-width: 580px;
                margin: 0 auto;
                padding: 24px;
                border-radius: 18px;
            }}
            a.button {{
                display: inline-block;
                margin: 10px;
                padding: 12px 18px;
                border-radius: 8px;
                background: #d4af37;
                color: #111;
                text-decoration: none;
                font-weight: bold;
            }}
            p {{
                line-height: 1.5;
            }}
        </style>
    </head>
    <body>
        <div class="box">
            <h2>Pedido pronto</h2>
            <p>Baixe os arquivos do pedido e depois abra o WhatsApp.</p>
            <p>No WhatsApp, anexe o Excel ou o PDF manualmente.</p>

            <a class="button" href="/excel">Baixar Excel</a>
            <a class="button" href="/pdf">Baixar PDF</a>
            <a class="button" href="{link}" target="_blank">Abrir WhatsApp</a>
            <br>
            <a class="button" href="/">Voltar</a>
        </div>
    </body>
    </html>
    """


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)