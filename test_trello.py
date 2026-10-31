import os
from dotenv import load_dotenv
from trello import TrelloClient

load_dotenv()

key = os.getenv("TRELLO_API_KEY")
token = os.getenv("TRELLO_TOKEN")
board_name = os.getenv("TRELLO_BOARD_NAME", "DIO")

print("--- Teste de Conexão com o Trello ---")
print(f"Buscando quadro: '{board_name}'...")

if not key or not token:
    print("❌ Erro: TRELLO_API_KEY ou TRELLO_TOKEN não foram encontrados no arquivo .env!")
    exit(1)

try:
    client = TrelloClient(api_key=key, token=token)
    boards = client.list_boards()
    print(f"Total de quadros encontrados na sua conta: {len(boards)}")
    
    target_board = None
    for b in boards:
        print(f" - Quadro: {b.name}")
        if b.name.strip().lower() == board_name.strip().lower():
            target_board = b

    if target_board:
        print(f"\n[SUCESSO] Quadro '{target_board.name}' encontrado com sucesso!")
        print("Listas presentes no quadro:")
        for lst in target_board.list_lists():
            print(f"  - Lista: {lst.name} ({len(lst.list_cards())} cards)")
        print("\nTudo pronto para rodar o agente!")
    else:
        print(f"\n[AVISO] Quadro '{board_name}' nao foi encontrado. Verifique o nome no Trello ou no .env.")

except Exception as e:
    print(f"\n[ERRO] Falha ao conectar com o Trello: {e}")

