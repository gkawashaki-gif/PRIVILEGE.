from flask import Flask, request, redirect, send_file
import pandas as pd
from datetime import datetime
from urllib.parse import quote
import os

app = Flask(__name__)

pedidos = []

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

WHATSAPP_NUMERO = "5515998401570"


@app.route('/')
def home():
    lista = ""
    for i, p in enumerate(pedidos):
        lista += f"""
        <div style='border-bottom:1px solid #555; padding:8px; display:flex; justify-content:space-between;'>
            <span>{p['Material']} - {p['Comprimento']} x {p['Largura']} mm (Qtd: {p['Quantidade']})</span>
            <a href='/remover/{i}'>❌</a>
        </div>
        """

    op_chapas = "".join([f"<option value='{c}'>{c}</option>" for c in chapas])
    op_fitas = "".join([f"<option value='{f}'>{f}</option>" for f in fitas])

    return f'''
    <html>
    <head>
        <title>Privilege Marcenaria</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: Arial;
                background: #0f2e2e;
                color: white;
                text-align: center;
                padding: 20px;
            }}
            .box {{
                background: rgba(0,0,0,0.7);
                max-width: 500px;
                margin: auto;
                padding: 20px;
                border-radius: 15px;
            }}
            img {{
                width: 200px;
            }}
            input, select {{
                width: 90%;
                padding: 10px;
                margin: 5px;
            }}
            button {{
                background: #d4af37;
                padding: 10px;
                border: none;
                cursor: pointer;
                margin-top: 10px;
            }}
        </style>
    </head>

    <body>
    <div class="box">

    <img src="/logo.png">

    <form action="/add" method="post">
        <select name="material" required>
            <option value="">Selecione a chapa</option>
            {op_chapas}
        </select>

        <input name="comprimento" type="number" max="2730" placeholder="Comprimento (mm)" required>
        <input name="largura" type="number" max="1830" placeholder="Largura (mm)" required>
        <input name="quantidade" type="number" placeholder="Quantidade" required>

        <h3>Fitas</h3>

        Superior:
        <select name="fita_sup">{op_fitas}</select>

        Inferior:
        <select name="fita_inf">{op_fitas}</select>

        Esquerda:
        <select name="fita_esq">{op_fitas}</select>

        Direita:
        <select name="fita_dir">{op_fitas}</select>

        <button type="submit">Adicionar</button>
    </form>

    <h3>Peças</h3>
    {lista}

    <a href="/excel"><button>Gerar Excel</button></a>
    <a href="/preparar"><button>Enviar WhatsApp</button></a>

    </div>
    </body>
    </html>
    '''


@app.route('/logo.png')
def logo():
    return send_file("logo.png")


@app.route('/add', methods=['POST'])
def add():
    comp = int(request.form['comprimento'])
    larg = int(request.form['largura'])

    if comp > 2730 or larg > 1830:
        return "Erro: máximo 2730 x 1830 mm"

    pedidos.append({
        "Material": request.form['material'],
        "Comprimento": comp,
        "Largura": larg,
        "Quantidade": request.form['quantidade'],
        "Fita Superior": request.form['fita_sup'],
        "Fita Inferior": request.form['fita_inf'],
        "Fita Esquerda": request.form['fita_esq'],
        "Fita Direita": request.form['fita_dir']
    })

    return redirect('/')


@app.route('/remover/<int:id>')
def remover(id):
    if id < len(pedidos):
        pedidos.pop(id)
    return redirect('/')


@app.route('/excel')
def excel():
    df = pd.DataFrame(pedidos)
    nome = f"pedido_{datetime.now().strftime('%H%M%S')}.xlsx"
    df.to_excel(nome, index=False)
    return send_file(nome, as_attachment=True)


@app.route('/preparar')
def preparar():
    texto = "Pedido Privilege:%0A"

    for p in pedidos:
        texto += f"{p['Material']} - {p['Comprimento']}x{p['Largura']} ({p['Quantidade']})%0A"

    link = f"https://wa.me/{WHATSAPP_NUMERO}?text={texto}"

    return redirect(link)


# 🔥 ESSA PARTE É O SEGREDO DO RENDER
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)