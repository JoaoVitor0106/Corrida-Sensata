#funcoes.py
import pygame
import json
from constantes import *
import random


try:
    with open("perguntas.json", encoding="utf-8") as f:
        dados = json.load(f)
        perguntas_multipla = dados["multipla_escolha"]
        pergunta_descritiva = dados["descritiva"]
except FileNotFoundError:
    print("Arquivo 'perguntas.json' não encontrado. Crie o arquivo ou verifique o caminho.")
    perguntas_multipla = []
    pergunta_descritiva = []


def carregar_e_escalar(imagem, tamanho):
    img = pygame.image.load(imagem).convert_alpha()
    return pygame.transform.scale(img, tamanho)


def desenhar_fundo(tela, pista_img, nitro_img, nitro_pego, nitro_pos_x, carros):
    tela.fill(BRANCO)
    tela.blit(pista_img, (0, 0))
    if not nitro_pego:
        tela.blit(nitro_img, (nitro_pos_x, 130))

    for carro in carros:
        carro.draw(tela)

    pygame.draw.rect(tela, CINZA, (0, ALTURA_PISTA, LARGURA, ALTURA - ALTURA_PISTA))
    pygame.draw.rect(tela, PRETO, (0, ALTURA_PISTA, LARGURA, ALTURA - ALTURA_PISTA), 3)

def render_pergunta(tela, fonte, texto_da_pergunta, lista_de_opcoes, 
                    cor_texto_pergunta, cor_opcao_normal, cor_opcao_hover, 
                    indice_opcao_com_hover):
    # Desenha a pergunta
    texto_pergunta_surf = fonte.render(texto_da_pergunta, True, cor_texto_pergunta)
    tela.blit(texto_pergunta_surf, (20, ALTURA_PISTA + 20))

    retangulos_das_opcoes_desenhadas = []
    pos_y_da_opcao = ALTURA_PISTA + 60

    for i, texto_da_opcao_atual in enumerate(lista_de_opcoes):
        cor_final_da_opcao = cor_opcao_normal
        if i == indice_opcao_com_hover:
            cor_final_da_opcao = cor_opcao_hover

        opcao_surf = fonte.render(f"{i+1}. {texto_da_opcao_atual}", True, cor_final_da_opcao)

        opcao_rect_desenhado = tela.blit(opcao_surf, (20, pos_y_da_opcao))
        retangulos_das_opcoes_desenhadas.append(opcao_rect_desenhado)
        
        pos_y_da_opcao += fonte.get_height() + 10

    return retangulos_das_opcoes_desenhadas


def obter_pergunta_disponivel(perguntas_ja_usadas):
    disponiveis = [p for p in perguntas_multipla if p.get("id") not in perguntas_ja_usadas]
    if disponiveis:
        pergunta_escolhida = random.choice(disponiveis)
        if "id" in pergunta_escolhida:
            perguntas_ja_usadas.append(pergunta_escolhida["id"])
        return pergunta_escolhida
    return None