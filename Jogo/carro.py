#carro.py
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