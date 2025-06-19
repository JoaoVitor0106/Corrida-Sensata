import pygame
import threading
import time
import json
import random
import os
import google.generativeai as genai  # Para utilizar o modelo Gemini
from dotenv import load_dotenv       # Para carregar a chave da API de um arquivo .env

# --- IMPORTAÇÃO DOS MÓDULOS DO JOGO ---
from constantes import *
from classes import Carro
from funcoes import (
    carregar_e_escalar,
    desenhar_fundo,
    render_pergunta,
    obter_pergunta_disponivel,
    perguntas_multipla,
    pergunta_descritiva,
    remover_acentos,
    quebrar_texto_em_linhas  # Garante que longas perguntas caibam na tela
)
from menu import tela_de_menu  # Tela inicial do jogo

# --- CONFIGURAÇÃO DA API DO GEMINI ---
load_dotenv(dotenv_path="chave.env")  # Carrega a chave da API do arquivo .env
try:
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key: raise ValueError("Chave de API do Gemini não encontrada")
    genai.configure(api_key=api_key)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    print("INFO: API do Google Gemini configurada com sucesso.")
except Exception as e:
    print(f"ERRO FATAL: Falha ao configurar a API do Gemini: {e}")
    gemini_model = None

# --- FUNÇÃO PRINCIPAL DO JOGO ---
def rodar_jogo(TELA, fonte, fonte_input, grande, clock):
    # --- Toca música de fundo em loop ---
    try:
        pygame.mixer.music.load('assets/sounds/FundoSo.mp3')
        pygame.mixer.music.set_volume(0.4)
        pygame.mixer.music.play(-1)
    except pygame.error as e:
        print(f"Erro ao carregar som de fundo: {e}")

    # --- CARREGAMENTO DE IMAGENS E SONS ---
    pista_img = carregar_e_escalar("assets/pista.png", (LARGURA, ALTURA_PISTA))
    obstaculo_img = carregar_e_escalar("assets/gelo.png", (40, 40))
    sound_vitoria = pygame.mixer.Sound('assets/sounds/vitoria.wav')
    sound_obstaculo = pygame.mixer.Sound('assets/sounds/nitro.wav')

    # --- INSTÂNCIA DOS CARROS ---
    carros = [Carro(img, pos, nome) for img, pos, nome in [
        ("assets/carros/MR2.png", (50, 130), "Jogador"),
        ("assets/carros/Supra.png", (50, 180), "Bot1"),
        ("assets/carros/Uno.png", (50, 230), "Bot2"),
        ("assets/carros/Miata.png", (50, 280), "Bot3")
    ]]
    carro_jogador = carros[0]

    # --- VARIÁVEIS DE ESTADO DO JOGO ---
    fase = "pergunta_multipla"
    vencedor = None
    semaforo_jogo = threading.Semaphore(1)  # Evita múltiplos vencedores
    pergunta_atual = None
    perguntas_ja_usadas = []
    retangulos_opcoes_clicaveis_atuais = []

    # --- OBSTÁCULO ---
    obstaculo_pos_x = random.randint(LARGURA // 3, LARGURA - LARGURA // 3)
    obstaculo_pego = False
    pergunta_obstaculo_atual = None
    texto_input_obstaculo = ""
    verificando_com_ia_agora = False
    resposta_da_ia_pronta = threading.Event()
    resultado_da_ia = None

    # --- BOTS CONGELADOS QUANDO O JOGADOR ACERTA A PERGUNTA DESCRITIVA ---
    bots_congelados = False
    bots_descongelam_em = 0

    # --- Define o vencedor ---
    def set_vencedor(nome):
        nonlocal vencedor
        if vencedor is None: vencedor = nome

    # --- Função que move os bots em threads paralelas ---
    def bots_movimento(carro_obj, stop_event):
        while not stop_event.is_set() and vencedor is None:
            if bots_congelados:
                time.sleep(0.1)
                continue
            time.sleep(random.uniform(0.15, 0.6))  # Simula o tempo de resposta dos bots
            if stop_event.is_set() or vencedor is not None: break
            carro_obj.mover(random.randint(3, 8))
            if carro_obj.rect.x > LARGURA - 100:
                if semaforo_jogo.acquire(blocking=False):
                    try:
                        if vencedor is None: set_vencedor(carro_obj.nome)
                    finally: semaforo_jogo.release()

    # --- Verifica resposta com a IA (para perguntas descritivas) ---
    def chamar_ia_para_verificar(p_original, r_esperada_gabarito, r_jogador):
        nonlocal resultado_da_ia, verificando_com_ia_agora
        if gemini_model is None:
            resultado_da_ia = False
        else:
            prompt = f'Você é um juiz em um jogo...'
            try:
                # Segurança desativada para evitar bloqueios da IA
                safety_settings = [{"category": c, "threshold": "BLOCK_NONE"} for c in [
                    "HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", 
                    "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]
                response = gemini_model.generate_content(prompt, safety_settings=safety_settings)
                resultado_da_ia = "SIM" in response.text.strip().upper()
            except Exception as e:
                print(f"Erro ao chamar a API: {e}")
                resultado_da_ia = False
        verificando_com_ia_agora = False
        resposta_da_ia_pronta.set()

    # --- Inicia as threads dos bots ---
    stop_bots_event = threading.Event()
    for bot in carros[1:]:
        threading.Thread(target=bots_movimento, args=(bot, stop_bots_event), daemon=True).start()

    # --- LOOP PRINCIPAL DO JOGO ---
    game_running = True
    while game_running:
        clock.tick(FPS)
        posicao_mouse_frame_atual = pygame.mouse.get_pos()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT or (evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE):
                game_running = False

            # --- EVENTOS DURANTE O JOGO ---
            if vencedor is None:
                # Entrada de texto para pergunta descritiva
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

                # Escolha de múltipla escolha
                if fase == "pergunta_multipla" and pergunta_atual:
                    escolha = -1
                    if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                        for i, rect in enumerate(retangulos_opcoes_clicaveis_atuais):
                            if rect.collidepoint(posicao_mouse_frame_atual):
                                escolha = i
                                break
                    elif evento.type == pygame.KEYDOWN and evento.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]:
                        try: escolha = int(evento.unicode) - 1
                        except (ValueError, IndexError): pass
                    if escolha != -1 and 0 <= escolha < len(pergunta_atual["opcoes"]):
                        if escolha == pergunta_atual["resposta"]:
                            carro_jogador.mover(MOVE_NORMAL)
                        pergunta_atual = None
                        if carro_jogador.rect.x > LARGURA - 100:
                            set_vencedor(carro_jogador.nome)

        # --- LÓGICA DO OBSTÁCULO E CONGELAMENTO DOS BOTS ---
        if vencedor is None:
            obstaculo_hitbox = pygame.Rect(obstaculo_pos_x, carro_jogador.rect.centery - 15, 40, 40)
            if not obstaculo_pego and carro_jogador.rect.colliderect(obstaculo_hitbox):
                obstaculo_pego = True
                fase = "pergunta_obstaculo"
                texto_input_obstaculo = ""
                pergunta_obstaculo_atual = random.choice(pergunta_descritiva) if pergunta_descritiva else None
                try: sound_obstaculo.play()
                except pygame.error: pass

            if fase == "pergunta_obstaculo" and resposta_da_ia_pronta.is_set():
                if resultado_da_ia:
                    bots_congelados = True
                    bots_descongelam_em = time.time() + DURACAO_CONGELAMENTO
                fase = "pergunta_multipla"
                obstaculo_pego = False
                obstaculo_pos_x = random.randint(LARGURA//3, LARGURA-LARGURA//3)
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
                    try: sound_vitoria.play()
                    except pygame.error: pass
            if time.time() > fim_timer:
                game_running = False

        # --- RENDERIZAÇÃO VISUAL ---
        desenhar_fundo(TELA, pista_img, obstaculo_img, obstaculo_pego, obstaculo_pos_x, carros)

        if vencedor is None:
            if fase == "pergunta_multipla" and pergunta_atual:
                indice_hover = -1
                for i, rect in enumerate(retangulos_opcoes_clicaveis_atuais):
                    if rect.collidepoint(posicao_mouse_frame_atual):
                        indice_hover = i
                        break
                retangulos_opcoes_clicaveis_atuais = render_pergunta(
                    TELA, fonte, pergunta_atual["pergunta"],
                    pergunta_atual["opcoes"], AZUL, PRETO, AMARELO, indice_hover
                )
            elif fase == "pergunta_obstaculo" and pergunta_obstaculo_atual:
                y_pos_q = ALTURA_PISTA + 20
                linhas = quebrar_texto_em_linhas(pergunta_obstaculo_atual["pergunta"], LARGURA - 40, fonte)
                for linha in linhas:
                    texto_surf = fonte.render(linha, True, AZUL)
                    TELA.blit(texto_surf, (20, y_pos_q))
                    y_pos_q += fonte.get_height()
                y_pos_input = y_pos_q + 10
                if verificando_com_ia_agora:
                    msg_espera_surf = fonte.render("Verificando com IA...", True, PRETO)
                    TELA.blit(msg_espera_surf, (20, y_pos_input))
                else:
                    input_box_rect = pygame.Rect(20, y_pos_input, LARGURA - 40, 40)
                    pygame.draw.rect(TELA, BRANCO, input_box_rect)
                    pygame.draw.rect(TELA, PRETO, input_box_rect, 2)
                    texto_input_surf = fonte_input.render(f"{texto_input_obstaculo}_", True, PRETO)
                    TELA.blit(texto_input_surf, (input_box_rect.x + 10, input_box_rect.y + 5))
        else:
            msg = "Você venceu!" if vencedor == carro_jogador.nome else f"{vencedor} venceu!"
            if vencedor == "Fim das Perguntas": msg = "Perguntas esgotadas!"
            cor = VERDE if vencedor == carro_jogador.nome else VERMELHO
            texto_final_surf = grande.render(msg, True, cor)
            TELA.blit(texto_final_surf, texto_final_surf.get_rect(center=(LARGURA / 2, ALTURA_PISTA + (ALTURA - ALTURA_PISTA) / 2)))

        pygame.display.flip()  # Atualiza tela a cada frame

    stop_bots_event.set()  # Finaliza as threads dos bots
    return "menu"  # Volta para o menu

# --- FUNÇÃO MAIN: gerencia o ciclo do jogo/menu ---
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

# --- EXECUÇÃO PRINCIPAL ---
if __name__ == '__main__':
    main()
