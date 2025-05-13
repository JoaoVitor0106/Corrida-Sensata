import pygame

class Carro(pygame.sprite.Sprite):
    def __init__(self, imagem, posicao):
        super().__init__()
        self.image = pygame.image.load(imagem).convert_alpha()
        self.rect = self.image.get_rect(center = posicao)
        self.image = pygame.transform.scale(self.image, (75, 50))

    def update(self):
        if self.rect.left < 800:
            self.rect.left += 1
        else:
            self.rect.left = -75
pygame.init()
tempo = pygame.time.Clock()

tela = pygame.display.set_mode((800, 700))
pygame.display.set_caption("Corrida Sensata")

pista = pygame.image.load("graphics/pista.png").convert()
pista = pygame.transform.scale(pista, (800, 400))

Carro1 = pygame.sprite.GroupSingle()
Carro1.add(Carro("graphics/carros/carro_vermelho.png", (130, 145)))
Carro2 = pygame.sprite.GroupSingle()
Carro2.add(Carro("graphics/carros/carro_vermelho.png", (130, 145+(1*50))))
Carro3 = pygame.sprite.GroupSingle()
Carro3.add(Carro("graphics/carros/carro_vermelho.png", (130, 145+(2*50))))
Carro4 = pygame.sprite.GroupSingle()
Carro4.add(Carro("graphics/carros/carro_vermelho.png", (130, 145+(3*50+5))))

while True:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            pygame.quit()
            exit()

    tela.blit(pista, (0, 0))

    Carro1.draw(tela)
    Carro1.update()
    Carro2.draw(tela)
    Carro2.update()
    Carro3.draw(tela)
    Carro3.update()
    Carro4.draw(tela)
    Carro4.update()

    pygame.display.update()
    tempo.tick(60)  # Limitar a 60 quadros por segundo
