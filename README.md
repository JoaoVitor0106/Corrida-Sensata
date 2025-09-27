
-----

# 🚗 Corrida Sensata

Um jogo em **Python + Pygame** onde você compete em uma corrida contra 3 carros controlados por **threads**, mas com um diferencial: para avançar na pista, você precisa **responder perguntas** de múltipla escolha e descritivas. O vencedor é quem cruzar a linha de chegada primeiro\! 🏁

-----

## 🎮 Funcionalidades

  - Corrida entre **jogador x 3 carros automáticos**.
  - Perguntas de **múltipla escolha** para avançar na pista.
  - Perguntas **descritivas** ao pegar *nitro*, com avaliação feita por IA.
  - Interface gráfica completa construída com **Pygame**.
  - Sistema de **menu inicial** para começar o jogo.
  - Efeitos sonoros para fundo, nitro e vitória.

-----

## 📂 Estrutura do Projeto

```
Jogo/
├── main.py         # Arquivo principal que inicia o jogo
├── menu.py         # Lógica da tela de menu inicial
├── classes.py      # Classes dos objetos (Carro, Jogador, etc.)
├── constantes.py   # Cores, tamanhos e configurações fixas
├── funcoes.py      # Funções auxiliares do jogo
├── perguntas.json  # Banco de perguntas de múltipla escolha
├── chave.env       # Arquivo para a chave de API da IA (não incluso no repo)
└── assets/         # Pasta com todas as imagens e sons
    ├── Civic.png
    ├── gelo.png
    ├── menu.png
    ├── pista.png
    ├── carros/
    │   ├── carro1.png
    │   ├── carro2.png
    │   ├── carro3.png
    │   ├── carro4.png
    │   └── carro_jogador.png
    └── sounds/
        ├── FundoSo.mp3
        ├── nitro.wav
        └── vitoria.wav
```

-----

## 🚀 Como Rodar o Jogo

### 1️⃣ Clone o repositório

```bash
git clone https://github.com/JoaoVitor0106/Jogo.git
cd Jogo
```

### 2️⃣ Crie um ambiente virtual (Opcional, mas recomendado)

```bash
# Para Linux/Mac
python -m venv venv
source venv/bin/activate

# Para Windows
python -m venv venv
venv\Scripts\activate
```

### 3️⃣ Instale as dependências

O único requisito é o Pygame.

```bash
pip install pygame
```

### 4️⃣ (Opcional) Configure a chave da IA

Para que as perguntas de nitro funcionem, crie um arquivo chamado `chave.env` na pasta raiz do projeto e adicione sua chave de API.

**Exemplo (`chave.env`):**

```
GEMINI_API_KEY = sua_chave_aqui
```

### 5️⃣ Inicie o jogo

```bash
python main.py
```

-----

## 🕹️ Como Jogar

1.  Inicie o jogo pelo menu principal.
2.  Responda corretamente às perguntas de múltipla escolha que aparecem na tela para fazer seu carro avançar.
3.  Desvie dos obstáculos de gelo na pista.
4.  Colete os itens de "nitro" para ter a chance de responder a uma pergunta descritiva e ganhar um grande impulso.
5.  Seja mais rápido que os outros 3 competidores e cruze a linha de chegada primeiro para vencer\! 🏆

-----

## 🔧 Tecnologias Utilizadas

  - **Python 🐍**
  - **Pygame 🎮**
  - **Threads** (para a movimentação autônoma dos carros oponentes)
  - **Integração com IA Generativa** (para avaliação das respostas descritivas)

-----

## 📜 Licença

Este projeto é de uso livre para fins acadêmicos e de aprendizado. Sinta-se à vontade para clonar, modificar e contribuir\! ✨
