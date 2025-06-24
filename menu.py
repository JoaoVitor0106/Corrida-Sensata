import pygame
from classes import Botao
from constantes import LARGURA, ALTURA, PRETO, CINZA_ESCURO
from funcoes import resource_path

def tela_de_menu(tela, fonte_titulo, fonte_botao):
    # Tenta carregar o fundo do menu. Se não tiver imagem, usa cor sólida.
    try:
        fundo_menu_img = pygame.image.load(resource_path("assets/menu.png")).convert()
        fundo_menu_img = pygame.transform.scale(fundo_menu_img, (LARGURA, ALTURA))
    except pygame.error:
        fundo_menu_img = None

    # Cria botões do menu
    botao_iniciar = Botao(LARGURA // 2, ALTURA // 2 - 50, "Iniciar Jogo", fonte_botao)
    botao_sair = Botao(LARGURA // 2, ALTURA // 2 + 50, "Sair", fonte_botao)
    
    menu_rodando = True
    while menu_rodando:
        # Desenha fundo do menu
        if fundo_menu_img:
            tela.blit(fundo_menu_img, (0, 0))
        else:
            tela.fill(CINZA_ESCURO)
        
        # Desenha o título do jogo
        texto_titulo = fonte_titulo.render("Corrida Sensata", True, PRETO)
        titulo_rect = texto_titulo.get_rect(center=(LARGURA // 2, ALTURA // 4))
        tela.blit(texto_titulo, titulo_rect)

        # Desenha botões e checa se foram clicados
        if botao_iniciar.draw(tela):
            return "JOGANDO"
        
        if botao_sair.draw(tela):
            return "SAIR"

        # Eventos de teclado/fechamento do menu
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "SAIR"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "SAIR"

        pygame.display.update()
