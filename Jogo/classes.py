#classes.py
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
    """
    Uma classe para criar botões de UI clicáveis e com efeito de hover.
    """
    def __init__(self, x, y, texto, fonte, cor_texto=(255, 255, 255), cor_fundo=(100, 100, 255), cor_hover=(150, 150, 255)):
        """
        Inicializa o botão.
        Args:
            x (int): Posição X do centro do botão.
            y (int): Posição Y do centro do botão.
            texto (str): O texto que aparecerá no botão.
            fonte (pygame.font.Font): O objeto de fonte para renderizar o texto.
            cor_texto (tuple): Cor do texto em RGB.
            cor_fundo (tuple): Cor de fundo normal do botão em RGB.
            cor_hover (tuple): Cor de fundo quando o mouse está sobre o botão em RGB.
        """
        self.texto = texto
        self.fonte = fonte
        self.cor_texto = cor_texto
        self.cor_fundo = cor_fundo
        self.cor_hover = cor_hover
        
        # Renderiza o texto uma vez para obter as dimensões
        self.imagem_texto = self.fonte.render(self.texto, True, self.cor_texto)
        
        # Define as dimensões do retângulo do botão com um preenchimento
        largura = self.imagem_texto.get_width() + 40
        altura = self.imagem_texto.get_height() + 20
        
        # Cria o retângulo do botão, centralizado nas coordenadas x, y
        self.rect = pygame.Rect(x - (largura // 2), y - (altura // 2), largura, altura)
        
        # Flag para garantir que o clique seja registrado apenas uma vez
        self.clicado = False

    def draw(self, tela):
        """
        Desenha o botão na tela e verifica interações do mouse.
        Args:
            tela (pygame.Surface): A superfície da tela onde o botão será desenhado.
        Returns:
            bool: True se o botão foi clicado nesta frame, False caso contrário.
        """
        acao = False
        cor_atual = self.cor_fundo
        pos_mouse = pygame.mouse.get_pos()

        # 1. Verifica se o mouse está sobre o botão (hover)
        if self.rect.collidepoint(pos_mouse):
            cor_atual = self.cor_hover
            
            # 2. Verifica se o botão foi clicado (apenas no momento do clique)
            if pygame.mouse.get_pressed()[0] == 1 and not self.clicado:
                self.clicado = True
                acao = True
        
        # 3. Reseta o estado do clique se o botão do mouse for solto
        if pygame.mouse.get_pressed()[0] == 0:
            self.clicado = False

        # 4. Desenha o botão
        # Desenha o retângulo de fundo com bordas arredondadas
        pygame.draw.rect(tela, cor_atual, self.rect, border_radius=10)
        
        # Centraliza e desenha o texto sobre o retângulo
        texto_rect = self.imagem_texto.get_rect(center=self.rect.center)
        tela.blit(self.imagem_texto, texto_rect)

        return acao