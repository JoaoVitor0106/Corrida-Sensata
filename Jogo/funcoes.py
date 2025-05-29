import pygame
import json
from constantes import *
import random
with open("perguntas.json", encoding="utf-8") as f:
    dados = json.load(f)
    perguntas_multipla = dados["multipla_escolha"]
    pergunta_descritiva = dados["descritiva"]

def carregar_e_escalar(imagem, tamanho):
    img = pygame.image.load(imagem).convert_alpha()
    return pygame.transform.scale(img, tamanho)

def desenhar_fundo(tela, pista_img, chegada_img, nitro_img, nitro_pego, nitro_pos, carros):
    tela.fill(BRANCO)
    tela.blit(pista_img, (0, 0))
    tela.blit(chegada_img, (700, 85))
    if not nitro_pego:
        tela.blit(nitro_img, (nitro_pos, 130))

    for carro in carros:
        carro.draw(tela)

    pygame.draw.rect(tela, CINZA, (0, ALTURA_PISTA, LARGURA, ALTURA - ALTURA_PISTA))
    pygame.draw.rect(tela, PRETO, (0, ALTURA_PISTA, LARGURA, ALTURA - ALTURA_PISTA), 3)

def render_pergunta(tela, fonte, pergunta, opcoes, cor):
    texto = fonte.render(pergunta, True, cor)
    tela.blit(texto, (20, ALTURA_PISTA + 20))
    for i, opcao in enumerate(opcoes):
        opcao_txt = fonte.render(f"{i+1}. {opcao}", True, PRETO)
        tela.blit(opcao_txt, (20, ALTURA_PISTA + 60 + i * 30))

def obter_pergunta_disponivel(perguntas_ja_usadas):
    disponiveis = [p for p in perguntas_multipla if p["id"] not in perguntas_ja_usadas]
    if disponiveis:
        pergunta = random.choice(disponiveis)
        perguntas_ja_usadas.append(pergunta["id"])
        return pergunta
    return None
