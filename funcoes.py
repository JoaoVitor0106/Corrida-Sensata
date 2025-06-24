import pygame
import json
import random
import unicodedata
import os
import sys
from constantes import *

# Garante que o jogo funcione mesmo quando for empacotado com PyInstaller
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # Usado por PyInstaller
    except Exception:
        base_path = os.path.abspath(".")  # Caminho padrão
    return os.path.join(base_path, relative_path)

# Carrega e redimensiona uma imagem
def carregar_e_escalar(imagem, tamanho):
    img = pygame.image.load(resource_path(imagem)).convert_alpha()
    return pygame.transform.scale(img, tamanho)

# Desenha fundo da pista, obstáculos e os carros
def desenhar_fundo(tela, pista_img, obstaculo_img, obstaculos_ativos, carros):
    tela.fill(BRANCO)
    tela.blit(pista_img, (0, 0))
    
    for obstaculo in obstaculos_ativos:
        if obstaculo["ativo"]:
            tela.blit(obstaculo_img, (obstaculo["pos_x"], 130))

    for carro in carros:
        carro.draw(tela)

    pygame.draw.rect(tela, CINZA, (0, ALTURA_PISTA, LARGURA, ALTURA - ALTURA_PISTA))
    pygame.draw.rect(tela, PRETO, (0, ALTURA_PISTA, LARGURA, ALTURA - ALTURA_PISTA), 3)

# Exibe uma pergunta de múltipla escolha e destaca a opção com hover
def render_pergunta(tela, fonte, texto_da_pergunta, lista_de_opcoes,
                    cor_texto_pergunta, cor_opcao_normal, cor_opcao_hover,
                    indice_opcao_com_hover):
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

# Escolhe uma pergunta ainda não usada
def obter_pergunta_disponivel(perguntas_multipla, perguntas_ja_usadas):
    disponiveis = [p for p in perguntas_multipla if p.get("id") not in perguntas_ja_usadas]
    if disponiveis:
        pergunta_escolhida = random.choice(disponiveis)
        if "id" in pergunta_escolhida:
            perguntas_ja_usadas.append(pergunta_escolhida["id"])
        return pergunta_escolhida
    return None

# Carrega perguntas do JSON
try:
    with open(resource_path("perguntas.json"), encoding="utf-8") as f:
        dados = json.load(f)
        perguntas_multipla = dados.get("multipla_escolha", [])
        pergunta_descritiva = dados.get("descritiva", [])
except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f"ERRO ao carregar 'perguntas.json': {e}. O jogo pode não funcionar corretamente.")
    perguntas_multipla = []
    pergunta_descritiva = []

# Remove acentos de um texto
def remover_acentos(texto):
    if texto is None: return ""
    try:
        nfkd_form = unicodedata.normalize('NFKD', str(texto))
        return "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    except TypeError:
        return str(texto)

# Quebra um texto longo em várias linhas, sem ultrapassar o limite de largura
def quebrar_texto_em_linhas(texto, largura_maxima, fonte):
    linhas_finais = []
    palavras = texto.split(' ')
    linha_atual = ""

    for palavra in palavras:
        linha_teste = linha_atual + palavra + " "
        if fonte.size(linha_teste)[0] <= largura_maxima:
            linha_atual = linha_teste
        else:
            linhas_finais.append(linha_atual.strip())
            linha_atual = palavra + " "
    
    linhas_finais.append(linha_atual.strip())

    return linhas_finais
