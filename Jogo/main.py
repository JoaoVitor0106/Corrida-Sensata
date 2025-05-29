#main.py
import pygame
import threading
import time
import json
import random
from constantes import *
from carro import Carro
from funcoes import carregar_e_escalar, desenhar_fundo, render_pergunta, obter_pergunta_disponivel

try:
    with open("perguntas.json", encoding="utf-8") as f:
        dados = json.load(f)
except FileNotFoundError:
    pass 

pygame.init()
TELA = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Corrida Sensata")
fonte = pygame.font.Font(None, 36)
grande = pygame.font.Font(None, 72)
clock = pygame.time.Clock()

pista_img = carregar_e_escalar("assets/pista.png", (800, 400))
nitro_img = carregar_e_escalar("assets/nitro.png", (20, 20))

Carro1 = Carro("assets/carros/Civic.png", (50, 130), "Jogador")
Carro2 = Carro("assets/carros/Supra.png", (50, 180), "Bot1")
Carro3 = Carro("assets/carros/Uno.png", (50, 230), "Bot2")
Carro4 = Carro("assets/carros/Miata.png", (50, 280), "Bot3")
carros = [Carro1, Carro2, Carro3, Carro4]

jogando = True
fase = "pergunta_multipla"
pergunta_atual = None
perguntas_ja_usadas = []
nitro_pos_x = 400
nitro_pego = False
game_state = "running"
semaforo_jogo = threading.Semaphore(1)

retangulos_opcoes_clicaveis_atuais = []
indice_opcao_com_hover_atual = None

# NOVA LÓGICA PARA bots_movimento
def bots_movimento(carro):
    global game_state
    while game_state == "running":
        try:
            # Pausa aleatória para cada bot antes de se mover
            # Isso ajuda a dar a sensação de que estão se movendo em momentos ligeiramente diferentes
            tempo_pausa = random.uniform(0.1, 0.5) # Bots pausam entre 0.1 e 0.5 segundos
            time.sleep(tempo_pausa)
        except Exception: # Se ocorrer um erro na thread (improvável com time.sleep simples)
            break # Sai do loop do bot

        # Verifica novamente o game_state APÓS a pausa, pois o jogo pode ter terminado
        if game_state != "running":
            break

        # Bot se move uma distância aleatória
        # Ajuste os valores min e max para controlar a "habilidade" dos bots
        distancia_movimento = random.randint(2, 7) # Ex: move entre 2 e 7 pixels
        carro.mover(distancia_movimento)

        # Verifica se o bot venceu
        if carro.rect.x > 700:
            # A função game_over já tem um controle para não ser executada múltiplas vezes
            game_over(carro.nome) 
            # Não é estritamente necessário um break aqui, pois a mudança no game_state
            # fará com que o loop while termine na próxima iteração.

def game_over(vencedor):
    global game_state, retangulos_opcoes_clicaveis_atuais
    if game_state == "running": # Esta verificação é crucial
        game_state = "win" if vencedor == "Jogador" else "lose"
        retangulos_opcoes_clicaveis_atuais = []
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            # Corrigido para tocar som de derrota também, se desejar, ou apenas vitória
            if vencedor == "Jogador":
                sound_vitoria = pygame.mixer.Sound('assets/sounds/vitoria.wav')
                sound_vitoria.play()
            # else:
            #     sound_derrota = pygame.mixer.Sound('assets/sounds/derrota.wav') # Exemplo
            #     sound_derrota.play()
        except pygame.error as e:
            print(f"Erro ao tocar som em game_over: {e}") # Adicionado print de erro
            pass

def iniciar_bots():
    for bot_carro in [Carro2, Carro3, Carro4]:
        thread_bot = threading.Thread(target=bots_movimento, args=(bot_carro,), daemon=True)
        thread_bot.start()

iniciar_bots()

while jogando:
    clock.tick(FPS)
    posicao_mouse_frame_atual = pygame.mouse.get_pos()

    indice_opcao_com_hover_atual = None
    if fase == "pergunta_multipla" and pergunta_atual and game_state == "running":
        for i, rect_opcao in enumerate(retangulos_opcoes_clicaveis_atuais):
            if rect_opcao.collidepoint(posicao_mouse_frame_atual):
                indice_opcao_com_hover_atual = i
                break

    desenhar_fundo(TELA, pista_img, nitro_img, nitro_pego, nitro_pos_x, carros)

    if game_state == "running":
        if fase == "pergunta_multipla":
            if not pergunta_atual:
                pergunta_atual = obter_pergunta_disponivel(perguntas_ja_usadas)
                if not pergunta_atual:
                    if game_state == "running": game_over("Jogador")
            
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
            render_pergunta(TELA, fonte, "Nitro Ativado! Pressione Enter para avançar!", [], AZUL, PRETO, AMARELO, None)
            retangulos_opcoes_clicaveis_atuais = []

    elif game_state == "win" or game_state == "lose":
        msg = "Você venceu!" if game_state == "win" else "Você perdeu!"
        texto_final = grande.render(msg, True, VERDE if game_state == "win" else VERMELHO)
        TELA.blit(texto_final, (LARGURA//2 - texto_final.get_width()//2, ALTURA_PISTA + 50))
        retangulos_opcoes_clicaveis_atuais = []

    pygame.display.flip()

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            jogando = False
            game_state = "quit"
        
        elif evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                jogando = False
                game_state = "quit"

            if game_state == "running":
                if fase == "pergunta_nitro" and evento.key == pygame.K_RETURN:
                    if semaforo_jogo.acquire(blocking=False):
                        try:
                            Carro1.mover(MOVE_NITRO)
                            if Carro1.rect.x > 700:
                                if game_state == "running": game_over(Carro1.nome)
                            fase = "pergunta_multipla"
                        finally:
                            semaforo_jogo.release()
                elif fase == "pergunta_multipla" and pergunta_atual:
                    if evento.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]:
                        try:
                            opcao_pelo_teclado = int(evento.unicode) - 1
                            if 0 <= opcao_pelo_teclado < len(pergunta_atual["opcoes"]):
                                if semaforo_jogo.acquire(blocking=False):
                                    try:
                                        if opcao_pelo_teclado == pergunta_atual["resposta"]:
                                            Carro1.mover(MOVE_NORMAL)
                                        
                                        if Carro1.rect.x > 700:
                                            if game_state == "running": game_over(Carro1.nome)
                                        
                                        pergunta_atual = None
                                        retangulos_opcoes_clicaveis_atuais = []
                                    finally:
                                        semaforo_jogo.release()
                        except ValueError:
                            pass

        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if evento.button == 1 and game_state == "running" and \
               fase == "pergunta_multipla" and pergunta_atual:
                
                pos_clique_mouse = evento.pos
                
                for i, rect_opcao_clicavel in enumerate(retangulos_opcoes_clicaveis_atuais):
                    if rect_opcao_clicavel.collidepoint(pos_clique_mouse):
                        if semaforo_jogo.acquire(blocking=False):
                            try:
                                if i == pergunta_atual["resposta"]:
                                    Carro1.mover(MOVE_NORMAL)
                                
                                if Carro1.rect.x > 700:
                                    if game_state == "running": game_over(Carro1.nome)
                                
                                pergunta_atual = None
                                retangulos_opcoes_clicaveis_atuais = []
                            finally:
                                semaforo_jogo.release()
                        break

    nitro_hitbox = pygame.Rect(nitro_pos_x, 130, 20, 20)
    if not nitro_pego and Carro1.rect.colliderect(nitro_hitbox) and game_state == "running":
        nitro_pego = True
        fase = "pergunta_nitro"
        retangulos_opcoes_clicaveis_atuais = []
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            sound_nitro = pygame.mixer.Sound('assets/sounds/nitro.wav')
            sound_nitro.play()
        except pygame.error:
            pass

pygame.quit()