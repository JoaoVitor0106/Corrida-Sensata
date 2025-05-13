import pygame

pygame.init()
tempo = pygame.time.Clock()

tela = pygame.display.set_mode((800, 400))
pygame.display.set_caption("Corrida Sensata")

pista = pygame.image.load("graphics/pista.png").convert()
pista = pygame.transform.scale(pista, (800, 400))

carro = pygame.image.load("graphics/carros/carro_vermelho.png").convert_alpha()
carro_rect = carro.get_rect(center = (130, 145))
carro = pygame.transform.scale(carro, (75, 50))

while True:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            pygame.quit()
            exit()

    tela.blit(pista, (0, 0))

    if carro_rect.left < 800:
        carro_rect.left += 1
    else:
        carro_rect.left = -75
    tela.blit(carro,carro_rect)

    pygame.display.update()
    tempo.tick(60)  # Limitar a 60 quadros por segundo
