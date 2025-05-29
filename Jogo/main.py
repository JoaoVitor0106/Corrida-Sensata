import pygame
import threading
import time
import json
from constantes import *
from carro import Carro
from funcoes import carregar_e_escalar, desenhar_fundo, render_pergunta, obter_pergunta_disponivel
with open("perguntas.json", encoding="utf-8") as f:
    dados = json.load(f)
    perguntas_multipla = dados["multipla_escolha"]
    pergunta_descritiva = dados["descritiva"]

pygame.init()
TELA = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Corrida Sensata")
fonte = pygame.font.Font(None, 36)
grande = pygame.font.Font(None, 72)
clock = pygame.time.Clock()

# Carregamento de imagens
pista_img = carregar_e_escalar("assets/pista.png", (800, 200))
chegada_img = carregar_e_escalar("assets/chegada.png", (50, 100))
nitro_img = carregar_e_escalar("assets/nitro.png", (20, 20))

# Carros
Carro1 = Carro("assets/Civic.png", (50, 100), "Jogador")
Carro2 = Carro("assets/Supra.png", (50, 150), "Bot1")
Carro3 = Carro("assets/Uno.png", (50, 200), "Bot2")
Carro4 = Carro("assets/Miata.png", (50, 250), "Bot3")
carros = [Carro1, Carro2, Carro3, Carro4]

# Controle de jogo
jogando = True
fase = "pergunta_multipla"
pergunta_atual = None
opcao_selecionada = None
perguntas_ja_usadas = []
nitro_pos = 400
nitro_pego = False
game_state = "running"
semaforo_jogo = threading.Semaphore(1)

def bots_movimento(carro):
    global game_state
    while game_state == "running":
        if semaforo_jogo.acquire(blocking=False):
            try:
                time.sleep(0.5)
                carro.mover(10)
                if carro.rect.x > 700:
                    game_over(carro.nome)
            finally:
                semaforo_jogo.release()

def game_over(vencedor):
    global game_state
    game_state = "win" if vencedor == "Jogador" else "lose"
    pygame.mixer.Sound('assets/sounds/vitoria.wav').play()

def iniciar_bots():
    for bot in [Carro2, Carro3, Carro4]:
        threading.Thread(target=bots_movimento, args=(bot,), daemon=True).start()

iniciar_bots()

while jogando:
    clock.tick(FPS)
    desenhar_fundo(TELA, pista_img, chegada_img, nitro_img, nitro_pego, nitro_pos, carros)

    if game_state == "running":
        if fase == "pergunta_multipla":
            if not pergunta_atual:
                pergunta_atual = obter_pergunta_disponivel(perguntas_ja_usadas)
                if not pergunta_atual:
                    game_over("Jogador")
            if pergunta_atual:
                render_pergunta(TELA, fonte, pergunta_atual["pergunta"], pergunta_atual["opcoes"], AZUL)
        else:
            render_pergunta(TELA, fonte, "Digite sua resposta descritiva:", ["(Digite e pressione Enter)"], AZUL)
    else:
        msg = "Você venceu!" if game_state == "win" else "Você perdeu!"
        texto = grande.render(msg, True, VERDE if game_state == "win" else VERMELHO)
        TELA.blit(texto, (LARGURA//2 - texto.get_width()//2, ALTURA_PISTA + 50))

    pygame.display.flip()

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            jogando = False
        elif evento.type == pygame.KEYDOWN and game_state == "running":
            if fase == "pergunta_multipla":
                if evento.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]:
                    opcao = int(evento.unicode) - 1
                    if semaforo_jogo.acquire(blocking=False):
                        try:
                            if opcao == pergunta_atual["resposta"]:
                                Carro1.mover(10)
                                if Carro1.rect.x > 700:
                                    game_over(Carro1.nome)
                            pergunta_atual = None
                        finally:
                            semaforo_jogo.release()
            else:
                if evento.key == pygame.K_RETURN:
                    Carro1.mover(15)
                    fase = "pergunta_multipla"

    if not nitro_pego and Carro1.rect.colliderect(pygame.Rect(nitro_pos, 130, 20, 20)):
        nitro_pego = True
        fase = "pergunta_nitro"
        pygame.mixer.Sound('assets/sounds/nitro.wav').play()

pygame.quit()
