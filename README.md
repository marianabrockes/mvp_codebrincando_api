# API do Projeto CodeBrincando

## Descrição do Projeto

Esta é a API RESTful para o projeto **CodeBrincando**, uma plataforma lúdica e interativa para ensinar conceitos básicos de programação (HTML, CSS, JavaScript) para crianças. A API é responsável por gerenciar usuários (alunos), desafios de programação e o progresso de cada aluno.

Este projeto foi desenvolvido como parte de um MVP e utiliza Python, Flask e SQLite.

---

## Instruções de Instalação e Execução

Siga os passos abaixo para configurar e executar o ambiente de desenvolvimento local.

### Pré-requisitos

- Python 3.8 ou superior (`python3`)
- `pip` (gerenciador de pacotes do Python)

### 1. Clonar o Repositório

(Quando você tiver o repositório no GitHub, colocará o comando aqui. Por enquanto, pode pular esta parte.)

### 2. Configurar o Ambiente Virtual

Navegue até a pasta do projeto e crie um ambiente virtual. Isso isola as dependências do projeto.

```bash
# Navegue para a pasta da API
cd backend-api

# Crie o ambiente virtual
python3 -m venv .venv
```

### 3. Ativar o Ambiente Virtual

- **No Windows:**
  ```bash
  .\.venv\Scripts\activate
  ```
- **No macOS / Linux:**
  ```bash
  source .venv/bin/activate
  ```

### 4. Instalar as Dependências

Com o ambiente ativado, instale todas as bibliotecas necessárias que estão listadas no arquivo `requirements.txt`.

```bash
pip install -r requirements.txt
```

### 5. Iniciar a API

Após a instalação das dependências, inicie o servidor Flask:

```bash
python app.py
```

A API estará rodando em `http://127.0.0.1:5000`. O banco de dados `database.db` será criado automaticamente na primeira vez que a aplicação for iniciada.

---

## Acessando a Documentação (Swagger)

Com a API em execução, a documentação interativa do Swagger UI pode ser acessada no seu navegador através do seguinte endereço:

```
http://127.0.0.1:5000/apidocs
```

Lá você poderá ver todos os endpoints disponíveis, seus parâmetros e testá-los diretamente.
