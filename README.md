# 🤖 Agente de Tarefas com Google ADK, Gemini e Trello (Desafio DIO)

Agente inteligente em Python desenvolvido para organizar tarefas diárias em um quadro do **Trello** por meio de conversação em linguagem natural, utilizando o **Google Agent Development Kit (ADK)**, o modelo **Google Gemini** e a biblioteca **`py-trello`**.

---

## 📌 O que o Agente Faz

O agente atua como um assistente pessoal de produtividade conectado em tempo real ao seu Trello:
1. **Início Proativo**: Inicia a conversa cumprimentando o usuário, informando a data de hoje e perguntando quais são as tarefas planejadas para o dia.
2. **Criação de Cards (`criar_tarefa`)**: Cria automaticamente cards na lista `A fazer`, configurando título, descrição e prazo de entrega.
3. **Listagem Flexível (`listar_tarefas`)**: Consulta e retorna todas as tarefas do quadro ou filtra por um status específico (`A fazer`, `Em andamento`, `Concluído`).
4. **Movimentação Dinâmica (`mover_tarefa`)**: Move o card entre `A fazer`, `Em andamento` e `Concluído` quando o usuário relata seu progresso.
5. **Remoção de Tarefas (`remover_tarefa`)**: Permite remover/arquivar tarefas canceladas ou descartadas.
6. **Multi-Quadro (`listar_quadros`)**: Lista todos os quadros disponíveis na conta e permite escolher em qual quadro operar.

---

## 🛠️ Ferramentas (Tools) do Agente

Cada função Python no [`agent.py`](agent.py) foi transformada em uma ferramenta (*Function Calling*) que o Gemini decide acionar automaticamente a partir da conversa:

| Ferramenta | Descrição | Parâmetros |
| :--- | :--- | :--- |
| `criar_tarefa` | Cria um novo card na lista `A fazer` com título, descrição e prazo. | `nome`, `descricao`, `data_entrega`, `nome_quadro` (opcional) |
| `listar_tarefas` | Lista todas as tarefas do quadro ou filtra por uma lista específica. | `status` (opcional), `nome_quadro` (opcional) |
| `mover_tarefa` | Move um card existente para `A fazer`, `Em andamento` ou `Concluído`. | `nome_tarefa`, `novo_status`, `nome_quadro` (opcional) |
| `remover_tarefa` | Remove/arquiva um card do quadro do Trello. | `nome_tarefa`, `nome_quadro` (opcional) |
| `listar_quadros` | Lista todos os quadros abertos na conta do Trello do usuário. | *(nenhum)* |

---

## 🚀 Melhorias Implementadas (Evoluções do Desafio)

Implementamos **todas as 6 melhorias sugeridas** no desafio da DIO:

1. **Correção da Data que chegava com 1 dia a menos no Trello**:
   - **Causa**: Ao enviar apenas `YYYY-MM-DD`, o Trello interpreta como `00:00 UTC`, o que no fuso horário de Brasília (`UTC-3`) recua para as `21:00` do dia anterior, além de objetos `datetime` puros causarem `TypeError: Object of type datetime is not JSON serializable` em versões recentes do `py-trello`.
   - **Solução**: Convertemos a data para uma string ISO 8601 com fuso horário explícito (`UTC-3` às `12:00:00`), garantindo que o card exiba o dia exato no Trello.
2. **Aceitar `"concluído"` com ou sem acento e variações de caixa (`_normalize_string`)**:
   - Utilizamos `unicodedata.normalize('NFKD', ...)` para remover acentos e padronizar strings em minúsculas, permitindo que `"concluido"`, `"Concluído"`, `"a fazer"` ou `"EM ANDAMENTO"` funcionem sem erro de status inválido.
3. **Nova Ferramenta de Remover Tarefa (`remover_tarefa`)**:
   - A instrução original prometia remover tarefas, mas o código base não possuía a função. Implementamos e registramos `remover_tarefa` no agente.
4. **Tratamento de Erros com `try/except` em Todas as Ferramentas**:
   - Todas as 5 ferramentas possuem blocos `try/except` que capturam falhas de rede, parâmetros ou API e retornam mensagens claras para o agente explicar ao usuário.
5. **Conexão Centralizada com o Trello (`_get_trello_client` e `_get_board`)**:
   - Eliminamos a repetição de código concentrando a autenticação e busca do quadro em funções auxiliares reutilizadas por todas as ferramentas.
6. **Suporte a Múltiplos Quadros (`listar_quadros` e `nome_quadro`)**:
   - O agente pode consultar todos os quadros da conta do usuário e operar em qualquer quadro informado na conversa.

---

## ⚙️ Como Configurar o Trello e as Credenciais

### 1. Preparar o Quadro no Trello
1. Crie uma conta ou acesse o [Trello](https://trello.com/).
2. Crie um quadro chamado **`DIO`** (ou defina o nome desejado no `.env`).
3. Certifique-se de que o quadro possui as 3 listas:
   - `A fazer`
   - `Em andamento`
   - `Concluído`
4. Acesse o portal de desenvolvedores do Trello em **[https://trello.com/power-ups/admin](https://trello.com/power-ups/admin)**:
   - Crie uma nova integração/Power-Up.
   - Gere sua **API Key** (`TRELLO_API_KEY`).
   - Clique no link **Token** na mesma página para autorizar e copiar seu **Token** (`TRELLO_TOKEN`).

### 2. Obter a Chave do Google Gemini
1. Acesse o [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Gere uma chave gratuita de API (`GEMINI_API_KEY`).

### 3. Configurar o Ambiente Local
```bash
# 1. Clone o repositório
git clone https://github.com/SEU_USUARIO/dio-agente-tarefas-trello.git
cd dio-agente-tarefas-trello

# 2. Crie e ative o ambiente virtual (Python 3.10+)
python -m venv .venv

# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Crie o arquivo .env a partir do modelo
cp .env.example .env
```

Preencha o arquivo `.env` com as suas chaves reais (o `.env` está protegido no `.gitignore`):
```env
GEMINI_API_KEY=sua_chave_gemini_aqui
TRELLO_API_KEY=sua_chave_trello_aqui
TRELLO_TOKEN=seu_token_trello_aqui
TRELLO_BOARD_NAME=DIO
```

---

## 🧪 Como Executar e Como Foi Testado

### 1. Teste de Conexão com o Trello
```bash
python test_trello.py
```

### 2. Executar pela Interface Web do Google ADK (`adk web`)
Na raiz do repositório, execute:
```bash
adk web
```
Acesse o endereço exibido no terminal (geralmente `http://localhost:8000`), selecione o agente `trello_agent` e converse pelo navegador!

### 3. Executar Direto no Terminal Interativo
```bash
python agent.py
```

### Evidência de Testes Executados
Todas as ferramentas e melhorias foram validadas em um quadro real do Trello:
```text
============================================================
🤖 Agente de Tarefas DIO Trello iniciado!
📅 Data atual: 31/10/2026 (Modelo ativo: gemini-3.6-flash)
Digite 'sair' para encerrar a conversa.
============================================================

Agente: Olá! Bom dia! Hoje é 31/10/2026. Quais são as tarefas que você tem planejadas para o dia de hoje?

Você: Oi! Quais tarefas eu tenho no meu quadro hoje?
Agente: Aqui estão as tarefas atuais no seu quadro **DIO**:
- **A fazer**: Revisar documentacao README (Entrega: 31/10/2026)
- **Em andamento**: Publicar projeto no GitHub e LinkedIn (Entrega: 31/10/2026)
- **Concluído**: Finalizar Desafio DIO Agente Trello (Entrega: 01/11/2026)
```

---

## 📁 Estrutura do Repositório

- [`agent.py`](agent.py): Código principal do agente, ferramentas Python, integração com Gemini e execução no terminal.
- [`trello_agent/`](trello_agent/agent.py): Módulo estruturado para execução via `adk web` / `adk run`.
- [`test_trello.py`](test_trello.py): Script de diagnóstico rápido de conexão e listas do Trello.
- [`requirements.txt`](requirements.txt): Dependências do projeto (`google-adk`, `google-genai`, `py-trello`, `python-dotenv`).
- [`.env.example`](.env.example): Modelo de configuração de variáveis de ambiente (sem expor segredos).
- [`.gitignore`](.gitignore): Proteção para garantir que `.env` e `.venv` nunca sejam versionados.
