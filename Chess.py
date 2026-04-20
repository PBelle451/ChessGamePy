import pygame
import sys
import copy

pygame.init()

# ── Constantes de tela ──────────────────────────────────────────
BOARD_SIZE  = 640
PANEL_WIDTH = 240
WIDTH       = BOARD_SIZE + PANEL_WIDTH
HEIGHT      = BOARD_SIZE
SQ          = BOARD_SIZE // 8
FPS         = 60

# ── Paleta ──────────────────────────────────────────────────────
C_LIGHT    = (240, 217, 181)
C_DARK     = (181, 136,  99)
C_BG       = ( 22,  21,  18)
C_PANEL    = ( 30,  28,  24)
C_ACCENT   = (241, 194,  50)
C_SELECT   = (100, 200, 100, 160)
C_MOVE     = (100, 200, 100, 100)
C_CHECK    = (220,  50,  50, 180)
C_TEXT     = (220, 210, 190)
C_MUTED    = (140, 130, 110)
C_WHITE_P  = (255, 248, 230)
C_BLACK_P  = ( 40,  35,  30)
C_BORDER   = ( 60,  55,  45)

# ── Fontes ──────────────────────────────────────────────────────
F_BIG   = pygame.font.SysFont("Georgia", 26, bold=True)
F_MED   = pygame.font.SysFont("Georgia", 18)
F_SM    = pygame.font.SysFont("Georgia", 14)
F_COORD = pygame.font.SysFont("Georgia", 13, italic=True)
F_PIECE = pygame.font.SysFont("Segoe UI Symbol", SQ - 12)

# Símbolos Unicode para peças
SYMBOLS = {
    ('w','K'):'♔', ('w','Q'):'♕', ('w','R'):'♖',
    ('w','B'):'♗', ('w','N'):'♘', ('w','P'):'♙',
    ('b','K'):'♚', ('b','Q'):'♛', ('b','R'):'♜',
    ('b','B'):'♝', ('b','N'):'♞', ('b','P'):'♟',
}

# ── Lógica do Xadrez ────────────────────────────────────────────

def initial_board():
    b = [[None]*8 for _ in range(8)]
    order = ['R','N','B','Q','K','B','N','R']
    for c,color in [(0,'b'),(7,'w')]:
        for j,p in enumerate(order):
            b[c][j] = (color, p)
        prow = 1 if color=='b' else 6
        for j in range(8):
            b[prow][j] = (color,'P')
    return b

def in_bounds(r,c): return 0 <= r < 8 and 0 <= c < 8

def piece_moves_raw(board, r, c, castling_rights, en_passant):
    """Retorna movimentos sem verificação de xeque."""
    piece = board[r][c]
    if not piece: return []
    color, ptype = piece
    opp = 'b' if color=='w' else 'w'
    moves = []

    def slide(dirs):
        for dr,dc in dirs:
            nr,nc = r+dr, c+dc
            while in_bounds(nr,nc):
                if board[nr][nc]:
                    if board[nr][nc][0]==opp: moves.append((nr,nc))
                    break
                moves.append((nr,nc))
                nr+=dr; nc+=dc

    if ptype == 'P':
        d = -1 if color=='w' else 1
        start = 6 if color=='w' else 1
        if in_bounds(r+d,c) and not board[r+d][c]:
            moves.append((r+d,c))
            if r==start and not board[r+2*d][c]:
                moves.append((r+2*d,c))
        for dc in [-1,1]:
            nr,nc = r+d, c+dc
            if in_bounds(nr,nc):
                if board[nr][nc] and board[nr][nc][0]==opp:
                    moves.append((nr,nc))
                if en_passant == (nr,nc):
                    moves.append((nr,nc))

    elif ptype == 'N':
        for dr,dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            nr,nc = r+dr,c+dc
            if in_bounds(nr,nc) and (not board[nr][nc] or board[nr][nc][0]==opp):
                moves.append((nr,nc))

    elif ptype == 'B': slide([(-1,-1),(-1,1),(1,-1),(1,1)])
    elif ptype == 'R': slide([(-1,0),(1,0),(0,-1),(0,1)])
    elif ptype == 'Q': slide([(-1,-1),(-1,1),(1,-1),(1,1),(-1,0),(1,0),(0,-1),(0,1)])

    elif ptype == 'K':
        for dr,dc in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
            nr,nc = r+dr,c+dc
            if in_bounds(nr,nc) and (not board[nr][nc] or board[nr][nc][0]==opp):
                moves.append((nr,nc))
        # Roque
        row = 7 if color=='w' else 0
        if r==row and c==4:
            if castling_rights[color]['K']:
                if not board[row][5] and not board[row][6]:
                    moves.append((row,6))
            if castling_rights[color]['Q']:
                if not board[row][3] and not board[row][2] and not board[row][1]:
                    moves.append((row,2))

    return moves

def king_pos(board, color):
    for r in range(8):
        for c in range(8):
            if board[r][c]==(color,'K'): return r,c
    return None

def is_attacked(board, r, c, by_color):
    """Verifica se (r,c) é atacado por by_color."""
    # Usa movimentos brutos sem en-passant/roque para velocidade
    fake_cr = {'w':{'K':False,'Q':False},'b':{'K':False,'Q':False}}
    for rr in range(8):
        for cc in range(8):
            if board[rr][cc] and board[rr][cc][0]==by_color:
                if (r,c) in piece_moves_raw(board,rr,cc,fake_cr,None):
                    return True
    return False

def in_check(board, color):
    kp = king_pos(board,color)
    if not kp: return False
    opp = 'b' if color=='w' else 'w'
    return is_attacked(board, kp[0], kp[1], opp)

def legal_moves(board, r, c, castling_rights, en_passant):
    piece = board[r][c]
    if not piece: return []
    color = piece[0]
    opp = 'b' if color=='w' else 'w'
    raw = piece_moves_raw(board,r,c,castling_rights,en_passant)
    legal = []
    for (nr,nc) in raw:
        # Roque: verifica passagem
        if piece[1]=='K' and abs(nc-c)==2:
            row = r
            step = 1 if nc>c else -1
            mid = c+step
            tmp = copy.deepcopy(board)
            tmp[row][mid] = tmp[row][c]; tmp[row][c] = None
            if is_attacked(tmp,row,c,opp) or is_attacked(tmp,row,mid,opp):
                continue
        nb = copy.deepcopy(board)
        # En passant captura
        if piece[1]=='P' and en_passant==(nr,nc):
            cap_row = r
            nb[cap_row][nc] = None
        nb[nr][nc] = nb[r][c]; nb[r][c] = None
        if not in_check(nb,color):
            legal.append((nr,nc))
    return legal

def all_legal_moves(board, color, castling_rights, en_passant):
    moves = []
    for r in range(8):
        for c in range(8):
            if board[r][c] and board[r][c][0]==color:
                for m in legal_moves(board,r,c,castling_rights,en_passant):
                    moves.append(((r,c),m))
    return moves

def apply_move(board, castling_rights, en_passant, fr, fc, tr, tc):
    nb = copy.deepcopy(board)
    ncr = copy.deepcopy(castling_rights)
    nep = None
    piece = nb[fr][fc]
    color, ptype = piece

    # En passant captura
    if ptype=='P' and en_passant==(tr,tc):
        nb[fr][tc] = None

    # Roque
    if ptype=='K' and abs(tc-fc)==2:
        row = fr
        if tc==6: nb[row][5]=nb[row][7]; nb[row][7]=None
        else:     nb[row][3]=nb[row][0]; nb[row][0]=None

    nb[tr][tc] = nb[fr][fc]; nb[fr][fc] = None

    # Atualiza direitos de roque
    if ptype=='K': ncr[color]['K']=False; ncr[color]['Q']=False
    if ptype=='R':
        row = 7 if color=='w' else 0
        if fr==row and fc==7: ncr[color]['K']=False
        if fr==row and fc==0: ncr[color]['Q']=False
    if (tr,tc)==(7,7): ncr['w']['K']=False
    if (tr,tc)==(7,0): ncr['w']['Q']=False
    if (tr,tc)==(0,7): ncr['b']['K']=False
    if (tr,tc)==(0,0): ncr['b']['Q']=False

    # En passant flag
    if ptype=='P' and abs(tr-fr)==2:
        nep = ((fr+tr)//2, tc)

    # Promoção auto-queen
    if ptype=='P' and (tr==0 or tr==7):
        nb[tr][tc] = (color,'Q')

    return nb, ncr, nep

# ── Renderização ────────────────────────────────────────────────

def draw_board(surf, selected, highlights, check_king, flipped):
    for r in range(8):
        for c in range(8):
            dr = 7-r if flipped else r
            dc = 7-c if flipped else c
            color = C_LIGHT if (r+c)%2==0 else C_DARK
            rect = pygame.Rect(c*SQ, r*SQ, SQ, SQ)
            pygame.draw.rect(surf, color, rect)

            # Destaque xeque
            if (dr,dc)==check_king:
                s = pygame.Surface((SQ,SQ), pygame.SRCALPHA)
                s.fill(C_CHECK)
                surf.blit(s,rect)

            # Seleção
            if (dr,dc)==selected:
                s = pygame.Surface((SQ,SQ), pygame.SRCALPHA)
                s.fill(C_SELECT)
                surf.blit(s,rect)

            # Movimentos possíveis
            if (dr,dc) in highlights:
                s = pygame.Surface((SQ,SQ), pygame.SRCALPHA)
                s.fill(C_MOVE)
                surf.blit(s,rect)
                # Ponto central
                pygame.draw.circle(surf, (80,160,80,200),
                    (c*SQ+SQ//2, r*SQ+SQ//2), SQ//8)

    # Coordenadas
    files = "abcdefgh"
    ranks = "87654321"
    if flipped: files=files[::-1]; ranks=ranks[::-1]
    for i in range(8):
        tc = C_DARK if i%2==0 else C_LIGHT
        # Letras (bottom)
        t = F_COORD.render(files[i], True, tc)
        surf.blit(t, (i*SQ+SQ-12, BOARD_SIZE-15))
        # Números (left)
        t = F_COORD.render(ranks[i], True, C_DARK if i%2==1 else C_LIGHT)
        surf.blit(t, (4, i*SQ+4))

def draw_pieces(surf, board, flipped, dragging=None, drag_pos=None):
    for r in range(8):
        for c in range(8):
            dr = 7-r if flipped else r
            dc = 7-c if flipped else c
            piece = board[dr][dc]
            if not piece: continue
            if dragging and dragging==(dr,dc): continue
            sym = SYMBOLS.get(piece, '?')
            t = F_PIECE.render(sym, True, C_WHITE_P if piece[0]=='w' else C_BLACK_P)
            # Sombra
            ts = F_PIECE.render(sym, True, (0,0,0,120))
            surf.blit(ts, (c*SQ+(SQ-t.get_width())//2+2, r*SQ+(SQ-t.get_height())//2+2))
            surf.blit(t,  (c*SQ+(SQ-t.get_width())//2,   r*SQ+(SQ-t.get_height())//2))

    # Peça sendo arrastada
    if dragging and drag_pos:
        piece = board[dragging[0]][dragging[1]]
        if piece:
            sym = SYMBOLS.get(piece,'?')
            t = F_PIECE.render(sym, True, C_WHITE_P if piece[0]=='w' else C_BLACK_P)
            surf.blit(t, (drag_pos[0]-t.get_width()//2, drag_pos[1]-t.get_height()//2))

def draw_panel(surf, turn, move_history, status, captured_w, captured_b, flipped):
    x = BOARD_SIZE
    pygame.draw.rect(surf, C_PANEL, (x,0,PANEL_WIDTH,HEIGHT))
    pygame.draw.line(surf, C_BORDER, (x,0),(x,HEIGHT), 2)

    y = 18
    # Título
    title = F_BIG.render("♟  XADREZ", True, C_ACCENT)
    surf.blit(title, (x+(PANEL_WIDTH-title.get_width())//2, y))
    y += 38
    pygame.draw.line(surf, C_BORDER, (x+10,y),(x+PANEL_WIDTH-10,y),1)
    y += 14

    # Vez de jogar
    turn_str = "● Brancas" if turn=='w' else "● Pretas"
    tc = (240,240,220) if turn=='w' else (120,110,90)
    bg = (60,55,45) if turn!='w' else (80,75,60)
    trect = pygame.Rect(x+10, y, PANEL_WIDTH-20, 32)
    pygame.draw.rect(surf, bg, trect, border_radius=6)
    tt = F_MED.render(turn_str, True, tc)
    surf.blit(tt, (x+10+(PANEL_WIDTH-20-tt.get_width())//2, y+7))
    y += 44

    # Status
    if status:
        st = F_MED.render(status, True, C_ACCENT)
        surf.blit(st, (x+(PANEL_WIDTH-st.get_width())//2, y))
        y += 28

    # Peças capturadas
    def draw_captured(pieces, label, yy):
        lt = F_SM.render(label, True, C_MUTED)
        surf.blit(lt, (x+12, yy)); yy+=18
        row=""; xs=x+12
        for p in pieces:
            s = SYMBOLS.get(p,'')
            row+=s
        if row:
            t = F_SM.render(row, True, C_TEXT)
            surf.blit(t,(xs,yy))
        return yy+20

    y = draw_captured(captured_b, "Capturadas (Brancas):", y)
    y = draw_captured(captured_w, "Capturadas (Pretas):", y)
    y += 4
    pygame.draw.line(surf, C_BORDER, (x+10,y),(x+PANEL_WIDTH-10,y),1)
    y += 10

    # Histórico de movimentos
    ht = F_SM.render("Histórico de Movimentos", True, C_MUTED)
    surf.blit(ht,(x+(PANEL_WIDTH-ht.get_width())//2, y)); y+=20

    cols = ['a','b','c','d','e','f','g','h']
    shown = move_history[-18:]
    for i in range(0, len(shown), 2):
        num = (len(move_history)-len(shown)+i)//2+1
        m1 = shown[i]
        m2 = shown[i+1] if i+1<len(shown) else ""
        line = f"{num:2d}. {m1:<8}{m2}"
        lt = F_SM.render(line, True, C_TEXT)
        surf.blit(lt,(x+12,y)); y+=17
        if y>HEIGHT-80: break

    # Botões
    btn_y = HEIGHT - 60
    draw_button(surf, x+10, btn_y, PANEL_WIDTH//2-14, 28, "Reiniciar", C_BORDER, C_TEXT, "restart")
    draw_button(surf, x+PANEL_WIDTH//2+4, btn_y, PANEL_WIDTH//2-14, 28,
                "Girar" if not flipped else "Girar ↩", C_BORDER, C_TEXT, "flip")

BUTTONS = {}
def draw_button(surf, x,y,w,h,text,bg,fg,tag):
    rect = pygame.Rect(x,y,w,h)
    BUTTONS[tag] = rect
    pygame.draw.rect(surf, bg, rect, border_radius=5)
    pygame.draw.rect(surf, C_MUTED, rect, 1, border_radius=5)
    t = F_SM.render(text, True, fg)
    surf.blit(t,(x+(w-t.get_width())//2, y+(h-t.get_height())//2))

def pos_to_coords(r, c, flipped):
    cols = "abcdefgh"
    dr = r if not flipped else 7-r
    dc = c if not flipped else 7-c
    return f"{cols[dc]}{8-dr}"

def move_to_str(fr,fc,tr,tc,piece,captured,flipped):
    src = pos_to_coords(fr,fc,flipped)
    dst = pos_to_coords(tr,tc,flipped)
    cap = "x" if captured else "-"
    sym = SYMBOLS.get(piece,'')
    return f"{sym}{src}{cap}{dst}"

# ── Tela de promoção ────────────────────────────────────────────

def promotion_screen(surf, color):
    overlay = pygame.Surface((WIDTH,HEIGHT), pygame.SRCALPHA)
    overlay.fill((0,0,0,160))
    surf.blit(overlay,(0,0))
    bw,bh = 110,110
    opts = ['Q','R','B','N']
    total = len(opts)*(bw+20)-20
    sx = (WIDTH-total)//2
    sy = HEIGHT//2-bh//2
    rects = {}
    for i,p in enumerate(opts):
        rx = sx+i*(bw+20)
        rect = pygame.Rect(rx,sy,bw,bh)
        pygame.draw.rect(surf,(50,48,42),rect,border_radius=10)
        pygame.draw.rect(surf,C_ACCENT,rect,2,border_radius=10)
        sym = SYMBOLS.get((color,p),'')
        t = F_PIECE.render(sym,True, C_WHITE_P if color=='w' else C_BLACK_P)
        surf.blit(t,(rx+(bw-t.get_width())//2,sy+(bh-t.get_height())//2))
        rects[p]=rect
    pygame.display.flip()
    while True:
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: pygame.quit(); sys.exit()
            if ev.type==pygame.MOUSEBUTTONDOWN:
                mx,my=ev.pos
                for p,rect in rects.items():
                    if rect.collidepoint(mx,my): return p
        pygame.time.Clock().tick(FPS)

# ── Loop Principal ───────────────────────────────────────────────

def main():
    screen = pygame.display.set_mode((WIDTH,HEIGHT))
    pygame.display.set_caption("Xadrez")
    clock = pygame.time.Clock()

    def new_game():
        return {
            'board': initial_board(),
            'turn': 'w',
            'castling': {'w':{'K':True,'Q':True},'b':{'K':True,'Q':True}},
            'en_passant': None,
            'selected': None,
            'highlights': set(),
            'move_history': [],
            'captured_w': [],   # capturadas pelo branco (peças pretas)
            'captured_b': [],   # capturadas pelo preto (peças brancas)
            'status': '',
            'flipped': False,
            'dragging': None,
            'drag_pos': None,
            'game_over': False,
        }

    G = new_game()

    def sq_from_mouse(mx,my,flipped):
        if mx>=BOARD_SIZE: return None,None
        c = mx//SQ; r = my//SQ
        if flipped: r=7-r; c=7-c
        return r,c

    running = True
    while running:
        clock.tick(FPS)
        mx,my = pygame.mouse.get_pos()

        for ev in pygame.event.get():
            if ev.type==pygame.QUIT:
                running=False; break

            if ev.type==pygame.KEYDOWN:
                if ev.key==pygame.K_r: G=new_game()
                if ev.key==pygame.K_f: G['flipped']=not G['flipped']

            if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
                # Botões
                for tag,rect in BUTTONS.items():
                    if rect.collidepoint(mx,my):
                        if tag=='restart': G=new_game()
                        if tag=='flip': G['flipped']=not G['flipped']

                if not G['game_over']:
                    r,c = sq_from_mouse(mx,my,G['flipped'])
                    if r is not None:
                        piece = G['board'][r][c]
                        if piece and piece[0]==G['turn']:
                            G['selected']=(r,c)
                            G['highlights']=set(legal_moves(G['board'],r,c,G['castling'],G['en_passant']))
                            G['dragging']=(r,c)
                            G['drag_pos']=(mx,my)
                        elif G['selected']:
                            fr,fc=G['selected']
                            if (r,c) in G['highlights']:
                                # Executa movimento
                                moving = G['board'][fr][fc]
                                captured = G['board'][r][c]
                                ep = G['en_passant']
                                G['board'],G['castling'],G['en_passant'] = apply_move(
                                    G['board'],G['castling'],G['en_passant'],fr,fc,r,c)
                                # Promoção manual
                                if moving[1]=='P' and (r==0 or r==7):
                                    screen.blit(screen,(0,0))
                                    choice = promotion_screen(screen, moving[0])
                                    G['board'][r][c]=(moving[0],choice)
                                if captured:
                                    if captured[0]=='b': G['captured_b'].append(captured)
                                    else: G['captured_w'].append(captured)
                                # En passant captura
                                if moving[1]=='P' and ep==(r,c) and not captured:
                                    cap = G['board'][fr][c]
                                    if cap:
                                        if cap[0]=='b': G['captured_b'].append(cap)
                                        else: G['captured_w'].append(cap)
                                G['move_history'].append(move_to_str(fr,fc,r,c,moving,captured,G['flipped']))
                                G['turn']='b' if G['turn']=='w' else 'w'
                                # Verifica estado
                                opp=G['turn']
                                lm=all_legal_moves(G['board'],opp,G['castling'],G['en_passant'])
                                if not lm:
                                    if in_check(G['board'],opp):
                                        w='Brancas' if opp=='b' else 'Pretas'
                                        G['status']=f"Xeque-mate! {w} vencem!"
                                    else:
                                        G['status']="Empate (afogamento)!"
                                    G['game_over']=True
                                elif in_check(G['board'],opp):
                                    G['status']="Xeque!"
                                else:
                                    G['status']=''
                            G['selected']=None
                            G['highlights']=set()
                            G['dragging']=None

            if ev.type==pygame.MOUSEMOTION:
                if G['dragging']:
                    G['drag_pos']=(mx,my)

            if ev.type==pygame.MOUSEBUTTONUP and ev.button==1:
                if G['dragging'] and not G['game_over']:
                    r,c = sq_from_mouse(mx,my,G['flipped'])
                    fr,fc = G['dragging']
                    if r is not None and (r,c)!=( fr,fc) and (r,c) in G['highlights']:
                        moving = G['board'][fr][fc]
                        captured = G['board'][r][c]
                        ep = G['en_passant']
                        G['board'],G['castling'],G['en_passant'] = apply_move(
                            G['board'],G['castling'],G['en_passant'],fr,fc,r,c)
                        if moving[1]=='P' and (r==0 or r==7):
                            choice = promotion_screen(screen, moving[0])
                            G['board'][r][c]=(moving[0],choice)
                        if captured:
                            if captured[0]=='b': G['captured_b'].append(captured)
                            else: G['captured_w'].append(captured)
                        if moving[1]=='P' and ep==(r,c) and not captured:
                            cap = G['board'][fr][c]
                            if cap:
                                if cap[0]=='b': G['captured_b'].append(cap)
                                else: G['captured_w'].append(cap)
                        G['move_history'].append(move_to_str(fr,fc,r,c,moving,captured,G['flipped']))
                        G['turn']='b' if G['turn']=='w' else 'w'
                        opp=G['turn']
                        lm=all_legal_moves(G['board'],opp,G['castling'],G['en_passant'])
                        if not lm:
                            if in_check(G['board'],opp):
                                w='Brancas' if opp=='b' else 'Pretas'
                                G['status']=f"Xeque-mate! {w} vencem!"
                            else:
                                G['status']="Empate (afogamento)!"
                            G['game_over']=True
                        elif in_check(G['board'],opp):
                            G['status']="Xeque!"
                        else:
                            G['status']=''
                    G['dragging']=None
                    G['drag_pos']=None
                    G['selected']=None
                    G['highlights']=set()

        # ── Renderização ──
        screen.fill(C_BG)
        board_surf = pygame.Surface((BOARD_SIZE,BOARD_SIZE))

        check_king = None
        if in_check(G['board'],G['turn']):
            check_king = king_pos(G['board'],G['turn'])

        draw_board(board_surf, G['selected'], G['highlights'], check_king, G['flipped'])
        draw_pieces(board_surf, G['board'], G['flipped'], G['dragging'], G['drag_pos'])
        screen.blit(board_surf,(0,0))
        draw_panel(screen, G['turn'], G['move_history'], G['status'],
                   G['captured_w'], G['captured_b'], G['flipped'])

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__=='__main__':
    main()