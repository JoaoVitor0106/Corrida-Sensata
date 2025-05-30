# main.py
import pygame
import threading
import time
import json
import requests # Para chamadas HTTP ao Ollama
import random
import unicodedata # Para remover_acentos

from constantes import *
from carro import Carro
# Importa as funções e a pergunta_descritiva carregada de funcoes.py
from funcoes import (
    carregar_e_escalar,
    desenhar_fundo,
    render_pergunta,
    obter_pergunta_disponivel,
    pergunta_descritiva # Assumindo que funcoes.py carrega isso globalmente
)

# Inicialização do Pygame e Display
pygame.init()
pygame.mixer.init() 
TELA = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Corrida Sensata")
fonte = pygame.font.Font(None, 36)
fonte_input = pygame.font.Font(None, 32) 
grande = pygame.font.Font(None, 72)
clock = pygame.time.Clock()

# Carregar Assets
pista_img = carregar_e_escalar("assets/pista.png", (LARGURA, ALTURA_PISTA))
nitro_img = carregar_e_escalar("assets/nitro.png", (30, 30))

# Instanciar Carros
Carro1 = Carro("assets/carros/Civic.png", (50, 130), "Jogador")
Carro2 = Carro("assets/carros/Supra.png", (50, 180), "Bot1")
Carro3 = Carro("assets/carros/Uno.png", (50, 230), "Bot2")
Carro4 = Carro("assets/carros/Miata.png", (50, 280), "Bot3")
carros = [Carro1, Carro2, Carro3, Carro4]

# Variáveis Globais para IA e Input do Nitro
texto_input_nitro = ""
resposta_da_ia_pronta = threading.Event()
resultado_da_ia = None  
verificando_com_ia_agora = False
NOME_MODELO_OLLAMA = "phi3:latest" # !!! CONFIRME O NOME DO SEU MODELO OLLAMA !!!

# Variáveis de Estado do Jogo
jogando = True
fase = "pergunta_multipla"
pergunta_atual = None 
perguntas_ja_usadas = []
nitro_pos_x = random.randint(LARGURA // 3, LARGURA - LARGURA // 3) 
nitro_pego = False
game_state = "running"  
vencedor = None 
semaforo_jogo = threading.Semaphore(1)

# UI de Perguntas
retangulos_opcoes_clicaveis_atuais = []
indice_opcao_com_hover_atual = None

# --- Funções Auxiliares ---
def remover_acentos(texto):
    if texto is None: return ""
    try:
        nfkd_form = unicodedata.normalize('NFKD', str(texto))
        return "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    except TypeError:
        return str(texto)

def chamar_ia_para_verificar(p_original, r_esperada_gabarito, r_jogador, nome_modelo):
    global resultado_da_ia, resposta_da_ia_pronta, verificando_com_ia_agora
    # verificando_com_ia_agora é setado para True pela thread principal ANTES de chamar esta função.
    # resposta_da_ia_pronta.clear() e resultado_da_ia = None também são feitos pela thread principal.
    print(f"THREAD IA ({threading.get_ident()}): Iniciada. 'verificando_com_ia_agora' já deve ser True.")

    prompt = f"""Você é um juiz em um jogo de perguntas e respostas. Sua tarefa é avaliar se a resposta de um jogador está correta ou semanticamente muito similar a uma resposta gabarito, considerando a pergunta original.

Pergunta Original: "{p_original}"
Resposta Esperada (Gabarito): "{r_esperada_gabarito}"
Resposta do Jogador: "{r_jogador}"

A "Resposta do Jogador" está correta ou é uma variação aceitável da "Resposta Esperada" (por exemplo, contém as palavras-chave mais importantes ou o significado central)?
Responda APENAS com a palavra "SIM" se estiver correta/aceitável, ou APENAS com a palavra "NAO" se estiver incorreta.
"""
    try:
        payload = {
            "model": nome_modelo, "prompt": prompt, "stream": False,
            "options": {"temperature": 0.1, "num_predict": 10}
        }
        print(f"DEBUG: Enviando para Ollama (modelo {nome_modelo})")
        response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        resposta_ia_texto = data.get("response", "").strip().upper()
        print(f"DEBUG IA: Resposta crua: '{data.get('response', '')}', Processada: '{resposta_ia_texto}'")

        if "SIM" in resposta_ia_texto:
            resultado_da_ia = True
        elif "NAO" in resposta_ia_texto:
            resultado_da_ia = False
        else:
            print("DEBUG IA: Resposta da IA não conclusiva. Considerando incorreta.")
            resultado_da_ia = False
    except requests.exceptions.Timeout:
        print(f"Erro de Timeout ao conectar com Ollama. Verifique se o Ollama está rodando e o modelo '{nome_modelo}' está acessível.")
        resultado_da_ia = False
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão com Ollama: {e}. Verifique se o Ollama está rodando e o modelo '{nome_modelo}' está disponível.")
        resultado_da_ia = False
    except Exception as e:
        print(f"Erro inesperado ao processar IA: {e}")
        resultado_da_ia = False
    finally:
        print(f"THREAD IA ({threading.get_ident()}): Bloco finally. Setando verificando_com_ia_agora = False.")
        verificando_com_ia_agora = False
        resposta_da_ia_pronta.set()
        print(f"THREAD IA ({threading.get_ident()}): Finalizada. 'verificando_com_ia_agora'={verificando_com_ia_agora}, 'resposta_da_ia_pronta'={resposta_da_ia_pronta.is_set()}.")


# --- Lógica dos Bots e Jogo ---
def bots_movimento(carro_obj):
    global game_state, vencedor, verificando_com_ia_agora

    # print(f"Bot {carro_obj.nome} iniciando. Estado inicial: game_state='{game_state}', vencedor='{vencedor}', ia_verificando='{verificando_com_ia_agora}'")
    while game_state == "running" and vencedor is None:
        if verificando_com_ia_agora:
            # print(f"Bot {carro_obj.nome} PAUSADO esperando IA.")
            try:
                time.sleep(0.1) 
            except Exception:
                break
            continue 
            
        try:
            tempo_pausa = random.uniform(0.15, 0.6) 
            time.sleep(tempo_pausa)
        except Exception: 
            break 

        if game_state != "running" or vencedor is not None:
            break 
        
        if verificando_com_ia_agora:
            continue 

        distancia_movimento = random.randint(3, 8) 
        carro_obj.mover(distancia_movimento)

        if carro_obj.rect.x > LARGURA - 100: 
            if semaforo_jogo.acquire(blocking=False):
                try:
                    if vencedor is None: 
                        game_over(carro_obj.nome)
                finally:
                    semaforo_jogo.release()
                break 

def game_over(vencedor_nome_atual):
    global game_state, retangulos_opcoes_clicaveis_atuais, vencedor
    if game_state == "running": 
        print(f"INFO: Evento de fim de jogo para: {vencedor_nome_atual}!")
        vencedor = vencedor_nome_atual 
        if vencedor_nome_atual == Carro1.nome:
            game_state = "win"
        else: 
            game_state = "lose"
        
        retangulos_opcoes_clicaveis_atuais = []
        try:
            if not pygame.mixer.get_init(): pygame.mixer.init() # Garante que o mixer está init
            if game_state == "win": 
                sound_vitoria = pygame.mixer.Sound('assets/sounds/vitoria.wav')
                sound_vitoria.play()
            # else: 
            #     sound_derrota = pygame.mixer.Sound('assets/sounds/derrota.wav')
            #     sound_derrota.play()
        except pygame.error as e:
            print(f"Erro ao tocar som em game_over: {e}")

def iniciar_bots():
    for bot_obj in [Carro2, Carro3, Carro4]:
        thread_bot = threading.Thread(target=bots_movimento, args=(bot_obj,), daemon=True)
        thread_bot.start()

iniciar_bots()

# === LOOP PRINCIPAL DO JOGO ===
while jogando:
    clock.tick(FPS)
    posicao_mouse_frame_atual = pygame.mouse.get_pos()

    # --- 1. TRATAMENTO DE EVENTOS ---
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            jogando = False
            game_state = "quit"
        
        elif evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                jogando = False
                game_state = "quit"

            if game_state == "running" and vencedor is None:
                if fase == "pergunta_nitro":
                    if evento.key == pygame.K_RETURN:
                        if texto_input_nitro.strip():
                            if not verificando_com_ia_agora: # MODIFICADO: Controle da flag ANTES de iniciar thread
                                print("INFO: Preparando para enviar resposta para IA...")
                                verificando_com_ia_agora = True 
                                resposta_da_ia_pronta.clear()   
                                resultado_da_ia = None          

                                if pergunta_descritiva and "pergunta" in pergunta_descritiva and "resposta_certa" in pergunta_descritiva:
                                    thread_ia = threading.Thread(
                                        target=chamar_ia_para_verificar,
                                        args=(
                                            pergunta_descritiva["pergunta"],
                                            pergunta_descritiva["resposta_certa"], 
                                            texto_input_nitro,
                                            NOME_MODELO_OLLAMA 
                                        ),
                                        daemon=True
                                    )
                                    print(f"MAIN THREAD: Iniciando thread IA {thread_ia.name if hasattr(thread_ia, 'name') else 'sem nome'}...")
                                    thread_ia.start()
                                else:
                                    print("ERRO: Pergunta descritiva não carregada ou chave 'resposta_certa' ausente!")
                                    fase = "pergunta_multipla" 
                                    nitro_pego = False 
                                    verificando_com_ia_agora = False # Reseta se a thread não foi iniciada
                            else:
                                print("INFO: IA já está processando uma resposta. Aguarde.")
                        # else: input vazio, não faz nada no Enter
                    elif evento.key == pygame.K_BACKSPACE:
                        if not verificando_com_ia_agora:
                            texto_input_nitro = texto_input_nitro[:-1]
                    else: 
                        if not verificando_com_ia_agora:
                            if len(texto_input_nitro) < 150: 
                                texto_input_nitro += evento.unicode
                
                elif fase == "pergunta_multipla" and pergunta_atual:
                    if evento.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]:
                        try:
                            opcao_pelo_teclado = int(evento.unicode) - 1
                            if 0 <= opcao_pelo_teclado < len(pergunta_atual["opcoes"]):
                                if semaforo_jogo.acquire(blocking=False):
                                    try:
                                        acertou = (opcao_pelo_teclado == pergunta_atual["resposta"])
                                        if acertou:
                                            print("INFO: Resposta múltipla escolha CORRETA!")
                                            Carro1.mover(MOVE_NORMAL)
                                        else:
                                            print("INFO: Resposta múltipla escolha INCORRETA.")
                                        
                                        pergunta_atual = None 
                                        retangulos_opcoes_clicaveis_atuais = []
                                        if Carro1.rect.x > LARGURA - 100 and game_state == "running" and vencedor is None:
                                            game_over(Carro1.nome)
                                    finally:
                                        semaforo_jogo.release()
                        except ValueError:
                            pass 

        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if evento.button == 1 and game_state == "running" and \
               fase == "pergunta_multipla" and pergunta_atual and vencedor is None:
                for i, rect_opcao_clicavel in enumerate(retangulos_opcoes_clicaveis_atuais):
                    if rect_opcao_clicavel.collidepoint(posicao_mouse_frame_atual):
                        if semaforo_jogo.acquire(blocking=False):
                            try:
                                acertou = (i == pergunta_atual["resposta"])
                                if acertou:
                                    print("INFO: Resposta múltipla escolha CORRETA! (mouse)")
                                    Carro1.mover(MOVE_NORMAL)
                                else:
                                    print("INFO: Resposta múltipla escolha INCORRETA. (mouse)")

                                pergunta_atual = None
                                retangulos_opcoes_clicaveis_atuais = []
                                if Carro1.rect.x > LARGURA - 100 and game_state == "running" and vencedor is None:
                                    game_over(Carro1.nome)
                            finally:
                                semaforo_jogo.release()
                        break 

    # --- 2. LÓGICA DO JOGO / ATUALIZAÇÕES DE ESTADO ---
    if game_state == "running" and vencedor is None:
        nitro_y_pos = Carro1.rect.centery - (nitro_img.get_height() // 2) 
        nitro_hitbox = pygame.Rect(nitro_pos_x, nitro_y_pos, nitro_img.get_width(), nitro_img.get_height())
        
        if not nitro_pego and Carro1.rect.colliderect(nitro_hitbox):
            if fase != "pergunta_nitro": 
                print("INFO: Nitro pego!")
                nitro_pego = True
                fase = "pergunta_nitro"
                texto_input_nitro = ""
                # Reseta flags da IA ao pegar o nitro
                verificando_com_ia_agora = False
                resposta_da_ia_pronta.clear()
                resultado_da_ia = None
                try:
                    sound_nitro = pygame.mixer.Sound('assets/sounds/nitro.wav')
                    sound_nitro.play()
                except pygame.error as e: 
                    print(f"Erro ao tocar som do nitro: {e}")
        
        if fase == "pergunta_nitro" and resposta_da_ia_pronta.is_set():
            if resultado_da_ia is not None: 
                if semaforo_jogo.acquire(blocking=False):
                    try:
                        if resultado_da_ia: 
                            print("✅ Resposta correta (IA)! Nitro ativado.")
                            Carro1.mover(MOVE_NITRO)
                            if Carro1.rect.x > LARGURA - 100 and game_state == "running" and vencedor is None:
                                game_over(Carro1.nome)
                        else:
                            print("❌ Resposta incorreta para o nitro (IA) ou erro na IA.")
                        
                        fase = "pergunta_multipla" 
                        texto_input_nitro = ""
                        # nitro_pego = True # Mantém pego, ou False se quiser que reapareça
                    finally:
                        semaforo_jogo.release()
                
                # Reseta flags da IA após processar o resultado
                resposta_da_ia_pronta.clear()
                resultado_da_ia = None
                # verificando_com_ia_agora já foi setado para False pela thread da IA
        
        if fase == "pergunta_multipla" and not pergunta_atual and not verificando_com_ia_agora:
            if semaforo_jogo.acquire(blocking=False):
                try:
                    if pergunta_atual is None: # Simplificado: se não há pergunta, busca uma
                        nova_pergunta = obter_pergunta_disponivel(perguntas_ja_usadas)
                        if nova_pergunta:
                            pergunta_atual = nova_pergunta
                        else: 
                            if game_state == "running" and vencedor is None:
                                print("INFO: Todas as perguntas de múltipla escolha respondidas! Você perdeu.")
                                game_over("Fim das Perguntas") 
                finally:
                    semaforo_jogo.release()

    # --- 3. LÓGICA DE DESENHO ---
    desenhar_fundo(TELA, pista_img, nitro_img, nitro_pego, nitro_pos_x, carros)
    
    indice_opcao_com_hover_atual = None 
    if fase == "pergunta_multipla" and pergunta_atual and game_state == "running":
        # Atualiza o hover ANTES de renderizar a pergunta, para que render_pergunta use o índice correto
        if retangulos_opcoes_clicaveis_atuais: 
             for i_hover, rect_opcao_hover in enumerate(retangulos_opcoes_clicaveis_atuais):
                if rect_opcao_hover.collidepoint(posicao_mouse_frame_atual):
                    indice_opcao_com_hover_atual = i_hover
                    break
    
    # Seção principal de desenho baseada no estado do jogo
    if game_state == "running":
        if fase == "pergunta_multipla":
            if pergunta_atual: 
                retangulos_opcoes_clicaveis_atuais = render_pergunta(
                    TELA, fonte, 
                    pergunta_atual["pergunta"], 
                    pergunta_atual["opcoes"],
                    AZUL, PRETO, AMARELO, 
                    indice_opcao_com_hover_atual 
                )
            else: 
                retangulos_opcoes_clicaveis_atuais = []

        elif fase == "pergunta_nitro":
            if pergunta_descritiva and "pergunta" in pergunta_descritiva:
                y_pos_nitro_q = ALTURA_PISTA + 30
                texto_q_original = pergunta_descritiva["pergunta"]
                palavras_q = texto_q_original.split(' ')
                linhas_q_renderizadas = []
                linha_atual_q = ""
                max_largura_linha = LARGURA - 60 
                for palavra in palavras_q:
                    palavra_para_adicionar = palavra + " "
                    if fonte.size(linha_atual_q + palavra_para_adicionar)[0] < max_largura_linha:
                        linha_atual_q += palavra_para_adicionar
                    else:
                        linhas_q_renderizadas.append(linha_atual_q.strip())
                        linha_atual_q = palavra_para_adicionar
                linhas_q_renderizadas.append(linha_atual_q.strip())

                for i, linha_q in enumerate(linhas_q_renderizadas):
                    texto_q_surf = fonte.render(linha_q, True, AZUL)
                    TELA.blit(texto_q_surf, (TELA.get_width() // 2 - texto_q_surf.get_width() // 2, y_pos_nitro_q + i * (fonte.get_height() + 2)))
                
                y_pos_nitro_q += len(linhas_q_renderizadas) * (fonte.get_height() + 2) + 15

                if verificando_com_ia_agora:
                    msg_espera_surf = fonte.render("Verificando com IA, aguarde...", True, PRETO)
                    TELA.blit(msg_espera_surf, (TELA.get_width() // 2 - msg_espera_surf.get_width() // 2, y_pos_nitro_q))
                else:
                    input_box_width = LARGURA - 100
                    input_box_rect = pygame.Rect(TELA.get_width() // 2 - input_box_width // 2, y_pos_nitro_q - 5, input_box_width, 40)
                    pygame.draw.rect(TELA, BRANCO, input_box_rect)
                    pygame.draw.rect(TELA, PRETO, input_box_rect, 2)
                    input_render = f"{texto_input_nitro}_"
                    texto_input_surf = fonte_input.render(input_render, True, PRETO)
                    TELA.blit(texto_input_surf, (input_box_rect.x + 10, input_box_rect.y + (input_box_rect.height - texto_input_surf.get_height()) // 2))
                
                y_pos_nitro_q += 40 + 20 
                instr_surf = fonte.render("Pressione Enter para enviar.", True, CINZA) 
                TELA.blit(instr_surf, (TELA.get_width() // 2 - instr_surf.get_width() // 2, y_pos_nitro_q))
            else:
                fallback_surf = fonte.render("Nitro! Erro: Pergunta descritiva não carregada.", True, VERMELHO)
                TELA.blit(fallback_surf, (20, ALTURA_PISTA + 20))
                if semaforo_jogo.acquire(blocking=False):
                    try:
                        if fase == "pergunta_nitro": 
                           fase = "pergunta_multipla"
                           nitro_pego = False 
                    finally:
                        semaforo_jogo.release()
    
    # CORRIGIDO: Este bloco deve estar fora do 'if game_state == "running":'
    elif game_state == "win" or game_state == "lose":
        cor_texto_final = VERMELHO 
        if game_state == "win":
            msg_texto = "Você venceu!"
            cor_texto_final = VERDE
        else: # game_state == "lose"
            if vencedor == "Fim das Perguntas":
                msg_texto = "Você perdeu! Perguntas esgotadas."
            elif vencedor and vencedor != Carro1.nome: 
                msg_texto = f"{vencedor} venceu!"
            else: 
                msg_texto = "Você perdeu!" 
        
        texto_final_surf = grande.render(msg_texto, True, cor_texto_final)
        TELA.blit(texto_final_surf, (LARGURA//2 - texto_final_surf.get_width()//2, ALTURA_PISTA + 70))

    pygame.display.flip()

pygame.quit()