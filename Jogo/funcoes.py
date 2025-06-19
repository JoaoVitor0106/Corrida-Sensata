# --- IMPORTAÇÕES ---
import pygame
import json
import random
import unicodedata  # Usado para remover acentos dos textos (para análise de IA ou padronização)
from constantes import *  # Importa constantes como cores, larguras e alturas definidas globalmente

# --- FUNÇÃO: Carrega uma imagem e redimensiona para o tamanho desejado ---
def carregar_e_escalar(imagem, tamanho):
    img = pygame.image.load(imagem).convert_alpha()  # Carrega com canal alpha (transparência)
    return pygame.transform.scale(img, tamanho)      # Redimensiona a imagem para o tamanho informado

# --- FUNÇÃO: Desenha o fundo da tela durante o jogo ---
def desenhar_fundo(tela, pista_img, obstaculo_img, obstaculo_pego, obstaculo_pos_x, carros):
    tela.fill(BRANCO)  # Pinta o fundo da tela de branco
    tela.blit(pista_img, (0, 0))  # Desenha a imagem da pista no topo

    # Se o obstáculo ainda não foi pego, desenha-o na tela
    if not obstaculo_pego:
        tela.blit(obstaculo_img, (obstaculo_pos_x, 130))

    # Desenha cada carro na tela
    for carro in carros:
        carro.draw(tela)

    # Área inferior (onde aparecem as perguntas e respostas)
    pygame.draw.rect(tela, CINZA, (0, ALTURA_PISTA, LARGURA, ALTURA - ALTURA_PISTA))  # Área cinza
    pygame.draw.rect(tela, PRETO, (0, ALTURA_PISTA, LARGURA, ALTURA - ALTURA_PISTA), 3)  # Borda preta

# --- FUNÇÃO: Renderiza uma pergunta de múltipla escolha e suas opções ---
def render_pergunta(tela, fonte, texto_da_pergunta, lista_de_opcoes,
                    cor_texto_pergunta, cor_opcao_normal, cor_opcao_hover,
                    indice_opcao_com_hover):
    # Renderiza o texto da pergunta
    texto_pergunta_surf = fonte.render(texto_da_pergunta, True, cor_texto_pergunta)
    tela.blit(texto_pergunta_surf, (20, ALTURA_PISTA + 20))

    retangulos_das_opcoes_desenhadas = []
    pos_y_da_opcao = ALTURA_PISTA + 60  # Começa abaixo da pergunta

    # Renderiza cada opção
    for i, texto_da_opcao_atual in enumerate(lista_de_opcoes):
        cor_final_da_opcao = cor_opcao_normal
        if i == indice_opcao_com_hover:
            cor_final_da_opcao = cor_opcao_hover  # Destaca a opção sob o cursor

        opcao_surf = fonte.render(f"{i+1}. {texto_da_opcao_atual}", True, cor_final_da_opcao)
        opcao_rect_desenhado = tela.blit(opcao_surf, (20, pos_y_da_opcao))
        retangulos_das_opcoes_desenhadas.append(opcao_rect_desenhado)
        pos_y_da_opcao += fonte.get_height() + 10  # Espaçamento entre opções

    return retangulos_das_opcoes_desenhadas  # Retorna os retângulos para detectar clique

# --- FUNÇÃO: Seleciona uma pergunta que ainda não foi usada ---
def obter_pergunta_disponivel(perguntas_multipla, perguntas_ja_usadas):
    # Filtra perguntas que ainda não foram usadas com base no ID
    disponiveis = [p for p in perguntas_multipla if p.get("id") not in perguntas_ja_usadas]
    if disponiveis:
        pergunta_escolhida = random.choice(disponiveis)
        if "id" in pergunta_escolhida:
            perguntas_ja_usadas.append(pergunta_escolhida["id"])  # Marca como usada
        return pergunta_escolhida
    return None  # Retorna None se todas foram usadas

# --- BLOCO DE CARREGAMENTO DAS PERGUNTAS DO ARQUIVO JSON ---
try:
    with open("perguntas.json", encoding="utf-8") as f:
        dados = json.load(f)  # Carrega o conteúdo do arquivo
        perguntas_multipla = dados.get("multipla_escolha", [])  # Lista de perguntas de múltipla escolha
        pergunta_descritiva = dados.get("descritiva", [])        # Lista de perguntas descritivas
except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f"ERRO ao carregar 'perguntas.json': {e}. O jogo pode não funcionar corretamente.")
    perguntas_multipla = []
    pergunta_descritiva = []

# --- FUNÇÃO: Remove acentos de um texto ---
def remover_acentos(texto):
    if texto is None:
        return ""
    try:
        nfkd_form = unicodedata.normalize('NFKD', str(texto))  # Normaliza para decompor acentos
        return "".join([c for c in nfkd_form if not unicodedata.combining(c)])  # Remove acentos
    except TypeError:
        return str(texto)

# --- FUNÇÃO: Quebra textos longos em várias linhas para caber na tela ---
def quebrar_texto_em_linhas(texto, largura_maxima, fonte):
    """
    Divide o texto em várias linhas que se encaixam na largura máxima da tela,
    respeitando os limites da fonte usada.
    """
    linhas_finais = []
    palavras = texto.split(' ')  # Separa em palavras
    linha_atual = ""

    for palavra in palavras:
        linha_teste = linha_atual + palavra + " "
        if fonte.size(linha_teste)[0] <= largura_maxima:
            linha_atual = linha_teste  # Cabe na linha atual
        else:
            linhas_finais.append(linha_atual.strip())  # Adiciona linha e começa nova
            linha_atual = palavra + " "

    linhas_finais.append(linha_atual.strip())  # Última linha

    return linhas_finais
