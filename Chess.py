"""
Xadrez com IA — Minimax + Alpha-Beta Pruning
Pecas renderizadas com fonte FreeSerif (suporte unicode completo)
"""

import pygame, sys, copy, threading

pygame.init()

# Tela
BOARD_PX   = 600
PANEL_W    = 220
W, H       = BOARD_PX + PANEL_W, BOARD_PX
SQ         = BOARD_PX // 8
FPS        = 60

# Cores
SQ_LIGHT   = (240, 217, 181)
SQ_DARK    = (181, 136,  99)
C_BG       = ( 18,  17,  14)
C_PANEL    = ( 26,  24,  20)
C_BORDER   = ( 55,  50,  40)
C_ACCENT   = (200, 160,  60)
C_TEXT     = (215, 205, 185)
C_MUTED    = (120, 110,  90)
C_SEL      = ( 80, 180,  80, 140)
C_HINT     = ( 60, 150,  60,  90)
C_CHECK    = (200,  40,  40, 170)
C_LAST_FR  = (200, 200,  60, 100)
C_LAST_TO  = (200, 200,  60, 140)

# Fontes
PIECE_FONT  = pygame.font.SysFont("freeserif", SQ - 8)
COORD_FONT  = pygame.font.SysFont("freeserif", 13)
UI_BIG      = pygame.font.SysFont("freeserif", 22, bold=True)
UI_MED      = pygame.font.SysFont("freeserif", 16)
UI_SM       = pygame.font.SysFont("freeserif", 13)

# Simbolos Unicode para as pecas
SYM = {
    ('w','K'):'♔', ('w','Q'):'♕', ('w','R'):'♖',
    ('w','B'):'♗', ('w','N'):'♘', ('w','P'):'♙',
    ('b','K'):'♚', ('b','Q'):'♛', ('b','R'):'♜',
    ('b','B'):'♝', ('b','N'):'♞', ('b','P'):'♟',
}

PIECE_VALS = {'P':100,'N':320,'B':330,'R':500,'Q':900,'K':20000}

# Tabelas posicionais (perspectiva branca)
PST = {
'P': [[ 0, 0, 0, 0, 0, 0, 0, 0],
      [50,50,50,50,50,50,50,50],
      [10,10,20,30,30,20,10,10],
      [ 5, 5,10,25,25,10, 5, 5],
      [ 0, 0, 0,20,20, 0, 0, 0],
      [ 5,-5,-10, 0, 0,-10,-5, 5],
      [ 5,10,10,-20,-20,10,10, 5],
      [ 0, 0, 0, 0, 0, 0, 0, 0]],
'N': [[-50,-40,-30,-30,-30,-30,-40,-50],
      [-40,-20,  0,  0,  0,  0,-20,-40],
      [-30,  0, 10, 15, 15, 10,  0,-30],
      [-30,  5, 15, 20, 20, 15,  5,-30],
      [-30,  0, 15, 20, 20, 15,  0,-30],
      [-30,  5, 10, 15, 15, 10,  5,-30],
      [-40,-20,  0,  5,  5,  0,-20,-40],
      [-50,-40,-30,-30,-30,-30,-40,-50]],
'B': [[-20,-10,-10,-10,-10,-10,-10,-20],
      [-10,  0,  0,  0,  0,  0,  0,-10],
      [-10,  0,  5, 10, 10,  5,  0,-10],
      [-10,  5,  5, 10, 10,  5,  5,-10],
      [-10,  0, 10, 10, 10, 10,  0,-10],
      [-10, 10, 10, 10, 10, 10, 10,-10],
      [-10,  5,  0,  0,  0,  0,  5,-10],
      [-20,-10,-10,-10,-10,-10,-10,-20]],
'R': [[ 0, 0, 0, 0, 0, 0, 0, 0],
      [ 5,10,10,10,10,10,10, 5],
      [-5, 0, 0, 0, 0, 0, 0,-5],
      [-5, 0, 0, 0, 0, 0, 0,-5],
      [-5, 0, 0, 0, 0, 0, 0,-5],
      [-5, 0, 0, 0, 0, 0, 0,-5],
      [-5, 0, 0, 0, 0, 0, 0,-5],
      [ 0, 0, 0, 5, 5, 0, 0, 0]],
'Q': [[-20,-10,-10, -5, -5,-10,-10,-20],
      [-10,  0,  0,  0,  0,  0,  0,-10],
      [-10,  0,  5,  5,  5,  5,  0,-10],
      [ -5,  0,  5,  5,  5,  5,  0, -5],
      [  0,  0,  5,  5,  5,  5,  0, -5],
      [-10,  5,  5,  5,  5,  5,  0,-10],
      [-10,  0,  5,  0,  0,  0,  0,-10],
      [-20,-10,-10, -5, -5,-10,-10,-20]],
'K': [[-30,-40,-40,-50,-50,-40,-40,-30],
      [-30,-40,-40,-50,-50,-40,-40,-30],
      [-30,-40,-40,-50,-50,-40,-40,-30],
      [-30,-40,-40,-50,-50,-40,-40,-30],
      [-20,-30,-30,-40,-40,-30,-30,-20],
      [-10,-20,-20,-20,-20,-20,-20,-10],
      [ 20, 20,  0,  0,  0,  0, 20, 20],
      [ 20, 30, 10,  0,  0, 10, 30, 20]],
}

# ============================================================
#  LOGICA DO XADREZ
# ============================================================

def initial_board():
    b = [[None]*8 for _ in range(8)]
    order = ['R','N','B','Q','K','B','N','R']
    for row, color in [(0,'b'),(7,'w')]:
        for c, p in enumerate(order):
            b[row][c] = (color, p)
        pr = 1 if color=='b' else 6
        for c in range(8):
            b[pr][c] = (color,'P')
    return b

def ib(r,c):
    return 0 <= r < 8 and 0 <= c < 8

def raw_moves(board, r, c, cr, ep):
    piece = board[r][c]
    if not piece: return []
    color, pt = piece
    opp = 'b' if color=='w' else 'w'
    mv = []

    def slide(dirs):
        for dr,dc in dirs:
            nr,nc = r+dr, c+dc
            while ib(nr,nc):
                if board[nr][nc]:
                    if board[nr][nc][0]==opp: mv.append((nr,nc))
                    break
                mv.append((nr,nc))
                nr+=dr; nc+=dc

    if pt=='P':
        d = -1 if color=='w' else 1
        sr = 6 if color=='w' else 1
        if ib(r+d,c) and not board[r+d][c]:
            mv.append((r+d,c))
            if r==sr and not board[r+2*d][c]:
                mv.append((r+2*d,c))
        for dc in (-1,1):
            nr,nc = r+d, c+dc
            if ib(nr,nc):
                if (board[nr][nc] and board[nr][nc][0]==opp) or ep==(nr,nc):
                    mv.append((nr,nc))
    elif pt=='N':
        for dr,dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            nr,nc = r+dr,c+dc
            if ib(nr,nc) and (not board[nr][nc] or board[nr][nc][0]==opp):
                mv.append((nr,nc))
    elif pt=='B': slide([(-1,-1),(-1,1),(1,-1),(1,1)])
    elif pt=='R': slide([(-1,0),(1,0),(0,-1),(0,1)])
    elif pt=='Q': slide([(-1,-1),(-1,1),(1,-1),(1,1),(-1,0),(1,0),(0,-1),(0,1)])
    elif pt=='K':
        for dr,dc in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
            nr,nc = r+dr,c+dc
            if ib(nr,nc) and (not board[nr][nc] or board[nr][nc][0]==opp):
                mv.append((nr,nc))
        row = 7 if color=='w' else 0
        if r==row and c==4:
            if cr[color]['K'] and not board[row][5] and not board[row][6]:
                mv.append((row,6))
            if cr[color]['Q'] and not board[row][3] and not board[row][2] and not board[row][1]:
                mv.append((row,2))
    return mv

def king_sq(board, color):
    for r in range(8):
        for c in range(8):
            if board[r][c]==(color,'K'): return r,c
    return None

def attacked(board, r, c, by):
    fake = {'w':{'K':False,'Q':False},'b':{'K':False,'Q':False}}
    for rr in range(8):
        for cc in range(8):
            if board[rr][cc] and board[rr][cc][0]==by:
                if (r,c) in raw_moves(board,rr,cc,fake,None):
                    return True
    return False

def in_check(board, color):
    ks = king_sq(board, color)
    return bool(ks and attacked(board, ks[0], ks[1], 'b' if color=='w' else 'w'))

def legal_moves_sq(board, r, c, cr, ep):
    piece = board[r][c]
    if not piece: return []
    color = piece[0]
    opp   = 'b' if color=='w' else 'w'
    legal = []
    for (nr,nc) in raw_moves(board,r,c,cr,ep):
        if piece[1]=='K' and abs(nc-c)==2:
            step = 1 if nc>c else -1
            mid  = c+step
            tmp  = copy.deepcopy(board)
            tmp[r][mid]=tmp[r][c]; tmp[r][c]=None
            if attacked(tmp,r,c,opp) or attacked(tmp,r,mid,opp):
                continue
        nb = copy.deepcopy(board)
        if piece[1]=='P' and ep==(nr,nc):
            nb[r][nc]=None
        nb[nr][nc]=nb[r][c]; nb[r][c]=None
        if not in_check(nb,color):
            legal.append((nr,nc))
    return legal

def all_legal(board, color, cr, ep):
    moves=[]
    for r in range(8):
        for c in range(8):
            if board[r][c] and board[r][c][0]==color:
                for m in legal_moves_sq(board,r,c,cr,ep):
                    moves.append(((r,c),m))
    return moves

def do_move(board, cr, ep, fr, fc, tr, tc, promo='Q'):
    nb  = copy.deepcopy(board)
    ncr = copy.deepcopy(cr)
    nep = None
    piece = nb[fr][fc]
    color, pt = piece

    if pt=='P' and ep==(tr,tc):
        nb[fr][tc]=None

    if pt=='K' and abs(tc-fc)==2:
        row=fr
        if tc==6: nb[row][5]=nb[row][7]; nb[row][7]=None
        else:     nb[row][3]=nb[row][0]; nb[row][0]=None

    nb[tr][tc]=nb[fr][fc]; nb[fr][fc]=None

    if pt=='K': ncr[color]['K']=False; ncr[color]['Q']=False
    if pt=='R':
        row=7 if color=='w' else 0
        if fr==row and fc==7: ncr[color]['K']=False
        if fr==row and fc==0: ncr[color]['Q']=False

    for (rr,cc,clr,side) in [(7,7,'w','K'),(7,0,'w','Q'),(0,7,'b','K'),(0,0,'b','Q')]:
        if (tr,tc)==(rr,cc): ncr[clr][side]=False

    if pt=='P' and abs(tr-fr)==2:
        nep=((fr+tr)//2,tc)

    if pt=='P' and (tr==0 or tr==7):
        nb[tr][tc]=(color,promo)

    return nb, ncr, nep

# ============================================================
#  AVALIACAO + MINIMAX
# ============================================================

def evaluate(board, color):
    score = 0
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if not p: continue
            pc, pt = p
            val = PIECE_VALS[pt]
            pr = r if pc=='w' else 7-r
            pos = PST[pt][pr][c]
            total = val + pos
            score += total if pc==color else -total
    return score

def order_moves(board, moves):
    def score(m):
        (fr,fc),(tr,tc) = m
        cap = board[tr][tc]
        if cap:
            return -(PIECE_VALS[cap[1]] - PIECE_VALS[board[fr][fc][1]])
        return 0
    return sorted(moves, key=score)

def minimax(board, cr, ep, depth, alpha, beta, maximizing, ai_color, stop_event):
    if stop_event.is_set():
        return evaluate(board, ai_color), None

    color = ai_color if maximizing else ('b' if ai_color=='w' else 'w')
    moves = all_legal(board, color, cr, ep)

    if not moves:
        if in_check(board, color):
            return (-99999 if maximizing else 99999), None
        return 0, None

    if depth == 0:
        return evaluate(board, ai_color), None

    moves = order_moves(board, moves)
    best_move = None

    if maximizing:
        best = -float('inf')
        for (fr,fc),(tr,tc) in moves:
            nb,ncr,nep = do_move(board,cr,ep,fr,fc,tr,tc)
            val,_ = minimax(nb,ncr,nep,depth-1,alpha,beta,False,ai_color,stop_event)
            if val > best:
                best = val; best_move = ((fr,fc),(tr,tc))
            alpha = max(alpha, best)
            if beta <= alpha: break
        return best, best_move
    else:
        best = float('inf')
        for (fr,fc),(tr,tc) in moves:
            nb,ncr,nep = do_move(board,cr,ep,fr,fc,tr,tc)
            val,_ = minimax(nb,ncr,nep,depth-1,alpha,beta,True,ai_color,stop_event)
            if val < best:
                best = val; best_move = ((fr,fc),(tr,tc))
            beta = min(beta, best)
            if beta <= alpha: break
        return best, best_move

AI_DEPTH = 3

def ai_think(board, cr, ep, ai_color, result_container, stop_event):
    _, move = minimax(board, cr, ep, AI_DEPTH, -float('inf'), float('inf'),
                      True, ai_color, stop_event)
    if not stop_event.is_set():
        result_container['move'] = move
        result_container['done'] = True

# ============================================================
#  RENDERIZACAO
# ============================================================

def blend(surf, rgba, rect):
    s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    s.fill(rgba)
    surf.blit(s, rect)

def draw_board(surf, sel, hints, check_king, last_move):
    for r in range(8):
        for c in range(8):
            base = SQ_LIGHT if (r+c)%2==0 else SQ_DARK
            rect = pygame.Rect(c*SQ, r*SQ, SQ, SQ)
            pygame.draw.rect(surf, base, rect)

            if last_move:
                (lfr,lfc),(ltr,ltc) = last_move
                if (r,c)==(lfr,lfc): blend(surf, C_LAST_FR, rect)
                if (r,c)==(ltr,ltc): blend(surf, C_LAST_TO, rect)

            if check_king and (r,c)==check_king:
                blend(surf, C_CHECK, rect)
            if sel and (r,c)==sel:
                blend(surf, C_SEL, rect)
            if (r,c) in hints:
                blend(surf, C_HINT, rect)
                pygame.draw.circle(surf, (50,140,50),
                    (c*SQ+SQ//2, r*SQ+SQ//2), SQ//7)

    files="abcdefgh"; ranks="87654321"
    for i in range(8):
        tc = SQ_DARK if i%2==0 else SQ_LIGHT
        t = COORD_FONT.render(files[i], True, tc)
        surf.blit(t, (i*SQ + SQ-t.get_width()-3, BOARD_PX-t.get_height()-2))
        t = COORD_FONT.render(ranks[i], True, SQ_DARK if i%2==1 else SQ_LIGHT)
        surf.blit(t, (3, i*SQ+3))

def draw_piece_at(surf, piece, x, y, sz):
    sym = SYM.get(piece, '?')
    shadow = PIECE_FONT.render(sym, True, (15, 12, 8))
    surf.blit(shadow, (x+(sz-shadow.get_width())//2+2, y+(sz-shadow.get_height())//2+2))
    col = (255, 250, 235) if piece[0]=='w' else (30, 25, 20)
    t = PIECE_FONT.render(sym, True, col)
    surf.blit(t, (x+(sz-t.get_width())//2, y+(sz-t.get_height())//2))

def draw_pieces(surf, board, dragging, drag_pos):
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if not p or (dragging and dragging==(r,c)): continue
            draw_piece_at(surf, p, c*SQ, r*SQ, SQ)
    if dragging and drag_pos:
        p = board[dragging[0]][dragging[1]]
        if p:
            draw_piece_at(surf, p, drag_pos[0]-SQ//2, drag_pos[1]-SQ//2, SQ)

BTNS = {}

def draw_panel(surf, G):
    global AI_DEPTH
    x = BOARD_PX
    pygame.draw.rect(surf, C_PANEL, (x,0,PANEL_W,H))
    pygame.draw.line(surf, C_BORDER, (x,0),(x,H), 2)

    y = 16
    title = UI_BIG.render("XADREZ  ♟", True, C_ACCENT)
    surf.blit(title, (x+(PANEL_W-title.get_width())//2, y)); y+=38
    pygame.draw.line(surf, C_BORDER, (x+10,y),(x+PANEL_W-10,y), 1); y+=14

    if G['game_over']:
        msg = G['status']; tc = C_ACCENT
    elif G['thinking']:
        msg = "IA pensando..."; tc = (100,160,220)
    else:
        who = "Brancas" if G['turn']=='w' else "Pretas"
        msg = f"Vez: {who}"; tc = C_TEXT
    t = UI_MED.render(msg, True, tc)
    surf.blit(t, (x+(PANEL_W-t.get_width())//2, y)); y+=26

    ai_lbl = "Voce: " + ("Brancas" if G['ai_color']=='b' else "Pretas")
    t = UI_SM.render(ai_lbl, True, C_MUTED)
    surf.blit(t,(x+(PANEL_W-t.get_width())//2,y)); y+=18

    diff_lbl = f"Dificuldade: {'I'*AI_DEPTH}  ({AI_DEPTH})"
    t = UI_SM.render(diff_lbl, True, C_MUTED)
    surf.blit(t,(x+(PANEL_W-t.get_width())//2,y)); y+=20

    if G['status']=="Xeque!" and not G['game_over']:
        t = UI_SM.render("! XEQUE !", True, (220,80,80))
        surf.blit(t,(x+(PANEL_W-t.get_width())//2,y)); y+=18

    pygame.draw.line(surf, C_BORDER,(x+10,y),(x+PANEL_W-10,y),1); y+=10

    def draw_caps(pieces, label):
        nonlocal y
        t=UI_SM.render(label, True, C_MUTED)
        surf.blit(t,(x+12,y)); y+=16
        row="".join(SYM.get(p,'') for p in pieces)
        if row:
            t=UI_SM.render(row, True, C_TEXT)
            surf.blit(t,(x+12,y))
        y+=18

    draw_caps(G['caps_b'], "Brancas capturaram:")
    draw_caps(G['caps_w'], "Pretas capturaram:")
    pygame.draw.line(surf, C_BORDER,(x+10,y),(x+PANEL_W-10,y),1); y+=8

    ht = UI_SM.render("Historico", True, C_MUTED)
    surf.blit(ht,(x+(PANEL_W-ht.get_width())//2,y)); y+=16
    shown = G['history'][-18:]
    for i in range(0,len(shown),2):
        num=(len(G['history'])-len(shown)+i)//2+1
        m1=shown[i]; m2=shown[i+1] if i+1<len(shown) else ""
        lt=UI_SM.render(f"{num:2d}. {m1:<8}{m2}", True, C_TEXT)
        surf.blit(lt,(x+10,y)); y+=15
        if y>H-80: break

    by = H-68
    _btn(surf, x+8,  by,   PANEL_W//2-12, 26, "Reiniciar", "restart")
    _btn(surf, x+PANEL_W//2+4, by, PANEL_W//2-12, 26, "Trocar Lado", "swap")
    by+=32
    _btn(surf, x+8, by, PANEL_W//2-12, 24, "< Facil", "easier")
    _btn(surf, x+PANEL_W//2+4, by, PANEL_W//2-12, 24, "Dificil >", "harder")

def _btn(surf, x, y, w, h, text, tag):
    rect = pygame.Rect(x,y,w,h)
    BTNS[tag] = rect
    mx,my = pygame.mouse.get_pos()
    hover = rect.collidepoint(mx,my)
    bg = (70,65,55) if hover else (42,40,34)
    pygame.draw.rect(surf, bg, rect, border_radius=4)
    pygame.draw.rect(surf, C_MUTED, rect, 1, border_radius=4)
    t = UI_SM.render(text, True, C_TEXT)
    surf.blit(t,(x+(w-t.get_width())//2, y+(h-t.get_height())//2))

def promotion_pick(surf, color):
    overlay = pygame.Surface((W,H), pygame.SRCALPHA)
    overlay.fill((0,0,0,170))
    surf.blit(overlay,(0,0))
    opts=['Q','R','B','N']; bw=bh=100
    total=len(opts)*(bw+16)-16
    sx=(BOARD_PX-total)//2; sy=H//2-bh//2
    rects={}
    for i,p in enumerate(opts):
        rx=sx+i*(bw+16)
        rect=pygame.Rect(rx,sy,bw,bh)
        pygame.draw.rect(surf,(50,46,38),rect,border_radius=10)
        pygame.draw.rect(surf,C_ACCENT,rect,2,border_radius=10)
        draw_piece_at(surf,(color,p),rx,sy,bw)
        rects[p]=rect
    lbl=UI_MED.render("Escolha a promocao:", True, C_TEXT)
    surf.blit(lbl,((BOARD_PX-lbl.get_width())//2, sy-34))
    pygame.display.flip()
    clk = pygame.time.Clock()
    while True:
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: pygame.quit(); sys.exit()
            if ev.type==pygame.MOUSEBUTTONDOWN:
                for p,rect in rects.items():
                    if rect.collidepoint(ev.pos): return p
        clk.tick(FPS)

# ============================================================
#  ESTADO DO JOGO
# ============================================================

def move_notation(fr,fc,tr,tc,piece,cap):
    files="abcdefgh"
    sym=SYM.get(piece,'')
    sep="x" if cap else "-"
    return f"{sym}{files[fc]}{8-fr}{sep}{files[tc]}{8-tr}"

def new_game(ai_color='b'):
    return {
        'board':    initial_board(),
        'turn':     'w',
        'cr':       {'w':{'K':True,'Q':True},'b':{'K':True,'Q':True}},
        'ep':       None,
        'sel':      None,
        'hints':    set(),
        'history':  [],
        'caps_w':   [],
        'caps_b':   [],
        'status':   '',
        'game_over':False,
        'last_move':None,
        'ai_color': ai_color,
        'thinking': False,
        'drag':     None,
        'drag_pos': None,
        'ai_result':{'move':None,'done':False},
        'ai_thread':None,
        'stop_ev':  threading.Event(),
    }

def check_game_state(G):
    opp=G['turn']
    lm=all_legal(G['board'],opp,G['cr'],G['ep'])
    if not lm:
        if in_check(G['board'],opp):
            winner="Brancas" if opp=='b' else "Pretas"
            G['status']=f"Xeque-mate! {winner} vencem!"
        else:
            G['status']="Empate (afogamento)!"
        G['game_over']=True
    elif in_check(G['board'],opp):
        G['status']="Xeque!"
    else:
        G['status']=''

def apply_move(G, fr, fc, tr, tc, screen=None):
    board=G['board']; cr=G['cr']; ep=G['ep']
    piece=board[fr][fc]; cap=board[tr][tc]; old_ep=ep

    G['board'],G['cr'],G['ep'] = do_move(board,cr,ep,fr,fc,tr,tc)

    if piece[1]=='P' and old_ep==(tr,tc) and not cap:
        cap_p = board[fr][tc]
        if cap_p:
            (G['caps_b'] if cap_p[0]=='b' else G['caps_w']).append(cap_p)
    elif cap:
        (G['caps_b'] if cap[0]=='b' else G['caps_w']).append(cap)

    if screen and piece[1]=='P' and (tr==0 or tr==7):
        choice = promotion_pick(screen, piece[0])
        G['board'][tr][tc]=(piece[0],choice)

    G['history'].append(move_notation(fr,fc,tr,tc,piece,cap))
    G['last_move']=((fr,fc),(tr,tc))
    G['turn']='b' if G['turn']=='w' else 'w'
    check_game_state(G)

def start_ai(G):
    G['thinking']=True
    G['ai_result']={'move':None,'done':False}
    G['stop_ev']=threading.Event()
    t=threading.Thread(target=ai_think,
        args=(G['board'],G['cr'],G['ep'],G['ai_color'],
              G['ai_result'],G['stop_ev']),daemon=True)
    G['ai_thread']=t
    t.start()

def stop_ai(G):
    if G.get('ai_thread') and G['ai_thread'].is_alive():
        G['stop_ev'].set()
        G['ai_thread'].join(timeout=0.5)
    G['thinking']=False

# ============================================================
#  MAIN
# ============================================================

def main():
    global AI_DEPTH
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Xadrez com IA")
    clock = pygame.time.Clock()

    G = new_game(ai_color='b')

    while True:
        clock.tick(FPS)
        mx,my = pygame.mouse.get_pos()

        # Resultado da IA pronto?
        if G['thinking'] and G['ai_result'].get('done'):
            G['thinking']=False
            move=G['ai_result']['move']
            if move and not G['game_over']:
                (fr,fc),(tr,tc)=move
                apply_move(G, fr, fc, tr, tc, None)

        # Vez da IA?
        if not G['game_over'] and not G['thinking'] and G['turn']==G['ai_color']:
            start_ai(G)

        for ev in pygame.event.get():
            if ev.type==pygame.QUIT:
                stop_ai(G); pygame.quit(); sys.exit()

            if ev.type==pygame.KEYDOWN:
                if ev.key==pygame.K_r:
                    stop_ai(G); G=new_game(G['ai_color'])

            if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
                for tag,rect in BTNS.items():
                    if rect.collidepoint(mx,my):
                        if tag=='restart':
                            stop_ai(G); G=new_game(G['ai_color'])
                        elif tag=='swap':
                            ai_c='w' if G['ai_color']=='b' else 'b'
                            stop_ai(G); G=new_game(ai_c)
                        elif tag=='harder' and AI_DEPTH<5:
                            AI_DEPTH+=1; stop_ai(G); G=new_game(G['ai_color'])
                        elif tag=='easier' and AI_DEPTH>1:
                            AI_DEPTH-=1; stop_ai(G); G=new_game(G['ai_color'])

                if mx < BOARD_PX and not G['game_over'] and not G['thinking']:
                    player = 'w' if G['ai_color']=='b' else 'b'
                    if G['turn']==player:
                        r,c=my//SQ, mx//SQ
                        if ib(r,c):
                            piece=G['board'][r][c]
                            if piece and piece[0]==player:
                                G['sel']=(r,c)
                                G['hints']=set(legal_moves_sq(G['board'],r,c,G['cr'],G['ep']))
                                G['drag']=(r,c); G['drag_pos']=(mx,my)
                            elif G['sel']:
                                if (r,c) in G['hints']:
                                    apply_move(G,G['sel'][0],G['sel'][1],r,c,screen)
                                G['sel']=None; G['hints']=set(); G['drag']=None

            if ev.type==pygame.MOUSEMOTION and G['drag']:
                G['drag_pos']=(mx,my)

            if ev.type==pygame.MOUSEBUTTONUP and ev.button==1:
                if G['drag'] and not G['game_over'] and not G['thinking']:
                    r,c=my//SQ,mx//SQ
                    fr,fc=G['drag']
                    if ib(r,c) and (r,c)!=(fr,fc) and (r,c) in G['hints']:
                        apply_move(G,fr,fc,r,c,screen)
                    G['drag']=None; G['sel']=None; G['hints']=set()

        # Render
        screen.fill(C_BG)
        bsurf = pygame.Surface((BOARD_PX,BOARD_PX))

        ck = None
        if in_check(G['board'],G['turn']):
            ck = king_sq(G['board'],G['turn'])

        draw_board(bsurf, G['sel'], G['hints'], ck, G['last_move'])
        draw_pieces(bsurf, G['board'], G['drag'], G['drag_pos'])

        if G['thinking']:
            s=pygame.Surface((BOARD_PX,BOARD_PX),pygame.SRCALPHA)
            s.fill((0,0,0,25))
            bsurf.blit(s,(0,0))
            txt=UI_MED.render("IA calculando...", True, (120,170,230))
            bsurf.blit(txt,((BOARD_PX-txt.get_width())//2, BOARD_PX//2-12))

        screen.blit(bsurf,(0,0))
        draw_panel(screen, G)
        pygame.display.flip()

if __name__=='__main__':
    main()