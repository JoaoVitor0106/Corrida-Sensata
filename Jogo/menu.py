# menu.py
import pygame
from classes import Botao
from constantes import LARGURA, ALTURA, PRETO, CINZA_ESCURO

def tela_de_menu(tela, fonte_titulo, fonte_botao):
    # Carrega e ajusta a imagem de fundo do menu
    try:
        fundo_menu_img = pygame.image.load("assets/menu.png").convert()
        fundo_menu_img = pygame.transform.scale(fundo_menu_img, (LARGURA, ALTURA))
    except pygame.error:
        # Caso a imagem não seja encontrada, usa uma cor sólida
        fundo_menu_img = None

    # Cria os botões
    botao_iniciar = Botao(LARGURA // 2, ALTURA // 2 - 50, "Iniciar Jogo", fonte_botao)
    botao_sair = Botao(LARGURA // 2, ALTURA // 2 + 50, "Sair", fonte_botao)
    
    menu_rodando = True
    while menu_rodando:
        # Desenha o fundo
        if fundo_menu_img:
            tela.blit(fundo_menu_img, (0, 0))
        else:
            tela.fill(CINZA_ESCURO)
        
        # Desenha o título
        texto_titulo = fonte_titulo.render("Corrida Sensata", True, PRETO)
        titulo_rect = texto_titulo.get_rect(center=(LARGURA // 2, ALTURA // 4))
        tela.blit(texto_titulo, titulo_rect)

        # Desenha os botões e verifica se foram clicados
        if botao_iniciar.draw(tela):
            return "JOGANDO" # Retorna o próximo estado do jogo
        
        if botao_sair.draw(tela):
            return "SAIR" # Retorna a instrução para sair

        # Gerenciamento de eventos do menu
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "SAIR"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "SAIR"

        pygame.display.update()
