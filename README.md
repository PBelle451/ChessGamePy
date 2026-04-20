# ♟ Xadrez com IA

Jogo de xadrez completo em Python com interface gráfica e inteligência artificial, desenvolvido com **Pygame**.

---

## Requisitos

- Python 3.8 ou superior
- Pygame 2.x

## Instalação

```bash
pip install pygame
```

## Como jogar

```bash
python chess.py
```

---

## Funcionalidades

### Regras completas
- Todos os movimentos das peças (rei, dama, torre, bispo, cavalo, peão)
- Roque (kingside e queenside)
- En passant
- Promoção de peão com escolha interativa
- Detecção de xeque, xeque-mate e empate por afogamento

### Interface
- Tabuleiro clássico com coordenadas (a–h, 1–8)
- Destaque visual ao selecionar uma peça (movimentos possíveis em verde)
- Último movimento destacado em amarelo
- Rei em xeque destacado em vermelho
- Arrastar e soltar as peças com o mouse
- Painel lateral com: vez de jogar, peças capturadas e histórico de movimentos

### Inteligência Artificial
- Algoritmo **Minimax com poda Alpha-Beta**
- Avaliação por valor de material + **tabelas posicionais** (PST)
- Profundidade configurável de 1 a 5 (padrão: 3)
- Roda em thread separada — a interface não trava enquanto a IA pensa

---

## Controles

| Ação | Como fazer |
|---|---|
| Mover peça | Clique na peça e clique no destino, ou arraste |
| Reiniciar | Botão **Reiniciar** ou tecla `R` |
| Trocar de lado | Botão **Trocar Lado** |
| Aumentar dificuldade | Botão **Difícil >** |
| Diminuir dificuldade | Botão **< Fácil** |

---

## Dificuldades

| Nível | Profundidade | Comportamento |
|---|---|---|
| 1 | 1 | Joga aleatoriamente entre os melhores imediatos |
| 2 | 2 | Evita perder peças |
| 3 | 3 | Joga taticamente — padrão recomendado |
| 4 | 4 | Forte, demora alguns segundos por jogada |
| 5 | 5 | Muito forte, pode demorar 10–30s por jogada |

---

## Estrutura do código

```
chess.py
├── Lógica do xadrez
│   ├── Geração de movimentos (raw_moves, legal_moves_sq)
│   ├── Aplicação de movimentos (do_move)
│   └── Detecção de xeque / xeque-mate
├── Inteligência Artificial
│   ├── Função de avaliação (evaluate)
│   ├── Minimax com Alpha-Beta (minimax)
│   └── Thread de busca (ai_think)
└── Interface gráfica (Pygame)
    ├── Tabuleiro e peças
    ├── Painel lateral
    └── Tela de promoção
```

---

## Licença

Projeto livre para uso pessoal e educacional.
