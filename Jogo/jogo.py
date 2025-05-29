import pygame
import random
import threading
import time
import difflib
from threading import Semaphore # Importa a classe Semaphore

# Inicializa o pygame
perguntas_ja_usadas = []
pygame.init()

# Tela
LARGURA, ALTURA = 800, 600
ALTURA_PISTA = 350
TELA = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Corrida Sensata")

# Cores
BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)
CINZA = (200, 200, 200)
AMARELO = (255, 255, 0)
VERDE = (0, 200, 0) # Cor para o botão
VERMELHO = (200, 0, 0) # Cor para o botão

# Fontes
fonte = pygame.font.SysFont("arial", 20)
grande = pygame.font.SysFont("arial", 26, bold=True)
# Semaforo para controlar acesso a seções críticas (perguntas e vitória)
# Valor inicial de 1 significa que apenas uma thread pode adquirir o semáforo por vez (mutex)
semaforo_jogo = Semaphore(1)

# Classe Carro com imagem
class Carro(pygame.sprite.Sprite):
    def __init__(self, imagem, posicao, nome): # Adiciona 'nome' para identificar o carro
        super().__init__()
        self.image = pygame.image.load(imagem).convert_alpha()
        self.image = pygame.transform.scale(self.image, (75, 50))
        self.rect = self.image.get_rect(center=posicao)
        self.nome = nome # Armazena o nome do carro

    def update(self):
        pass  # Sem movimento automático

# --- Variáveis Globais de Jogo ---
# Instanciar os carros (GroupSingle) - serão redefinidos ao reiniciar
Carro1 = pygame.sprite.GroupSingle()
Carro2 = pygame.sprite.GroupSingle()
Carro3 = pygame.sprite.GroupSingle()
Carro4 = pygame.sprite.GroupSingle()

# Variáveis de estado do jogo
nitro_pos = random.randint(100, 700)
nitro_pego = False
pergunta_atual = None
resposta_usuario = ""
todas_perguntas_respondidas = False
vencedor = None
fase = "corrida"
game_state = "running" # "running" | "win" | "game_over"

# Movimento dos bots - MOVIDO PARA CIMA
def bots_movimento(grupo_carro):
    global fase, vencedor, game_state # Acessa as variáveis globais
    while grupo_carro.sprite.rect.left < 700:
        if game_state != "running": # Se o jogo não está rodando, os bots param
            break

        # Verifica se já há um vencedor para parar o bot
        if vencedor is not None:
            break

        # Bots tentam adquirir o semáforo antes de avançar para a linha de chegada
        if semaforo_jogo.acquire(blocking=False): # Tenta adquirir, não trava
            try:
                grupo_carro.sprite.rect.left += random.randint(1, 3)
                if grupo_carro.sprite.rect.left >= 700 and vencedor is None:
                    vencedor = grupo_carro.sprite.nome
                    print(f"\n🏁 {vencedor} venceu a Corrida Sensata!")
                    if vencedor != "Jogador": # Se um bot vence, é Game Over para o jogador
                        game_state = "game_over"
                    else:
                        game_state = "win" # Se o jogador vence, é vitória
                    return # Encerra a thread do bot assim que vence
            finally:
                semaforo_jogo.release() # Sempre libera o semáforo
        time.sleep(random.uniform(0.1, 0.3)) # Intervalo menor para bots parecerem mais rápidos


def resetar_jogo():
    global Carro1, Carro2, Carro3, Carro4, nitro_pos, nitro_pego, perguntas_ja_usadas, fase, pergunta_atual, resposta_usuario, todas_perguntas_respondidas, vencedor, game_state

    # Reinicializa os carros
    Carro1 = pygame.sprite.GroupSingle()
    Carro1.add(Carro("graphics/carros/carro_vermelho.png", (130, 145), "Jogador"))

    Carro2 = pygame.sprite.GroupSingle()
    Carro2.add(Carro("graphics/carros/carro_vermelho.png", (130, 195), "Bot 1"))

    Carro3 = pygame.sprite.GroupSingle()
    Carro3.add(Carro("graphics/carros/carro_vermelho.png", (130, 245), "Bot 2"))

    Carro4 = pygame.sprite.GroupSingle()
    Carro4.add(Carro("graphics/carros/carro_vermelho.png", (130, 295), "Bot 3"))

    # Reinicializa o nitro
    nitro_pos = random.randint(100, 700)
    nitro_pego = False

    # Reinicializa as perguntas
    perguntas_ja_usadas.clear()
    pergunta_atual = None
    resposta_usuario = ""
    todas_perguntas_respondidas = False

    # Reinicializa os estados do jogo
    fase = "corrida"
    vencedor = None
    game_state = "running" # Volta para o estado de jogo rodando

    # Reinicia as threads dos bots
    # É fundamental iniciar as threads *APÓS* recriar os objetos Carro
    threading.Thread(target=bots_movimento, args=(Carro2,), daemon=True).start()
    threading.Thread(target=bots_movimento, args=(Carro3,), daemon=True).start()
    threading.Thread(target=bots_movimento, args=(Carro4,), daemon=True).start()

# Chamada inicial para configurar o jogo e iniciar as threads dos bots
resetar_jogo()

# Perguntas (lista permanece inalterada)
perguntas_multipla = [
    {
        "id": 1,
        "pergunta": "Qual a capital da França?",
        "opcoes": ["Berlim", "Madri", "Paris", "Lisboa"],
        "resposta": 2  # índice da resposta correta
    },
    {
        "id": 2,
        "pergunta": "Quem descobriu o Brasil?",
        "opcoes": ["Dom Pedro I", "Pedro Álvares Cabral", "Tiradentes", "Machado de Assis"],
        "resposta": 1
    },
    {
        "id": 3,
        "pergunta": "Qual é o resultado de 7 x 8?",
        "opcoes": ["54", "56", "64", "58"],
        "resposta": 1
    },
    {
        "id": 4,
        "pergunta": "Qual elemento químico tem o símbolo O?",
        "opcoes": ["Ouro", "Oxigênio", "Osmium", "Óxido"],
        "resposta": 1
    },
    {
        "id": 5,
        "pergunta": "Qual oceano banha a costa leste do Brasil?",
        "opcoes": ["Oceano Pacífico", "Oceano Atlântico", "Oceano Índico", "Oceano Ártico"],
        "resposta": 1
    },
    {
        "id": 6,
        "pergunta": "Quantos continentes existem no mundo?",
        "opcoes": ["4", "5", "6", "7"],
        "resposta": 3
    },
    {
        "id": 7,
        "pergunta": "Qual o maior animal terrestre?",
        "opcoes": ["Girafa", "Elefante Africano", "Rinoceronte", "Hipopamo"],
        "resposta": 1
    },
    {
        "id": 8,
        "pergunta": "Quem pintou a Mona Lisa?",
        "opcoes": ["Pablo Picasso", "Vincent van Gogh", "Leonardo da Vinci", "Claude Monet"],
        "resposta": 2
    },
    {
        "id": 9,
        "pergunta": "Qual é o maior planeta do nosso sistema solar?",
        "opcoes": ["Marte", "Júpiter", "Saturno", "Terra"],
        "resposta": 1
    },
    {
        "id": 10,
        "pergunta": "Quem escreveu 'Dom Quixote'?",
        "opcoes": ["William Shakespeare", "Miguel de Cervantes", "Machado de Assis", "Gabriel García Márquez"],
        "resposta": 1
    },
    {
        "id": 11,
        "pergunta": "Qual gás as plantas absorvem para fazer fotossíntese?",
        "opcoes": ["Oxigênio", "Nitrogênio", "Dióxido de Carbono", "Hidrogênio"],
        "resposta": 2
    },
    {
        "id": 12,
        "pergunta": "Qual é a capital da Argentina?",
        "opcoes": ["Santiago", "Montevidéu", "Bogotá", "Buenos Aires"],
        "resposta": 3
    },
    {
        "id": 13,
        "pergunta": "Em que ano o homem pisou na lua pela primeira vez?",
        "opcoes": ["1965", "1969", "1972", "1959"],
        "resposta": 1
    },
    {
        "id": 14,
        "pergunta": "Qual destes animais é um mamífero marinho?",
        "opcoes": ["Tubarão", "Orca", "Salmão", "Enguia"],
        "resposta": 1
    },
    {
        "id": 15,
        "pergunta": "Qual o componente principal do vidro?",
        "opcoes": ["Ferro", "Areia", "Plástico", "Alumínio"],
        "resposta": 1
    },
    {
        "id": 16,
        "pergunta": "Qual a montanha mais alta do mundo?",
        "opcoes": ["K2", "Monte Everest", "Monte Fuji", "Monte Kilimanjaro"],
        "resposta": 1
    },
    {
        "id": 17,
        "pergunta": "Qual o maior rio do mundo em volume de água?",
        "opcoes": ["Rio Nilo", "Rio Amazonas", "Rio Mississipi", "Rio Yangtzé"],
        "resposta": 1
    },
    {
        "id": 18,
        "pergunta": "Qual país tem o maior número de pirâmides?",
        "opcoes": ["Egito", "Sudão", "México", "China"],
        "resposta": 1
    },
    {
        "id": 19,
        "pergunta": "Qual o menor país do mundo?",
        "opcoes": ["Mônaco", "Vaticano", "Nauru", "San Marino"],
        "resposta": 1
    },
    {
        "id": 20,
        "pergunta": "Qual animal é conhecido por ter 8 braços?",
        "opcoes": ["Estrela do Mar", "Lula", "Polvo", "Medusa"],
        "resposta": 2
    },
    {
        "id": 21,
        "pergunta": "Qual o nome do primeiro homem a viajar para o espaço?",
        "opcoes": ["Neil Armstrong", "Buzz Aldrin", "Yuri Gagarin", "Valentina Tereshkova"],
        "resposta": 2
    },
    {
        "id": 22,
        "pergunta": "Qual é a língua mais falada no mundo?",
        "opcoes": ["Inglês", "Espanhol", "Mandarim", "Hindi"],
        "resposta": 2
    },
    {
        "id": 23,
        "pergunta": "Qual é o nome do criador da Microsoft?",
        "opcoes": ["Steve Jobs", "Mark Zuckerberg", "Bill Gates", "Elon Musk"],
        "resposta": 2
    },
    {
        "id": 24,
        "pergunta": "Qual instrumento musical tem cordas e é tocado com um arco?",
        "opcoes": ["Guitarra", "Violino", "Piano", "Flauta"],
        "resposta": 1
    },
    {
        "id": 25,
        "pergunta": "Qual o maior deserto do mundo?",
        "opcoes": ["Deserto do Saara", "Deserto da Arábia", "Deserto de Gobi", "Deserto da Antártida"],
        "resposta": 3
    }
]

pergunta_descritiva = {
    "pergunta": "O que causa o fenômeno das marés?",
    "resposta_certa": "A atração gravitacional da Lua e do Sol sobre a Terra."
}

# Função de comparação de texto
def comparar_texto(r1, r2):
    return difflib.SequenceMatcher(None, r1.lower(), r2.lower()).ratio() >= 0.6

# Funções de desenho
def desenhar():
    TELA.fill(BRANCO)

    # Pista
    pista = pygame.image.load("graphics/pista.png").convert()
    pista = pygame.transform.scale(pista, (800, 400))
    TELA.blit(pista, (0, 0))

    # Linha de chegada (agora uma imagem)
    chegada_img = pygame.image.load("graphics/chegada.jpg").convert_alpha() # Carrega a imagem
    # Redimensiona a imagem para ter a largura da linha antiga (5px) e a altura da pista
    chegada_img = pygame.transform.scale(chegada_img, (20, ALTURA_PISTA))
    TELA.blit(chegada_img, (700, 85)) # Desenha a imagem na posição da linha de chegada

    # Nitro
    if not nitro_pego:
        # Posição Y ajustada para o meio da pista para que o nitro apareça na linha dos carros
        pygame.draw.rect(TELA, AMARELO, (nitro_pos, 130, 20, 20))

    # Desenhar os carros
    Carro1.draw(TELA)
    Carro2.draw(TELA)
    Carro3.draw(TELA)
    Carro4.draw(TELA)

    # Caixa de diálogo
    pygame.draw.rect(TELA, CINZA, (0, ALTURA_PISTA, LARGURA, ALTURA - ALTURA_PISTA))
    pygame.draw.rect(TELA, PRETO, (0, ALTURA_PISTA, LARGURA, ALTURA - ALTURA_PISTA), 3)

    if game_state == "running":
        if fase == "pergunta_multipla":
            render_pergunta_multipla()
        elif fase == "pergunta_nitro":
            render_pergunta_nitro()
    elif game_state == "win":
        render_fim_de_jogo("Você Venceu!", VERDE)
    elif game_state == "game_over":
        render_fim_de_jogo("Game Over!", VERMELHO)


    pygame.display.flip()

def render_pergunta_multipla():
    texto = pergunta_atual["pergunta"]
    TELA.blit(grande.render(texto, True, PRETO), (40, ALTURA_PISTA + 20))
    for i, op in enumerate(pergunta_atual["opcoes"]):
        pygame.draw.rect(TELA, BRANCO, (60, ALTURA_PISTA + 60 + i * 40, 680, 30))
        pygame.draw.rect(TELA, PRETO, (60, ALTURA_PISTA + 60 + i * 40, 680, 30), 2)
        TELA.blit(fonte.render(f"{i + 1}) {op}", True, PRETO), (70, ALTURA_PISTA + 65 + i * 40))

def render_pergunta_nitro():
    TELA.blit(grande.render(pergunta_descritiva["pergunta"], True, PRETO), (40, ALTURA_PISTA + 20))
    pygame.draw.rect(TELA, BRANCO, (60, ALTURA_PISTA + 70, 680, 30))
    pygame.draw.rect(TELA, PRETO, (60, ALTURA_PISTA + 70, 680, 30), 2)
    TELA.blit(fonte.render(resposta_usuario, True, PRETO), (70, ALTURA_PISTA + 75))

def render_fim_de_jogo(mensagem, cor_mensagem):
    texto_status = grande.render(mensagem, True, cor_mensagem)
    texto_rect = texto_status.get_rect(center=(LARGURA // 2, ALTURA_PISTA + 80))
    TELA.blit(texto_status, texto_rect)

    # Botão Tente Novamente
    button_color = (100, 100, 255) # Azul para o botão
    button_text = fonte.render("Tente Novamente", True, BRANCO)
    button_rect = pygame.Rect(LARGURA // 2 - 100, ALTURA_PISTA + 150, 200, 50)
    pygame.draw.rect(TELA, button_color, button_rect)
    pygame.draw.rect(TELA, PRETO, button_rect, 2)
    TELA.blit(button_text, button_text.get_rect(center=button_rect.center))
    return button_rect # Retorna o rect do botão para detecção de clique

# Loop principal
clock = pygame.time.Clock()
jogando = True

while jogando:
    desenhar()

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            jogando = False

        if game_state == "running": # Só processa entradas do jogo se o jogo estiver rodando
            if evento.type == pygame.KEYDOWN:
                if fase == "pergunta_nitro":
                    if evento.key == pygame.K_RETURN:
                        # Adquire o semáforo antes de processar a resposta do nitro
                        if semaforo_jogo.acquire(blocking=False): # Tenta adquirir, não trava
                            try:
                                if comparar_texto(resposta_usuario, pergunta_descritiva["resposta_certa"]):
                                    print("✅ Resposta correta! Nitro ativado.")
                                    Carro1.sprite.rect.left += 100
                                else:
                                    print("❌ Resposta incorreta para o nitro.")
                                fase = "corrida"
                                resposta_usuario = ""
                            finally:
                                semaforo_jogo.release() # Libera o semáforo
                        else:
                            # Mensagem de depuração para o jogador se o recurso estiver ocupado
                            print("🚫 Recurso de pergunta de nitro ocupado. Tente novamente.")
                    elif evento.key == pygame.K_BACKSPACE:
                        resposta_usuario = resposta_usuario[:-1]
                    else:
                        resposta_usuario += evento.unicode

            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if fase == "pergunta_multipla":
                    x, y = evento.pos
                    for i in range(4):
                        rect = pygame.Rect(60, ALTURA_PISTA + 60 + i * 40, 680, 30)
                        if rect.collidepoint(x, y):
                            # Adquire o semáforo antes de processar a resposta de múltipla escolha
                            if semaforo_jogo.acquire(blocking=False): # Tenta adquirir, não trava
                                try:
                                    if i == pergunta_atual["resposta"]:
                                        print("✅ Resposta correta!")
                                        Carro1.sprite.rect.left += 50
                                    else:
                                        print("❌ Resposta incorreta.")
                                    fase = "corrida"
                                    break # Sai do loop for após responder
                                finally:
                                    semaforo_jogo.release() # Libera o semáforo
                            else:
                                # Mensagem de depuração para o jogador se o recurso estiver ocupado
                                print("🚫 Recurso de pergunta ocupado. Tente novamente.")
                            break # Sai do loop for mesmo se não adquiriu o semáforo para evitar múltiplos cliques
        else: # Se o jogo não está rodando (game_state é "win" ou "game_over")
            if evento.type == pygame.MOUSEBUTTONDOWN:
                x, y = evento.pos
                # Desenha o botão "Tente Novamente" para obter suas coordenadas para detecção de clique
                button_rect = pygame.Rect(LARGURA // 2 - 100, ALTURA_PISTA + 150, 200, 50)
                if button_rect.collidepoint(x, y):
                    resetar_jogo() # Chama a função para reiniciar o jogo

    # Lógica de controle do jogo (avançar, perguntas, vitória)
    if game_state == "running": # Só executa a lógica de corrida se o jogo estiver rodando
        if vencedor is None: # Só avança se não houver vencedor
            # Decidir quando mostrar perguntas
            # Apenas mostrar pergunta se o carro ainda não alcançou a linha de chegada
            # e se o semáforo puder ser adquirido (evita que um bot pegue a pergunta)
            if fase == "corrida" and Carro1.sprite.rect.left < 700:
                if not nitro_pego and Carro1.sprite.rect.left + 75 >= nitro_pos:
                    if semaforo_jogo.acquire(blocking=False): # Tenta adquirir o semáforo para o nitro
                        try:
                            fase = "pergunta_nitro"
                            nitro_pego = True
                        finally:
                            semaforo_jogo.release() # Libera imediatamente para a interação do usuário
                elif not todas_perguntas_respondidas and fase == "corrida": # Só tenta nova pergunta se não estiver em fase de pergunta
                    perguntas_disponiveis = [p for p in perguntas_multipla if p["id"] not in perguntas_ja_usadas]

                    if perguntas_disponiveis:
                        # O jogador só recebe uma pergunta se o semáforo estiver livre
                        if semaforo_jogo.acquire(blocking=False): # Tenta adquirir o semáforo para a pergunta múltipla
                            try:
                                pergunta_atual = random.choice(perguntas_disponiveis)
                                perguntas_ja_usadas.append(pergunta_atual["id"])
                                fase = "pergunta_multipla"
                            finally:
                                semaforo_jogo.release() # Libera imediatamente para a interação do usuário
                    else:
                        todas_perguntas_respondidas = True

            # Verificar vitória do jogador
            if Carro1.sprite.rect.left >= 700 and vencedor is None:
                if semaforo_jogo.acquire(blocking=False):
                    try:
                        vencedor = Carro1.sprite.nome
                        print(f"\n🏁 {vencedor} venceu a Corrida Sensata!")
                        game_state = "win" # Altera o estado do jogo para vitória
                    finally:
                        semaforo_jogo.release()
        else:
            # Se um vencedor foi definido, mas o game_state ainda não foi atualizado
            if vencedor != "Jogador" and game_state == "running":
                game_state = "game_over"

    clock.tick(30)

pygame.quit()