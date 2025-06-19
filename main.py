# main.py
import pygame
import threading
import time
import random
import os
import google.generativeai as genai
from dotenv import load_dotenv
import sys # Adicione esta importação para sys._MEIPASS

# --- Módulos do jogo ---
from constantes import *
from classes import Carro
from funcoes import (
    carregar_e_escalar,
    desenhar_fundo,
    render_pergunta,
    obter_pergunta_disponivel,
    perguntas_multipla,
    pergunta_descritiva,
    quebrar_texto_em_linhas,
    resource_path # Certifique-se de que resource_path está importado
)
from menu import tela_de_menu

# --- Configuração da API do Gemini ---
load_dotenv(dotenv_path="chave.env")
try:
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("Chave de API do Gemini não encontrada")
    genai.configure(api_key=api_key)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    print("INFO: API do Google Gemini configurada com sucesso.")
except Exception as e:
    print(f"ERRO FATAL: Falha ao configurar a API do Gemini: {e}")
    gemini_model = None

def rodar_jogo(TELA, fonte, fonte_input, grande, clock):
    # --- Carregamento de mídia ---
    try:
        # Use resource_path para carregar o som
        pygame.mixer.music.load(resource_path('assets/sounds/FundoSo.mp3'))
        pygame.mixer.music.set_volume(0.4)
        pygame.mixer.music.play(-1)
    except pygame.error:
        pass

    pista_img = carregar_e_escalar(resource_path("assets/pista.png"), (LARGURA, ALTURA_PISTA))
    obstaculo_img = carregar_e_escalar(resource_path("assets/gelo.png"), (40, 40))
    sound_vitoria = pygame.mixer.Sound(resource_path('assets/sounds/vitoria.wav'))
    sound_obstaculo = pygame.mixer.Sound(resource_path('assets/sounds/nitro.wav'))

    carros = [Carro(resource_path(img), pos, nome) for img, pos, nome in [
        ("assets/carros/MR2.png", (50, 130), "Jogador"),
        ("assets/carros/Supra.png", (50, 180), "Bot1"),
        ("assets/carros/Uno.png", (50, 230), "Bot2"),
        ("assets/carros/Miata.png", (50, 280), "Bot3")
    ]]
    carro_jogador = carros[0]

    # --- Variáveis de jogo ---
    fase = "pergunta_multipla"
    vencedor = None
    semaforo_jogo = threading.Semaphore(1)
    pergunta_atual = None
    perguntas_ja_usadas = []
    retangulos_opcoes_clicaveis_atuais = []

    # NOVO: Gerenciamento de múltiplos obstáculos
    obstaculos_ativos = []
    NUM_OBSTACULOS_POR_RODADA = 3
    MIN_DISTANCIA_ENTRE_OBSTACULOS = 150 # Distância mínima entre obstáculos

    def gerar_obstaculos_iniciais():
        nonlocal obstaculos_ativos
        obstaculos_ativos.clear() # Limpa obstáculos anteriores
        posicoes_x_geradas = set() # Para garantir distâncias mínimas

        for _ in range(NUM_OBSTACULOS_POR_RODADA):
            pos_valida = False
            nova_pos_x = 0
            tentativas = 0
            while not pos_valida and tentativas < 100: # Limita tentativas para evitar loop infinito
                nova_pos_x = random.randint(LARGURA // 3, LARGURA - 100)
                pos_valida = True
                for p_existente in posicoes_x_geradas:
                    if abs(nova_pos_x - p_existente) < MIN_DISTANCIA_ENTRE_OBSTACULOS:
                        pos_valida = False
                        break
                tentativas += 1
            
            if pos_valida:
                obstaculos_ativos.append({"pos_x": nova_pos_x, "ativo": True})
                posicoes_x_geradas.add(nova_pos_x)
            else:
                print("Aviso: Não foi possível gerar um obstáculo com distância suficiente após muitas tentativas.")

    gerar_obstaculos_iniciais() # Chama a função para gerar no início

    pergunta_obstaculo_atual = None
    texto_input_obstaculo = ""
    verificando_com_ia_agora = False
    resposta_da_ia_pronta = threading.Event()
    resultado_da_ia = None
    bots_congelados = False
    bots_descongelam_em = 0

    def set_vencedor(nome):
        nonlocal vencedor
        if vencedor is None:
            vencedor = nome

    def bots_movimento(carro_bot, stop_event):
        """Move bots até o final da pista, pausando se congelados."""
        while not stop_event.is_set() and vencedor is None:
            if bots_congelados:
                time.sleep(0.1)
                continue
            time.sleep(random.uniform(0.15, 0.6))
            if stop_event.is_set() or vencedor is not None:
                break
            carro_bot.mover(random.randint(2, 5))
            if carro_bot.rect.x > LARGURA - 100:
                if semaforo_jogo.acquire(blocking=False):
                    try:
                        if vencedor is None:
                            set_vencedor(carro_bot.nome)
                    finally:
                        semaforo_jogo.release()

    def chamar_ia_para_verificar(pergunta_original, resposta_esperada, resposta_jogador):
        """Usa IA para avaliar resposta do jogador."""
        nonlocal resultado_da_ia, verificando_com_ia_agora
        if gemini_model is None:
            resultado_da_ia = False
        else:
            prompt = (
                "Você é um juiz em um jogo de perguntas e respostas. "
                "Sua tarefa é avaliar se a resposta de um jogador está correta "
                "ou semanticamente muito similar à resposta gabarito, considerando a pergunta original. "
                f"\n\nPergunta Original: \"{pergunta_original}\""
                f"\nResposta Esperada (Gabarito): \"{resposta_esperada}\""
                f"\nResposta do Jogador: \"{resposta_jogador}\""
                "\n\nA 'Resposta do Jogador' está correta ou é uma variação aceitável da 'Resposta Esperada'?"
                "\nResponda APENAS com a palavra 'SIM' se estiver correta/aceitável, ou APENAS com 'NAO' se estiver incorreta."
            )
            try:
                safety_settings = [{"category": c, "threshold": "BLOCK_NONE"} for c in [
                    "HARM_CATEGORY_HARASSMENT",
                    "HARM_CATEGORY_HATE_SPEECH",
                    "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "HARM_CATEGORY_DANGEROUS_CONTENT"
                ]]
                response = gemini_model.generate_content(prompt, safety_settings=safety_settings)
                resultado_da_ia = "SIM" in response.text.strip().upper()
            except Exception as e:
                print(f"Erro ao chamar a API: {e}")
                resultado_da_ia = False
        verificando_com_ia_agora = False
        resposta_da_ia_pronta.set()

    stop_bots_event = threading.Event()
    for bot in carros[1:]:
        threading.Thread(target=bots_movimento, args=(bot, stop_bots_event), daemon=True).start()

    game_running = True
    while game_running:
        clock.tick(FPS)
        pos_mouse = pygame.mouse.get_pos()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT or (evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE):
                game_running = False

            if vencedor is None:
                if evento.type == pygame.KEYDOWN and fase == "pergunta_obstaculo" and not verificando_com_ia_agora:
                    if evento.key == pygame.K_RETURN and texto_input_obstaculo.strip() and pergunta_obstaculo_atual:
                        verificando_com_ia_agora = True
                        resposta_da_ia_pronta.clear()
                        threading.Thread(
                            target=chamar_ia_para_verificar,
                            args=(pergunta_obstaculo_atual["pergunta"], pergunta_obstaculo_atual["resposta_certa"], texto_input_obstaculo),
                            daemon=True
                        ).start()
                    elif evento.key == pygame.K_BACKSPACE:
                        texto_input_obstaculo = texto_input_obstaculo[:-1]
                    elif len(texto_input_obstaculo) < 150:
                        texto_input_obstaculo += evento.unicode

                if fase == "pergunta_multipla" and pergunta_atual:
                    escolha = -1
                    if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                        for i, rect in enumerate(retangulos_opcoes_clicaveis_atuais):
                            if rect.collidepoint(pos_mouse):
                                escolha = i
                                break
                    elif evento.type == pygame.KEYDOWN and evento.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]:
                        try:
                            escolha = int(evento.unicode) - 1
                        except (ValueError, IndexError):
                            pass
                    if escolha != -1 and 0 <= escolha < len(pergunta_atual["opcoes"]):
                        if escolha == pergunta_atual["resposta"]:
                            carro_jogador.mover(MOVE_NORMAL)
                        pergunta_atual = None
                        if carro_jogador.rect.x > LARGURA - 100:
                            set_vencedor(carro_jogador.nome)

        if vencedor is None:
            # Lógica de colisão para múltiplos obstáculos
            obstaculo_colidido = None
            for obstaculo in obstaculos_ativos:
                if obstaculo["ativo"]:
                    obstaculo_hitbox = pygame.Rect(obstaculo["pos_x"], carro_jogador.rect.centery - 15, 40, 40)
                    if carro_jogador.rect.colliderect(obstaculo_hitbox):
                        obstaculo_colidido = obstaculo
                        break

            if obstaculo_colidido and fase != "pergunta_obstaculo": # Garante que não entre novamente na fase da pergunta se já estiver lá
                obstaculo_colidido["ativo"] = False # Marca o obstáculo como pego, mas não o remove da lista
                fase = "pergunta_obstaculo"
                texto_input_obstaculo = ""
                pergunta_obstaculo_atual = random.choice(pergunta_descritiva) if pergunta_descritiva else None
                try:
                    sound_obstaculo.play()
                except pygame.error:
                    pass

            if fase == "pergunta_obstaculo" and resposta_da_ia_pronta.is_set():
                if resultado_da_ia:
                    bots_congelados = True
                    bots_descongelam_em = time.time() + DURACAO_CONGELAMENTO
                fase = "pergunta_multipla"
                # Não é necessário resetar obstaculo_pego, pois agora usamos obstaculos_ativos[i]["ativo"]
                # obstaculo_pos_x = random.randint(LARGURA // 3, LARGURA - LARGURA // 3) # Não respawna, então removemos
                pergunta_obstaculo_atual = None
                resposta_da_ia_pronta.clear()

            if bots_congelados and time.time() > bots_descongelam_em:
                bots_congelados = False

            if fase == "pergunta_multipla" and not pergunta_atual:
                pergunta_atual = obter_pergunta_disponivel(perguntas_multipla, perguntas_ja_usadas)
                if not pergunta_atual:
                    set_vencedor("Fim das Perguntas")
        else:
            if 'fim_timer' not in locals():
                fim_timer = time.time() + 5
                if vencedor == carro_jogador.nome:
                    try:
                        sound_vitoria.play()
                    except pygame.error:
                        pass
            if time.time() > fim_timer:
                game_running = False

        # --- Renderização da tela ---
        # A função desenhar_fundo precisa ser atualizada para iterar sobre obstaculos_ativos
        desenhar_fundo(TELA, pista_img, obstaculo_img, obstaculos_ativos, carros) # Modificado aqui

        if vencedor is None:
            if fase == "pergunta_multipla" and pergunta_atual:
                hover = -1
                for i, rect in enumerate(retangulos_opcoes_clicaveis_atuais):
                    if rect.collidepoint(pos_mouse):
                        hover = i
                        break
                retangulos_opcoes_clicaveis_atuais = render_pergunta(TELA, fonte, pergunta_atual["pergunta"], pergunta_atual["opcoes"], AZUL, PRETO, AMARELO, hover)

            elif fase == "pergunta_obstaculo" and pergunta_obstaculo_atual:
                y = ALTURA_PISTA + 20
                linhas = quebrar_texto_em_linhas(pergunta_obstaculo_atual["pergunta"], LARGURA - 40, fonte)
                for linha in linhas:
                    TELA.blit(fonte.render(linha, True, AZUL), (20, y))
                    y += fonte.get_height()
                y_input = y + 10
                if verificando_com_ia_agora:
                    TELA.blit(fonte.render("Verificando com IA...", True, PRETO), (20, y_input))
                else:
                    input_box = pygame.Rect(20, y_input, LARGURA - 40, 40)
                    pygame.draw.rect(TELA, BRANCO, input_box)
                    pygame.draw.rect(TELA, PRETO, input_box, 2)
                    texto_input_surf = fonte_input.render(f"{texto_input_obstaculo}_", True, PRETO)
                    TELA.blit(texto_input_surf, (input_box.x + 10, input_box.y + 5))
        else:
            msg = "Você venceu!" if vencedor == carro_jogador.nome else f"{vencedor} venceu!"
            if vencedor == "Fim das Perguntas":
                msg = "Perguntas esgotadas!"
            cor = VERDE if vencedor == carro_jogador.nome else VERMELHO
            texto = grande.render(msg, True, cor)
            TELA.blit(texto, texto.get_rect(center=(LARGURA / 2, ALTURA_PISTA + (ALTURA - ALTURA_PISTA) / 2)))

        pygame.display.flip()

    stop_bots_event.set()
    return "menu"

def main():
    pygame.init()
    pygame.display.set_caption("Corrida Sensata")
    TELA = pygame.display.set_mode((LARGURA, ALTURA))
    fonte_titulo = pygame.font.Font(None, 80)
    fonte_botao = pygame.font.Font(None, 50)
    fonte_jogo = pygame.font.Font(None, 36)
    fonte_input_jogo = pygame.font.Font(None, 32)
    grande_jogo = pygame.font.Font(None, 72)
    clock = pygame.time.Clock()
    estado_atual = "menu"

    while True:
        if estado_atual == "menu":
            estado_atual = tela_de_menu(TELA, fonte_titulo, fonte_botao)
        elif estado_atual == "JOGANDO":
            estado_atual = rodar_jogo(TELA, fonte_jogo, fonte_input_jogo, grande_jogo, clock)
        elif estado_atual == "SAIR":
            break

    pygame.quit()
    print("Jogo encerrado.")

if __name__ == '__main__':
    main()