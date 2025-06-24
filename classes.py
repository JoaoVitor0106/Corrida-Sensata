import pygame

class Carro(pygame.sprite.Sprite):
    def __init__(self, imagem, posicao, nome, tamanho=(100, 75)):
        super().__init__()
        self.image = pygame.image.load(imagem).convert_alpha()
        self.image = pygame.transform.scale(self.image, tamanho)
        self.rect = self.image.get_rect(center=posicao)
        self.nome = nome

    def mover(self, velocidade):
        self.rect.x += velocidade

    def draw(self, tela):
        tela.blit(self.image, self.rect)

class Botao:
    def __init__(self, x, y, texto, fonte, cor_texto=(255, 255, 255), cor_fundo=(100, 100, 255), cor_hover=(150, 150, 255)):
        self.texto = texto
        self.fonte = fonte
        self.cor_texto = cor_texto
        self.cor_fundo = cor_fundo
        self.cor_hover = cor_hover
        
        # Prepara texto e botão
        self.imagem_texto = self.fonte.render(self.texto, True, self.cor_texto)
        largura = self.imagem_texto.get_width() + 40
        altura = self.imagem_texto.get_height() + 20
        self.rect = pygame.Rect(x - (largura // 2), y - (altura // 2), largura, altura)
        self.clicado = False

    def draw(self, tela):
        acao = False
        cor_atual = self.cor_fundo
        pos_mouse = pygame.mouse.get_pos()

        # Hover e clique
        if self.rect.collidepoint(pos_mouse):
            cor_atual = self.cor_hover
            if pygame.mouse.get_pressed()[0] == 1 and not self.clicado:
                self.clicado = True
                acao = True

        if pygame.mouse.get_pressed()[0] == 0:
            self.clicado = False

        # Desenha o botão
        pygame.draw.rect(tela, cor_atual, self.rect, border_radius=10)
        texto_rect = self.imagem_texto.get_rect(center=self.rect.center)
        tela.blit(self.imagem_texto, texto_rect)

        return acao
