from flask import Flask, request, jsonify
from flasgger import Swagger
from flask_cors import CORS
import sqlite3
import os
import requests
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Usa arquivo swagger.yaml como template principal da documentação
swagger = Swagger(app, template_file="swagger.yaml")


# --- FUNÇÕES DE BANCO DE DADOS ---
def get_db_conn():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_conn()
    cursor = conn.cursor()

    # ATENÇÃO: em desenvolvimento, apagamos as tabelas para recriar
    cursor.execute("DROP TABLE IF EXISTS usuarios")
    cursor.execute("DROP TABLE IF EXISTS desafios")
    cursor.execute("DROP TABLE IF EXISTS progresso_usuarios")
    cursor.execute("DROP TABLE IF EXISTS explicacoes")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            idade INTEGER
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS desafios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            linguagem TEXT NOT NULL,
            instrucao TEXT NOT NULL,
            codigo_bugado TEXT NOT NULL,
            codigo_esperado TEXT NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS progresso_usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            desafio_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pendente',
            data_conclusao DATETIME,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
            FOREIGN KEY (desafio_id) REFERENCES desafios (id)
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS explicacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            titulo TEXT NOT NULL,
            texto TEXT NOT NULL,
            codigo TEXT
        );
    """)

    # Desafios iniciais
    if cursor.execute("SELECT COUNT(*) FROM desafios").fetchone()[0] == 0:
        desafios_iniciais = [
            (
                'O Título Sumiu!',
                'html',
                'Para um título grandão, usamos a tag &lt;h1&gt;. Toda tag que é aberta precisa ser fechada com uma barra, assim: &lt;/h1&gt;. <br><br> DESAFIO <br> Nosso mascote queria escrever um título grande com a frase "Olá, Mundo!", o código dele foi: <br><br> &lt;titul0&gt;Olá, Mundo!&lt;/titul0&gt;  <br><br> O código do nosso mascote não está aparecendo, você consegue nos ajudar?',
                '<titul0>Olá, Mundo!</titul0>',
                '<h1>Olá, Mundo!</h1>'
            ),
            (
                'Parágrafo Tímido',
                'html',
                'A tag de parágrafo é a &lt;p&gt; e também precisa ser aberta e fechada para funcionar! <br><br> DESAFIO <br> O parágrafo do nosso mascote não foi fechado e ficou assim: <br><br> &lt;p&gt;Meu animal favorito é o golfinho!. <br><br> Você consegue nos ajudar?',
                '<p>Meu animal favorito é o golfinho!',
                '<p>Meu animal favorito é o golfinho!</p>'
            ),
            (
                'O Site não Pinta!',
                'css',
                'Para mudar a cor de fundo, a ordem que devemos dar ao computador é "background-color".<br> Se usarmos só "color", ele pinta o texto!<br><br> DESAFIO <br> O código do nosso mascote foi:<br><br>body { color: lightblue; } <br><br> O resultado desse codigo foi texto ficar azul. <br> Você consegue nos ajudar de novo e escrever um código que pinte apenas o fundo (background) de azul?',
                'body { color: lightblue; }',
                'body { background-color: lightblue; }'
            )
        ]
        cursor.executemany(
            'INSERT INTO desafios (nome, linguagem, instrucao, codigo_bugado, codigo_esperado) VALUES (?, ?, ?, ?, ?)',
            desafios_iniciais
        )

    # Explicações iniciais
    if cursor.execute("SELECT COUNT(*) FROM explicacoes").fetchone()[0] == 0:
        explicacoes_iniciais = [
            (
                'intro',
                "Ei, você, você mesmo!!",
                "Vamos aprender um pouco de Engenharia de Software?\nJuro que é muito mais simples do que parece!\n\nTeremos 5 conceitos para começar...",
                None
            ),
            (
                'conceito',
                "1. O que é um site?",
                "Um site é como uma casinha que vive dentro do computador! Quando você entra em um site, é como visitar essa casa. Ela pode ter portas (links), quadros na parede (imagens), recados colados na geladeira (textos) e até botões que fazem coisas acontecerem (tipo uma campainha que toca)!",
                None
            ),
            (
                'conceito',
                "2. O que é HTML? (a estrutura)",
                "O HTML é como o esqueleto da casa. Ele diz onde vai o título, a imagem, o botão, a lista… É tipo montar uma lancheira com divisórias: um espaço pro sanduíche, outro pro suco, outro pra sobremesa.",
                '<h1>Olá, mundo!</h1>\n<p>Este é o meu primeiro site!</p>'
            ),
            (
                'conceito',
                "3. O que é CSS? (o visual)",
                "CSS é o que deixa o site bonito! Ele pinta as paredes, escolhe a fonte do texto, muda o tamanho das coisas e até coloca brilhos e animações. É como colocar roupas e maquiagem no seu personagem!",
                'p {\n  color: blue;\n  font-size: 20px;\n}'
            ),
            (
                'conceito',
                "4. O que é JavaScript? (o cérebro)",
                "O JavaScript é o que dá vida ao site! Ele faz as coisas se mexerem, responderem quando você clica, mudarem sozinhas. É como o cérebro de um robô que reage quando você fala com ele.",
                'alert("Bem-vindo ao meu site!");'
            ),
            (
                'conceito',
                "5. O que é um Bug?",
                "Um bug é quando o código não funciona direitinho. Pode ser porque esquecemos um pedacinho, escrevemos uma palavrinha errada, ou colocamos tudo na ordem errada. É como montar um LEGO e perceber que a roda está do lado errado.",
                None
            )
        ]
        cursor.executemany(
            'INSERT INTO explicacoes (tipo, titulo, texto, codigo) VALUES (?, ?, ?, ?)',
            explicacoes_iniciais
        )

    # Usuário de teste
    if cursor.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
        cursor.execute(
            'INSERT INTO usuarios (nome, idade) VALUES (?, ?)',
            ('Aluno Teste', 8)
        )

    conn.commit()
    conn.close()


# --- ROTA PARA CADASTRAR UM NOVO USUÁRIO ---
@app.route('/cadastrar_usuario', methods=['POST'])
def cadastrar_usuario():
    """
    Cadastrar novo usuário
    ---
    tags:
      - Usuários
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        description: Dados do novo usuário
        schema:
          type: object
          required:
            - nome
            - idade
          properties:
            nome:
              type: string
              example: Maria
            idade:
              type: integer
              example: 10
    responses:
      201:
        description: Usuário cadastrado com sucesso
        schema:
          type: object
          properties:
            mensagem:
              type: string
              example: "Usuário 'Maria' cadastrado com sucesso!"
            usuario_id:
              type: integer
              example: 1
      400:
        description: Erro de validação ou payload inválido
    """
    dados = request.get_json()
    nome = dados['nome']
    idade = dados['idade']

    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO usuarios (nome, idade) VALUES (?, ?)', (nome, idade))
    novo_usuario_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        "mensagem": f"Usuário '{nome}' cadastrado com sucesso!",
        "usuario_id": novo_usuario_id
    }), 201


# --- ROTA PARA ATUALIZAR DADOS DE UM USUÁRIO (PUT) ---
@app.route('/usuarios/<int:usuario_id>', methods=['PUT'])
def atualizar_usuario(usuario_id):
    """
    Atualizar usuário
    ---
    tags:
      - Usuários
    consumes:
      - application/json
    parameters:
      - in: path
        name: usuario_id
        type: integer
        required: true
        description: ID do usuário a ser atualizado
      - in: body
        name: body
        required: true
        description: Novos dados do usuário (nome e/ou idade)
        schema:
          type: object
          properties:
            nome:
              type: string
              example: Novo Nome
            idade:
              type: integer
              example: 11
    responses:
      200:
        description: Usuário atualizado com sucesso
        schema:
          type: object
          properties:
            mensagem:
              type: string
            usuario_id:
              type: integer
            nome:
              type: string
            idade:
              type: integer
      400:
        description: Nenhum dado enviado para atualização
      404:
        description: Usuário não encontrado
    """
    dados = request.get_json() or {}

    novo_nome = dados.get("nome")
    nova_idade = dados.get("idade")

    if novo_nome is None and nova_idade is None:
        return jsonify({"erro": "Nada para atualizar. Envie nome e/ou idade."}), 400

    conn = get_db_conn()
    cursor = conn.cursor()

    usuario = cursor.execute(
        "SELECT * FROM usuarios WHERE id = ?",
        (usuario_id,)
    ).fetchone()

    if not usuario:
        conn.close()
        return jsonify({"erro": "Usuário não encontrado."}), 404

    nome_final = novo_nome if novo_nome is not None else usuario["nome"]
    idade_final = nova_idade if nova_idade is not None else usuario["idade"]

    cursor.execute(
        "UPDATE usuarios SET nome = ?, idade = ? WHERE id = ?",
        (nome_final, idade_final, usuario_id)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "mensagem": "Usuário atualizado com sucesso.",
        "usuario_id": usuario_id,
        "nome": nome_final,
        "idade": idade_final
    }), 200


# --- ROTA PARA DELETAR UM USUÁRIO (DELETE) ---
@app.route('/usuarios/<int:usuario_id>', methods=['DELETE'])
def deletar_usuario(usuario_id):
    """
    Deletar usuário
    ---
    tags:
      - Usuários
    parameters:
      - in: path
        name: usuario_id
        type: integer
        required: true
        description: ID do usuário a ser removido
    responses:
      200:
        description: Usuário removido com sucesso
        schema:
          type: object
          properties:
            mensagem:
              type: string
              example: "Usuário 1 removido com sucesso."
      404:
        description: Usuário não encontrado
    """
    conn = get_db_conn()
    cursor = conn.cursor()

    usuario = cursor.execute(
        "SELECT * FROM usuarios WHERE id = ?",
        (usuario_id,)
    ).fetchone()

    if not usuario:
        conn.close()
        return jsonify({"erro": "Usuário não encontrado."}), 404

    cursor.execute(
        "DELETE FROM progresso_usuarios WHERE usuario_id = ?",
        (usuario_id,)
    )

    cursor.execute(
        "DELETE FROM usuarios WHERE id = ?",
        (usuario_id,)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "mensagem": f"Usuário {usuario_id} removido com sucesso."
    }), 200


# --- ROTAS DE PROGRESSO/DESAFIOS ---
@app.route('/progresso/<int:usuario_id>', methods=['GET'])
def buscar_progresso(usuario_id):
    """
    Listar desafios e status de um usuário
    ---
    tags:
      - Progresso
    parameters:
      - in: path
        name: usuario_id
        type: integer
        required: true
        description: ID do usuário
    responses:
      200:
        description: Lista de desafios com status para o usuário
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              nome:
                type: string
              linguagem:
                type: string
              instrucao:
                type: string
              status:
                type: string
                example: pendente
              codigo_bugado:
                type: string
              codigo_esperado:
                type: string
    """
    conn = get_db_conn()
    query = """
        SELECT
            d.id,
            d.nome,
            d.linguagem,
            d.instrucao,
            COALESCE(p.status, 'pendente') as status,
            d.codigo_bugado,
            d.codigo_esperado
        FROM desafios d
        LEFT JOIN progresso_usuarios p
            ON d.id = p.desafio_id AND p.usuario_id = ?
    """
    progresso = conn.execute(query, (usuario_id,)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in progresso])


@app.route('/progresso', methods=['POST'])
def submeter_progresso():
    """
    Submeter código de um desafio
    ---
    tags:
      - Progresso
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        description: Dados da submissão de desafio
        schema:
          type: object
          required:
            - usuario_id
            - desafio_id
            - codigo_submetido
          properties:
            usuario_id:
              type: integer
              example: 1
            desafio_id:
              type: integer
              example: 2
            codigo_submetido:
              type: string
              example: "<h1>Olá, Mundo!</h1>"
    responses:
      200:
        description: Resultado da verificação do código
        schema:
          type: object
          properties:
            status:
              type: string
              example: concluido
            mensagem:
              type: string
              example: Parabéns! Resposta correta!
            correto:
              type: boolean
      400:
        description: Dados incompletos ou inválidos
      404:
        description: Usuário ou desafio não encontrado
      500:
        description: Erro interno ao processar a submissão
    """
    try:
        dados = request.get_json()
        usuario_id = dados.get('usuario_id')
        desafio_id = dados.get('desafio_id')
        codigo_submetido = dados.get('codigo_submetido')

        if not all([usuario_id, desafio_id, codigo_submetido is not None]):
            return jsonify({"erro": "Dados incompletos"}), 400

        conn = get_db_conn()
        cursor = conn.cursor()

        usuario = cursor.execute(
            'SELECT * FROM usuarios WHERE id = ?',
            (usuario_id,)
        ).fetchone()
        if not usuario:
            conn.close()
            return jsonify({"erro": "Usuário não encontrado"}), 404

        desafio = cursor.execute(
            'SELECT * FROM desafios WHERE id = ?',
            (desafio_id,)
        ).fetchone()
        if not desafio:
            conn.close()
            return jsonify({"erro": "Desafio não encontrado"}), 404

        codigo_esperado = desafio['codigo_esperado']
        correto = codigo_submetido.strip() == codigo_esperado.strip()
        status = "concluido" if correto else "pendente"

        progresso_existente = cursor.execute(
            'SELECT id FROM progresso_usuarios WHERE usuario_id = ? AND desafio_id = ?',
            (usuario_id, desafio_id)
        ).fetchone()

        agora = datetime.now() if correto else None

        if progresso_existente:
            cursor.execute(
                'UPDATE progresso_usuarios SET status = ?, data_conclusao = ? WHERE id = ?',
                (status, agora, progresso_existente['id'])
            )
        else:
            cursor.execute(
                'INSERT INTO progresso_usuarios (usuario_id, desafio_id, status, data_conclusao) VALUES (?, ?, ?, ?)',
                (usuario_id, desafio_id, status, agora)
            )

        conn.commit()
        conn.close()

        return jsonify({
            "status": status,
            "mensagem": "Parabéns! Resposta correta!" if correto else "Código incorreto. Tente novamente!",
            "correto": correto
        })

    except Exception as e:
        print(f"Ocorreu un erro na rota /progresso: {e}")
        return jsonify({"erro": str(e)}), 500


# --- ROTA PARA BUSCAR EXPLICAÇÕES ---
@app.route('/explicacoes', methods=['GET'])
def get_explicacoes():
    """
    Listar explicações iniciais
    ---
    tags:
      - Conteúdo
    responses:
      200:
        description: Lista de explicações exibidas na tela de introdução
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              tipo:
                type: string
                example: conceito
              titulo:
                type: string
              texto:
                type: string
              codigo:
                type: string
                nullable: true
    """
    conn = get_db_conn()
    explicacoes = conn.execute(
        'SELECT id, tipo, titulo, texto, codigo FROM explicacoes ORDER BY id'
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in explicacoes])


# --- ROTA DO ROBOTECA (GROQ) ---
@app.route("/ajuda-bot", methods=["POST"])
def ajuda_bot():
    """
    Enviar dúvida para a RoboTeca (Groq API)
    ---
    tags:
      - RoboTeca
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        description: Dúvida da criança e contexto do desafio/explicação
        schema:
          type: object
          required:
            - duvida
          properties:
            usuario_id:
              type: integer
              example: 1
            contexto:
              type: string
              example: "Explicação sobre HTML e tags de título."
            duvida:
              type: string
              example: "Não entendi por que h1 é diferente de p."
    responses:
      200:
        description: Resposta simplificada gerada pela RoboTeca
        schema:
          type: object
          properties:
            resposta_simplificada:
              type: string
      400:
        description: Nenhuma dúvida enviada no corpo da requisição
      500:
        description: Erro ao falar com a Groq API ou chave não configurada
    """
    dados = request.get_json()

    usuario_id = dados.get("usuario_id")
    contexto = dados.get("contexto", "")
    duvida = dados.get("duvida", "")

    if not duvida:
        return jsonify({"erro": "Nenhuma dúvida enviada"}), 400

    mensagem = (
        "Você é um robô tutor que ensina programação para crianças de 9 a 12 anos. "
        "Use uma linguagem neutra quanto ao gênero, chame-os de crianças ou estudantes. "
        "Use pronomes neutros com (a) ou (as)"
        "Explique SEM termos técnicos complicados, usando exemplos simples, analogias "
        "e linguagem divertida. Não use palavrões nem conteúdo sensível.\n\n"
        f"Contexto da explicação ou desafio: {contexto}\n\n"
        f"Dúvida da criança: {duvida}\n\n"
        "Resposta:"
    )

    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    if not GROQ_API_KEY:
        return jsonify({"erro": "API Key da Groq não configurada."}), 500

    url = "https://api.groq.com/openai/v1/chat/completions"

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "user", "content": mensagem}
        ],
        "temperature": 0.4
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        resposta = requests.post(url, json=payload, headers=headers, timeout=20)

        if resposta.status_code != 200:
            print("Groq status code:", resposta.status_code)
            print("Groq response body:", resposta.text)
            resposta.raise_for_status()

        data = resposta.json()

        texto_resposta = data["choices"][0]["message"]["content"]

        return jsonify({
            "resposta_simplificada": texto_resposta
        })

    except Exception as e:
        print("Erro com a API da Groq:", e)
        return jsonify({
            "erro": "Não foi possível falar com o robô agora, tente novamente mais tarde."
        }), 500


# --- ROTA DE STATUS BÁSICA ---
@app.route("/", methods=["GET"])
def status_api():
    """
    Status da API
    ---
    tags:
      - Status
    responses:
      200:
        description: API do CodeBrincando está no ar
        schema:
          type: object
          properties:
            mensagem:
              type: string
              example: API do CodeBrincando está no ar 🚀
            status:
              type: string
              example: ok
    """
    return jsonify({
        "mensagem": "API do CodeBrincando está no ar 🚀",
        "status": "ok"
    }), 200

if __name__ == "__main__":
    init_db() 
    app.run(host="0.0.0.0", port=5001)

