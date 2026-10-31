import os
import sys
import unicodedata
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from trello import TrelloClient
from google import genai
from google.genai import types

# Força codificação UTF-8 no terminal Windows para evitar erros com caracteres acentuados
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")

load_dotenv()

# --- Configurações das APIs ---
TRELLO_API_KEY = os.getenv("TRELLO_API_KEY")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN")
TRELLO_BOARD_NAME = os.getenv("TRELLO_BOARD_NAME", "DIO")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Garante que GOOGLE_API_KEY esteja definido para compatibilidade com o Google ADK (adk web)
if GEMINI_API_KEY and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY


def _normalize_string(text: str) -> str:
    """Remove acentos e converte para minúsculas para comparação flexível."""
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).strip().lower()


def _get_trello_client() -> TrelloClient:
    """Valida credenciais e retorna uma instância conectada do TrelloClient."""
    if not TRELLO_API_KEY or not TRELLO_TOKEN:
        raise ValueError("TRELLO_API_KEY e TRELLO_TOKEN devem estar configurados no arquivo .env.")
    return TrelloClient(api_key=TRELLO_API_KEY, token=TRELLO_TOKEN)


def _get_board(nome_quadro: str = None):
    """
    Melhoria 1 e 6: Conexão única e centralizada com o Trello + suporte a múltiplos quadros.
    Evita repetição de código em cada ferramenta e permite escolher em qual quadro operar.
    """
    client = _get_trello_client()
    boards = [b for b in client.list_boards() if not b.closed]
    alvo = nome_quadro or TRELLO_BOARD_NAME

    for board in boards:
        if _normalize_string(board.name) == _normalize_string(alvo):
            return board

    available_boards = [b.name for b in boards]
    raise ValueError(
        f"Quadro '{alvo}' não encontrado. Quadros disponíveis: {', '.join(available_boards)}"
    )


def _get_list_by_name(board, list_name: str):
    """Encontra a lista aberta do Trello normalizando variações de acentuação e caixa."""
    target_norm = _normalize_string(list_name)
    for lst in board.list_lists(list_filter="open"):
        if _normalize_string(lst.name) == target_norm:
            return lst
    return None


# --- Ferramentas do Agente ---

def listar_quadros() -> str:
    """
    Melhoria 6: Lista todos os quadros abertos disponíveis na conta do Trello do usuário.
    """
    try:
        client = _get_trello_client()
        boards = [b.name for b in client.list_boards() if not b.closed]
        if not boards:
            return "Nenhum quadro aberto encontrado na sua conta do Trello."
        return f"Quadros disponíveis no Trello (padrão: '{TRELLO_BOARD_NAME}'): " + ", ".join(boards)
    except Exception as e:
        return f"Erro ao listar quadros: {str(e)}"


def criar_tarefa(
    nome: str,
    descricao: str = "",
    data_entrega: str = None,
    nome_quadro: str = None
) -> str:
    """
    Cria uma nova tarefa (card) no quadro do Trello na lista 'A fazer'.

    Args:
        nome: O título da tarefa.
        descricao: Descrição detalhada da tarefa.
        data_entrega: Data de entrega no formato YYYY-MM-DD.
        nome_quadro: Nome opcional do quadro no Trello (se não informado, usa o padrão DIO).
    """
    try:
        board = _get_board(nome_quadro)
        lista_a_fazer = _get_list_by_name(board, "A fazer")
        if not lista_a_fazer:
            return f"Erro: Lista 'A fazer' não foi encontrada no quadro '{board.name}'."

        due_date = "null"
        if data_entrega:
            # Melhoria 2: Correção do fuso/dia a menos.
            # Quando passamos apenas 'YYYY-MM-DD', o Trello assume 00:00 UTC,
            # o que no Brasil (UTC-3) vira 21:00 do dia anterior!
            # Convertendo para string ISO 8601 com fuso UTC-3 às 12:00:00
            # evita o erro de serialização JSON e garante a data exata no Trello.
            try:
                data_obj = datetime.strptime(data_entrega.strip()[:10], "%Y-%m-%d")
                tz_br = timezone(timedelta(hours=-3))
                due_date = data_obj.replace(hour=12, minute=0, second=0, tzinfo=tz_br).isoformat()
            except ValueError:
                due_date = "null"

        card = lista_a_fazer.add_card(name=nome, desc=descricao, due=due_date)
        data_str = f" para {data_entrega}" if data_entrega else ""
        return f"Tarefa '{card.name}' criada com sucesso na lista 'A fazer' do quadro '{board.name}'{data_str}!"
    except Exception as e:
        return f"Erro ao criar tarefa: {str(e)}"


def listar_tarefas(status: str = None, nome_quadro: str = None) -> str:
    """
    Lista tarefas do quadro do Trello. Pode listar todas ou filtrar por status.

    Args:
        status: Status opcional para filtrar ('A fazer', 'Em andamento', 'Concluído').
        nome_quadro: Nome opcional do quadro no Trello (se não informado, usa o padrão DIO).
    """
    try:
        board = _get_board(nome_quadro)
        listas = board.list_lists(list_filter="open")

        status_filtrado = _normalize_string(status) if status else None
        resultado = [f"📌 **Quadro: {board.name}**"]

        encontrou_lista = False
        for lst in listas:
            if status_filtrado and _normalize_string(lst.name) != status_filtrado:
                continue

            encontrou_lista = True
            cards = lst.list_cards()
            resultado.append(f"\n📋 **{lst.name}** ({len(cards)} tarefas):")
            if not cards:
                resultado.append("  (Nenhuma tarefa nesta lista)")
            else:
                for card in cards:
                    due_str = str(card.due)[:10] if card.due else ""
                    data_info = f" [Entrega: {due_str}]" if due_str else ""
                    resultado.append(f"  - {card.name}{data_info}")
                    if card.desc:
                        resultado.append(f"    *Detalhes: {card.desc}*")

        if not encontrou_lista:
            return f"Nenhuma lista encontrada para o status '{status}' no quadro '{board.name}'."

        return "\n".join(resultado)
    except Exception as e:
        return f"Erro ao listar tarefas: {str(e)}"


def mover_tarefa(nome_tarefa: str, novo_status: str, nome_quadro: str = None) -> str:
    """
    Move uma tarefa existente para outro status ('A fazer', 'Em andamento' ou 'Concluído').

    Args:
        nome_tarefa: O nome (ou parte do nome) da tarefa que deseja mover.
        novo_status: O novo status de destino ('A fazer', 'Em andamento', 'Concluído').
        nome_quadro: Nome opcional do quadro no Trello (se não informado, usa o padrão DIO).
    """
    try:
        board = _get_board(nome_quadro)
        # Melhoria 3: Aceita variações com/sem acento e minúsculas
        lista_destino = _get_list_by_name(board, novo_status)
        if not lista_destino:
            return f"Erro: Status '{novo_status}' não é válido. Use: 'A fazer', 'Em andamento' ou 'Concluído'."

        nome_tarefa_norm = _normalize_string(nome_tarefa)
        target_card = None

        for lst in board.list_lists(list_filter="open"):
            for card in lst.list_cards():
                if nome_tarefa_norm in _normalize_string(card.name):
                    target_card = card
                    break
            if target_card:
                break

        if not target_card:
            return f"Não encontrei nenhuma tarefa com o nome '{nome_tarefa}' no quadro '{board.name}'."

        target_card.change_list(lista_destino.id)
        return f"Tarefa '{target_card.name}' movida para '{lista_destino.name}' com sucesso!"
    except Exception as e:
        return f"Erro ao mover tarefa: {str(e)}"


def remover_tarefa(nome_tarefa: str, nome_quadro: str = None) -> str:
    """
    Melhoria 4: Ferramenta de remoção/arquivamento de tarefas.
    Remove (arquiva) uma tarefa do quadro.

    Args:
        nome_tarefa: O nome (ou parte do nome) da tarefa a ser removida.
        nome_quadro: Nome opcional do quadro no Trello (se não informado, usa o padrão DIO).
    """
    try:
        board = _get_board(nome_quadro)
        nome_tarefa_norm = _normalize_string(nome_tarefa)
        target_card = None

        for lst in board.list_lists(list_filter="open"):
            for card in lst.list_cards():
                if nome_tarefa_norm in _normalize_string(card.name):
                    target_card = card
                    break
            if target_card:
                break

        if not target_card:
            return f"Não encontrei nenhuma tarefa com o nome '{nome_tarefa}' para remover."

        nome_encontrado = target_card.name
        target_card.delete()
        return f"Tarefa '{nome_encontrado}' removida do quadro '{board.name}' com sucesso!"
    except Exception as e:
        return f"Erro ao remover tarefa: {str(e)}"


# --- Configuração de Instrução e Agente ADK ---

HOJE = datetime.now().strftime("%d/%m/%Y")
HOJE_ISO = datetime.now().strftime("%Y-%m-%d")

SYSTEM_INSTRUCTION = f"""
Você é um assistente pessoal inteligente e proativo encarregado de gerenciar as tarefas diárias do usuário em um quadro do Trello.
A data de hoje é {HOJE} ({HOJE_ISO}).

Suas diretrizes:
1. No início da conversa, cumprimente o usuário cordialmente informando a data de hoje ({HOJE}) e pergunte quais são as tarefas planejadas para o dia.
2. Quando o usuário disser o que precisa fazer, use a ferramenta 'criar_tarefa' para cada item. Defina nome claro, descrição se houver e a data de entrega (formato YYYY-MM-DD; se for para hoje, use {HOJE_ISO}).
3. Quando o usuário perguntar o que tem para fazer ou pedir resumo, use 'listar_tarefas'.
4. Quando o usuário disser que começou ou terminou algo, use 'mover_tarefa' para o status apropriado ('A fazer', 'Em andamento' ou 'Concluído').
5. Se o usuário pedir para apagar, remover ou cancelar uma tarefa, use 'remover_tarefa'.
6. Se o usuário perguntar quais quadros existem ou quiser trabalhar em outro quadro, use 'listar_quadros' ou passe 'nome_quadro' nas ferramentas.
7. Seja sempre simpático, objetivo e confirme as ações executadas no quadro.
"""

TOOLS = [criar_tarefa, listar_tarefas, mover_tarefa, remover_tarefa, listar_quadros]

# Instância para compatibilidade com Google ADK (adk web / adk run)
try:
    from google.adk.agents import Agent
    root_agent = Agent(
        name="agente_trello_dio",
        model="gemini-3.6-flash",
        description="Agente organizador de tarefas diárias no Trello com Gemini.",
        instruction=SYSTEM_INSTRUCTION,
        tools=TOOLS,
    )
except ImportError:
    root_agent = None


# --- Execução Interativa Direta no Terminal ---

def main():
    if not GEMINI_API_KEY:
        print("Erro: A variável GEMINI_API_KEY não está configurada no .env!")
        return

    client = genai.Client(api_key=GEMINI_API_KEY)

    modelos_candidatos = [
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.8-flash",
    ]

    chat = None
    modelo_escolhido = None

    for modelo in modelos_candidatos:
        try:
            temp_chat = client.chats.create(
                model=modelo,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    tools=TOOLS,
                    temperature=0.2
                )
            )
            saudacao = temp_chat.send_message("Iniciar conversa apresentando a data de hoje e perguntando as tarefas.")
            chat = temp_chat
            modelo_escolhido = modelo
            break
        except Exception:
            continue

    if not chat:
        print("\n[Erro]: Todos os modelos do Gemini estão temporariamente indisponíveis no momento. Tente novamente em alguns instantes.")
        return

    print("=" * 60)
    print("🤖 Agente de Tarefas DIO Trello iniciado!")
    print(f"📅 Data atual: {HOJE} (Modelo ativo: {modelo_escolhido})")
    print("Digite 'sair' para encerrar a conversa.")
    print("=" * 60)

    print(f"\nAgente: {saudacao.text}\n")

    while True:
        try:
            mensagem_usuario = input("Você: ")
            if not mensagem_usuario.strip():
                continue
            if mensagem_usuario.lower() in ["sair", "exit", "quit"]:
                print("\nAgente: Até mais! Tenha um dia produtivo! 👋")
                break

            resposta = chat.send_message(mensagem_usuario)
            print(f"\nAgente: {resposta.text}\n")
        except KeyboardInterrupt:
            print("\nEncerrando...")
            break
        except Exception as err:
            print(f"\n[Erro na comunicação]: {err}\n")


if __name__ == "__main__":
    main()
