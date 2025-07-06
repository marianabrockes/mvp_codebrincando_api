import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify
from flasgger import Swagger
from flask_cors import CORS # LINHA IMPORTANTE

app = Flask(__name__)
CORS(app) # LINHA IMPORTANTE
swagger = Swagger(app)

# --- FUNÇÕES DE BANCO DE DADOS ---
def get_db_conn():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_conn()
    cursor = conn.cursor()
    
    # Apaga as tabelas antigas para garantir que a nova estrutura seja criada
    # (ATENÇÃO: Isso deletará os dados existentes. Como estamos em desenvolvimento, não há problema)
    cursor.execute("DROP TABLE IF EXISTS usuarios")
    cursor.execute("DROP TABLE IF EXISTS desafios")
    cursor.execute("DROP TABLE IF EXISTS progresso_usuarios")
    cursor.execute("DROP TABLE IF EXISTS explicacoes")

    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, idade INTEGER);''')
    
    # MUDANÇA AQUI: Adicionamos a coluna 'codigo_bugado'
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS desafios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            linguagem TEXT NOT NULL,
            instrucao TEXT NOT NULL,
            codigo_bugado TEXT NOT NULL, -- Nova coluna!
            codigo_esperado TEXT NOT NULL
        );
    ''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS progresso_usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER NOT NULL, desafio_id INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'pendente', data_conclusao DATETIME, FOREIGN KEY (usuario_id) REFERENCES usuarios (id), FOREIGN KEY (desafio_id) REFERENCES desafios (id));''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS explicacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            titulo TEXT NOT NULL,
            texto TEXT NOT NULL,
            codigo TEXT
        );
    ''')

    # MUDANÇA AQUI: Adicionamos o código bugado aos desafios iniciais
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
        cursor.executemany('INSERT INTO desafios (nome, linguagem, instrucao, codigo_bugado, codigo_esperado) VALUES (?, ?, ?, ?, ?)', desafios_iniciais)
    
    if cursor.execute("SELECT COUNT(*) FROM explicacoes").fetchone()[0] == 0:
        explicacoes_iniciais = [
            ('intro', "Ei, você, você mesmo!!", "Vamos aprender um pouco de Engenharia de Software?\nJuro que é muito mais simples do que parece!\n\nTeremos 5 conceitos para começar...", None),
            ('conceito', "1. O que é um site?", "Um site é como uma casinha que vive dentro do computador! Quando você entra em um site, é como visitar essa casa. Ela pode ter portas (links), quadros na parede (imagens), recados colados na geladeira (textos) e até botões que fazem coisas acontecerem (tipo uma campainha que toca)!", None),
            ('conceito', "2. O que é HTML? (a estrutura)", "O HTML é como o esqueleto da casa. Ele diz onde vai o título, a imagem, o botão, a lista… É tipo montar uma lancheira com divisórias: um espaço pro sanduíche, outro pro suco, outro pra sobremesa.", '<h1>Olá, mundo!</h1>\n<p>Este é o meu primeiro site!</p>'),
            ('conceito', "3. O que é CSS? (o visual)", "CSS é o que deixa o site bonito! Ele pinta as paredes, escolhe a fonte do texto, muda o tamanho das coisas e até coloca brilhos e animações. É como colocar roupas e maquiagem no seu personagem!", 'p {\n  color: blue;\n  font-size: 20px;\n}'),
            ('conceito', "4. O que é JavaScript? (o cérebro)", "O JavaScript é o que dá vida ao site! Ele faz as coisas se mexerem, responderem quando você clica, mudarem sozinhas. É como o cérebro de um robô que reage quando você fala com ele.", 'alert("Bem-vindo ao meu site!");'),
            ('conceito', "5. O que é um Bug?", "Um bug é quando o código não funciona direitinho. Pode ser porque esquecemos um pedacinho, escrevemos uma palavrinha errada, ou colocamos tudo na ordem errada. É como montar um LEGO e perceber que a roda está do lado errado.", None)
        ]
        cursor.executemany('INSERT INTO explicacoes (tipo, titulo, texto, codigo) VALUES (?, ?, ?, ?)', explicacoes_iniciais)

    if cursor.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
        cursor.execute('INSERT INTO usuarios (nome, idade) VALUES (?, ?)', ('Aluno Teste', 8))
    
    conn.commit()
    conn.close()

# --- ROTA PARA CADASTRAR UM NOVO USUÁRIO (MÉTODO POST) ---
@app.route('/cadastrar_usuario', methods=['POST'])
def cadastrar_usuario():
    """
    Cadastra um novo usuário no sistema.
    ---
    tags:
      - Usuários
    summary: Cria um novo usuário.
    description: Adiciona um novo usuário ao banco de dados com base nos dados fornecidos no corpo da requisição.
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - nome
            - idade
          properties:
            nome:
              type: string
              description: O nome do novo usuário.
              example: "Joãozinho Coder"
            idade:
              type: integer
              description: A idade do novo usuário.
              example: 9
    responses:
      201:
        description: Usuário cadastrado com sucesso.
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

# --- ROTAS DE PROGRESSO/DESAFIOS ---
@app.route('/progresso/<int:usuario_id>', methods=['GET'])
def buscar_progresso(usuario_id):
    """
    Busca o progresso de um usuário em todos os desafios.
    ---
    tags: [Progresso]
    summary: Retorna a lista de desafios com o status para um usuário.
    parameters:
      - name: usuario_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Uma lista de desafios com o status de progresso.
      404:
        description: Usuário não encontrado.
    """
    conn = get_db_conn()
    query = "SELECT d.id, d.nome, d.linguagem, d.instrucao, COALESCE(p.status, 'pendente') as status, d.codigo_esperado FROM desafios d LEFT JOIN progresso_usuarios p ON d.id = p.desafio_id AND p.usuario_id = ?"
    progresso = conn.execute(query, (usuario_id,)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in progresso])

@app.route('/progresso', methods=['POST'])
def submeter_progresso():
    """
    Submete a resposta de um desafio para verificação.
    ---
    tags:
      - Progresso
    summary: Verifica a resposta de um desafio submetida por um usuário.
    parameters:
      - name: body
        in: body
        required: true
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
              example: 1
            codigo_submetido:
              type: string
              example: "<h1>Olá, Mundo!</h1>"
    responses:
      200:
        description: Resposta processada.
      400:
        description: Dados incompletos.
      404:
        description: Usuário ou desafio não encontrado.
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

        usuario = cursor.execute('SELECT * FROM usuarios WHERE id = ?', (usuario_id,)).fetchone()
        if not usuario:
            conn.close()
            return jsonify({"erro": "Usuário não encontrado"}), 404

        desafio = cursor.execute('SELECT * FROM desafios WHERE id = ?', (desafio_id,)).fetchone()
        if not desafio:
            conn.close()
            return jsonify({"erro": "Desafio não encontrado"}), 404

        codigo_esperado = desafio['codigo_esperado']
        correto = codigo_submetido.strip() == codigo_esperado.strip()
        status = "concluido" if correto else "pendente"
        
        # --- LÓGICA CORRIGIDA PARA ATUALIZAR O BANCO DE DADOS ---
        # Esta forma é mais compatível que a anterior.

        # 1. Verifica se já existe um progresso para este usuário e desafio
        progresso_existente = cursor.execute(
            'SELECT id FROM progresso_usuarios WHERE usuario_id = ? AND desafio_id = ?',
            (usuario_id, desafio_id)
        ).fetchone()

        agora = datetime.now() if correto else None

        if progresso_existente:
            # 2. Se existe, atualiza o registro (UPDATE)
            cursor.execute(
                'UPDATE progresso_usuarios SET status = ?, data_conclusao = ? WHERE id = ?',
                (status, agora, progresso_existente['id'])
            )
        else:
            # 3. Se não existe, insere um novo registro (INSERT)
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
        # Imprime o erro no terminal do backend para facilitar a depuração
        print(f"Ocorreu um erro na rota /progresso: {e}")
        return jsonify({"erro": str(e)}), 500

# --- ROTA PARA BUSCAR EXPLICAÇÕES ---
@app.route('/explicacoes', methods=['GET'])
def get_explicacoes():
    """
    Busca todas as explicações do banco de dados.
    ---
    tags:
      - Explicações
    summary: Retorna a lista de todas as explicações.
    responses:
      200:
        description: Uma lista de explicações.
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              tipo:
                type: string
              titulo:
                type: string
              texto:
                type: string
              codigo:
                type: string
    """
    conn = get_db_conn()
    explicacoes = conn.execute('SELECT id, tipo, titulo, texto, codigo FROM explicacoes ORDER BY id').fetchall()
    conn.close()
    return jsonify([dict(row) for row in explicacoes])

if __name__ == '__main__':
    init_db()
    app.run(debug=True)