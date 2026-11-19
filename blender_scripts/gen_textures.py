import math, random, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
random.seed(84)
OUT = "/home/claude/tex/out"; os.makedirs(OUT, exist_ok=True)
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FM = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
def F(sz, mono=False): return ImageFont.truetype(FM if mono else FB, sz)

PINK=(255,40,170); CYAN=(0,230,255); YEL=(255,215,40); PURP=(150,60,255); ORNG=(255,120,20); GRN=(60,255,120); WHITE=(255,255,255)

def grad(w,h,c1,c2,horizontal=False):
    im=Image.new("RGB",(w,h)); d=ImageDraw.Draw(im)
    n = w if horizontal else h
    for i in range(n):
        t=i/max(1,n-1); c=tuple(int(c1[k]+(c2[k]-c1[k])*t) for k in range(3))
        if horizontal: d.line([(i,0),(i,h)],fill=c)
        else: d.line([(0,i),(w,i)],fill=c)
    return im

def stars(im, n, area=None, col=(255,255,255)):
    d=ImageDraw.Draw(im); w,h=im.size
    x0,y0,x1,y1 = area or (0,0,w,h)
    for _ in range(n):
        x=random.randint(x0,x1-1); y=random.randint(y0,y1-1); r=random.choice((1,1,1,2,2,3))
        d.ellipse([x-r,y-r,x+r,y+r],fill=col)

def glow_text(im, xy, text, font, col, glow=8, anchor="mm", stroke=0, stroke_col=(0,0,0)):
    layer=Image.new("RGBA",im.size,(0,0,0,0)); d=ImageDraw.Draw(layer)
    d.text(xy,text,font=font,fill=col+(255,),anchor=anchor,stroke_width=stroke+3,stroke_fill=col+(255,))
    layer=layer.filter(ImageFilter.GaussianBlur(glow))
    im.paste(layer,(0,0),layer); im.paste(layer,(0,0),layer)
    d2=ImageDraw.Draw(im)
    d2.text(xy,text,font=font,fill=(255,255,255) if glow else col,anchor=anchor,stroke_width=max(2,stroke),stroke_fill=col)

def sunset_grid(im, horizon, sun=True, sun_r=None, grid_col=PINK):
    w,h=im.size; d=ImageDraw.Draw(im)
    if sun:
        r = sun_r or w//4; cx=w//2; cy=horizon
        sunim=grad(2*r,2*r,(255,230,60),(255,40,140))
        mask=Image.new("L",(2*r,2*r),0); md=ImageDraw.Draw(mask); md.ellipse([0,0,2*r,2*r],fill=255)
        for i in range(6):  # franjas
            y=r+int(r*0.15)+i*int(r*0.14); md.rectangle([0,y,2*r,y+max(2,int(r*0.03)+i*2)],fill=0)
        md.rectangle([0,r,2*r,2*r],fill=0) if False else None
        im.paste(sunim,(cx-r,cy-r),mask)
    # montañas
    pts=[(0,horizon)]
    for x in range(0,w+40,40): pts.append((x,horizon-random.randint(int(h*0.02),int(h*0.09))))
    pts+= [(w,horizon)]
    d.polygon(pts,fill=(40,10,70))
    d.line(pts[1:-1],fill=CYAN,width=2)
    d.rectangle([0,horizon,w,h],fill=(15,0,30))
    for i in range(1,14):
        y=horizon+int((h-horizon)*(i/14)**1.8); d.line([(0,y),(w,y)],fill=grid_col,width=2)
    for i in range(-12,13):
        d.line([(w//2+i*w//24,horizon),(w//2+i*w//3,h)],fill=grid_col,width=2)

# ---------------- personajes originales ----------------
def eyes(d,cx,cy,s,look=(0,0)):
    for dx in (-1,1):
        x=cx+dx*s; d.ellipse([x-s*0.6,cy-s*0.75,x+s*0.6,cy+s*0.75],fill=WHITE,outline=(0,0,0),width=max(2,int(s*0.12)))
        d.ellipse([x-s*0.28+look[0]*s*0.2,cy-s*0.3+look[1]*s*0.2,x+s*0.28+look[0]*s*0.2,cy+s*0.3+look[1]*s*0.2],fill=(0,0,0))
        d.ellipse([x-s*0.1,cy-s*0.25,x+s*0.05,cy-s*0.1],fill=WHITE)

def char_gato(d,cx,cy,s):   # Astro Gato: gato astronauta
    d.ellipse([cx-s*1.3,cy-s*1.3,cx+s*1.3,cy+s*1.3],fill=(120,220,255),outline=WHITE,width=int(s*0.08))
    d.polygon([(cx-s*0.9,cy-s*0.4),(cx-s*0.7,cy-s*1.1),(cx-s*0.3,cy-s*0.7)],fill=(255,150,40))
    d.polygon([(cx+s*0.9,cy-s*0.4),(cx+s*0.7,cy-s*1.1),(cx+s*0.3,cy-s*0.7)],fill=(255,150,40))
    d.ellipse([cx-s*0.95,cy-s*0.8,cx+s*0.95,cy+s*0.9],fill=(255,150,40))
    eyes(d,cx,cy-s*0.05,s*0.35)
    d.polygon([(cx-s*0.1,cy+s*0.35),(cx+s*0.1,cy+s*0.35),(cx,cy+s*0.48)],fill=PINK)
    for dx in (-1,1):
        for k in (-1,0,1): d.line([(cx+dx*s*0.35,cy+s*0.45+k*s*0.08),(cx+dx*s*1.0,cy+s*0.4+k*s*0.15)],fill=(80,40,0),width=3)
    d.arc([cx-s*1.2,cy-s*1.2,cx-s*0.2,cy-s*0.2],200,250,fill=WHITE,width=int(s*0.1))

def char_slime(d,cx,cy,s):
    g=(80,240,90)
    d.ellipse([cx-s*1.5,cy+s*0.55,cx+s*1.5,cy+s*1.05],fill=g)          # charco
    d.polygon([(cx,cy-s*1.6),(cx-s*1.05,cy+s*0.2),(cx+s*1.05,cy+s*0.2)],fill=g)  # punta de gota
    d.ellipse([cx-s*1.1,cy-s*0.6,cx+s*1.1,cy+s*0.9],fill=g)
    d.ellipse([cx-s*0.75,cy-s*0.55,cx-s*0.4,cy-s*0.2],fill=(190,255,190))
    for k in range(3): d.ellipse([cx+s*(0.6+k*0.35),cy+s*(0.7-k*0.1),cx+s*(0.8+k*0.35),cy+s*(0.9-k*0.1)],fill=g)
    eyes(d,cx,cy,s*0.33,(0.5,0))
    d.arc([cx-s*0.4,cy+s*0.2,cx+s*0.4,cy+s*0.6],10,170,fill=(0,60,0),width=int(s*0.1))

def char_robot(d,cx,cy,s):
    d.line([(cx-s*0.5,cy-s*1.0),(cx-s*0.7,cy-s*1.5)],fill=(200,200,210),width=int(s*0.08)); d.ellipse([cx-s*0.85,cy-s*1.65,cx-s*0.55,cy-s*1.35],fill=PINK)
    d.line([(cx+s*0.5,cy-s*1.0),(cx+s*0.7,cy-s*1.5)],fill=(200,200,210),width=int(s*0.08)); d.ellipse([cx+s*0.55,cy-s*1.65,cx+s*0.85,cy-s*1.35],fill=CYAN)
    d.rounded_rectangle([cx-s*1.1,cy-s*1.0,cx+s*1.1,cy+s*0.9],radius=int(s*0.25),fill=(170,175,200),outline=(60,60,90),width=int(s*0.08))
    d.rounded_rectangle([cx-s*0.85,cy-s*0.7,cx+s*0.85,cy+s*0.1],radius=int(s*0.15),fill=(20,20,40))
    for dx in (-1,1): d.ellipse([cx+dx*s*0.45-s*0.2,cy-s*0.5,cx+dx*s*0.45+s*0.2,cy-s*0.1],fill=YEL)
    for i in range(5): d.rectangle([cx-s*0.6+i*s*0.26,cy+s*0.3,cx-s*0.45+i*s*0.26,cy+s*0.6],fill=(60,60,90))
    d.ellipse([cx-s*1.3,cy-s*0.3,cx-s*1.0,cy+s*0.1],fill=(255,80,80)); d.ellipse([cx+s*1.0,cy-s*0.3,cx+s*1.3,cy+s*0.1],fill=(255,80,80))

def char_cometa(d,cx,cy,s):
    for i,c in enumerate((PINK,ORNG,YEL)):
        d.polygon([(cx-s*0.3,cy-s*0.5+i*s*0.25),(cx-s*2.6,cy+s*1.2+i*s*0.25),(cx-s*2.4,cy+s*1.5+i*s*0.25),(cx-s*0.2,cy+s*0.1+i*s*0.25)],fill=c)
    pts=[]
    for k in range(10):
        r=s*1.15 if k%2==0 else s*0.5; a=-math.pi/2+k*math.pi/5
        pts.append((cx+r*math.cos(a),cy+r*math.sin(a)))
    d.polygon(pts,fill=YEL,outline=(255,140,0),width=int(s*0.08))
    eyes(d,cx,cy-s*0.05,s*0.22)
    d.arc([cx-s*0.25,cy+s*0.1,cx+s*0.25,cy+s*0.4],10,170,fill=(120,40,0),width=int(s*0.07))

def char_pulpo(d,cx,cy,s):
    col=(230,70,200)
    for i in range(6):
        x=cx-s*1.0+i*s*0.4
        d.line([(x,cy+s*0.3),(x+math.sin(i)*s*0.3,cy+s*1.0),(x-math.sin(i)*s*0.2,cy+s*1.5)],fill=col,width=int(s*0.22),joint="curve")
    d.ellipse([cx-s*1.1,cy-s*1.2,cx+s*1.1,cy+s*0.6],fill=col)
    d.ellipse([cx-s*0.75,cy-s*1.6,cx+s*0.75,cy-s*1.3],fill=(40,40,40)); d.rectangle([cx-s*0.45,cy-s*2.1,cx+s*0.45,cy-s*1.45],fill=(40,40,40))  # sombrero disco
    d.rectangle([cx-s*0.45,cy-s*1.65,cx+s*0.45,cy-s*1.5],fill=YEL)
    eyes(d,cx,cy-s*0.4,s*0.3,(-0.5,0))
    d.arc([cx-s*0.35,cy-s*0.05,cx+s*0.35,cy+s*0.3],10,170,fill=(80,0,60),width=int(s*0.08))

def char_topo(d,cx,cy,s):
    d.ellipse([cx-s,cy-s*1.1,cx+s,cy+s*1.2],fill=(140,90,50))
    d.ellipse([cx-s*0.6,cy-s*0.1,cx+s*0.6,cy+s*1.0],fill=(220,180,130))
    eyes(d,cx,cy-s*0.45,s*0.28)
    d.ellipse([cx-s*0.2,cy-s*0.05,cx+s*0.2,cy+s*0.25],fill=PINK)
    d.rectangle([cx-s*0.15,cy+s*0.45,cx-s*0.01,cy+s*0.65],fill=WHITE); d.rectangle([cx+s*0.01,cy+s*0.45,cx+s*0.15,cy+s*0.65],fill=WHITE)
    d.rectangle([cx-s*1.1,cy-s*1.35,cx+s*1.1,cy-s*1.15],fill=YEL); d.chord([cx-s*0.8,cy-s*1.9,cx+s*0.8,cy-s*0.8],180,360,fill=YEL)  # casco minero

def char_saturno(d,cx,cy,s):
    d.ellipse([cx-s*2.0,cy-s*0.45,cx+s*2.0,cy+s*0.45],outline=CYAN,width=int(s*0.16))
    d.ellipse([cx-s,cy-s,cx+s,cy+s],fill=(255,170,40),outline=(255,90,20),width=int(s*0.06))
    d.arc([cx-s*2.0,cy-s*0.45,cx+s*2.0,cy+s*0.45],0,180,fill=CYAN,width=int(s*0.16))
    eyes(d,cx,cy-s*0.15,s*0.3)
    d.arc([cx-s*0.35,cy+s*0.1,cx+s*0.35,cy+s*0.5],10,170,fill=(120,30,0),width=int(s*0.09))

CHARS={"gato":char_gato,"slime":char_slime,"robot":char_robot,"cometa":char_cometa,"pulpo":char_pulpo}
GAMES=[("ASTRO GATO","gato",(10,0,60),(120,0,140),CYAN),
       ("SLIME RALLY","slime",(0,40,40),(0,140,90),YEL),
       ("ROBO PUNCH","robot",(40,0,0),(170,20,60),CYAN),
       ("COMETA KID","cometa",(0,0,40),(40,20,140),PINK),
       ("PULPO DISCO","pulpo",(30,0,50),(200,40,150),YEL)]

def save(im,name,size=None):
    if size: im=im.resize(size,Image.LANCZOS)
    im.save(f"{OUT}/{name}.png"); print(name, im.size)

# ---------- maquinitas: lateral, marquesina, pantalla ----------
for i,(title,ch,c1,c2,acc) in enumerate(GAMES,1):
    side=grad(512,1024,c1,c2); stars(side,120,(0,0,512,600))
    sunset_grid(side,700,True,140,acc)
    d=ImageDraw.Draw(side); CHARS[ch](d,256,430,110)
    # franjas de carreras diagonales
    for k,cc in enumerate((PINK,YEL,CYAN)):
        d.polygon([(0,900+k*30),(512,780+k*30),(512,800+k*30),(0,920+k*30)],fill=cc)
    glow_text(side,(256,110),title.split()[0],F(84),acc,10)
    glow_text(side,(256,195),title.split()[1],F(84),WHITE if acc!=WHITE else PINK,10)
    save(side,f"cab{i}_side")
    mq=grad(1024,256,(10,0,25),c2,True); stars(mq,60)
    d=ImageDraw.Draw(mq); CHARS[ch](d,120,128,60); CHARS[ch](d,904,128,60)
    glow_text(mq,(512,128),title,F(96),acc,12,stroke=2,stroke_col=(0,0,0))
    save(mq,f"cab{i}_marquee")
    sc=Image.new("RGB",(512,384),(5,5,20)); stars(sc,50)
    d=ImageDraw.Draw(sc); CHARS[ch](d,256,200,70)
    glow_text(sc,(256,60),title,F(44,True),acc,6)
    glow_text(sc,(256,345),"INSERT COIN",F(34,True),YEL,4)
    for y in range(0,384,4): d.line([(0,y),(512,y)],fill=(0,0,0),width=1)  # scanlines
    save(sc,f"cab{i}_screen")
    # panel de control
    cp=grad(512,256,c2,c1); d=ImageDraw.Draw(cp)
    for k in range(10): d.line([(k*60-100,256),(k*60+60,0)],fill=tuple(min(255,x+40) for x in c2),width=10)
    d.text((440,220),"1P",font=F(40),fill=WHITE,anchor="mm")
    save(cp,f"cab{i}_panel")

# puerta de monedas
cd=Image.new("RGB",(256,256),(25,25,30)); d=ImageDraw.Draw(cd)
d.rounded_rectangle([10,10,246,246],12,outline=(160,160,170),width=6)
for k,x in enumerate((80,176)):
    d.rounded_rectangle([x-35,50,x+35,150],8,fill=(200,30,30) if k==0 else (30,160,60),outline=(230,230,230),width=4)
    d.rectangle([x-5,70,x+5,130],fill=(10,10,10)); d.text((x,175),"FICHA",font=F(18),fill=YEL,anchor="mm")
d.ellipse([118,200,138,220],fill=(180,180,190)); save(cd,"coin_door")

# alfombra cósmica (tileable)
cp=Image.new("RGB",(1024,1024),(12,6,30)); d=ImageDraw.Draw(cp)
for _ in range(90):
    x=random.randint(0,1024); y=random.randint(0,1024); c=random.choice((PINK,CYAN,YEL,PURP,GRN)); k=random.randint(0,4); s=random.randint(14,38)
    for ox in (-1024,0,1024):
        for oy in (-1024,0,1024):
            X=x+ox; Y=y+oy
            if k==0: d.ellipse([X-s,Y-s,X+s,Y+s],outline=c,width=5)
            elif k==1: d.polygon([(X,Y-s),(X+s,Y+s),(X-s,Y+s)],outline=c,width=5)
            elif k==2: d.line([(X-s,Y),(X-s//2,Y-s//2),(X,Y),(X+s//2,Y-s//2),(X+s,Y)],fill=c,width=5)
            elif k==3: d.ellipse([X-s//3,Y-s//3,X+s//3,Y+s//3],fill=c)
            else:
                d.ellipse([X-s,Y-s//1.6,X+s,Y+s//1.6],outline=c,width=4); d.ellipse([X-s//2,Y-s//2,X+s//2,Y+s//2],fill=c)
save(cp,"carpet")

# pared con paneles sutiles (tileable)
wl=grad(512,512,(28,16,48),(18,10,34)); d=ImageDraw.Draw(wl)
for x in range(0,512,128): d.line([(x,0),(x,512)],fill=(45,28,72),width=4)
d.line([(0,300),(512,300)],fill=(60,30,90),width=6)
for x in range(0,512,32):
    d.polygon([(x,300),(x+16,330),(x+32,300)],fill=(40,20,70))
save(wl,"wall")

# mural synthwave
mu=grad(2048,512,(20,0,50),(255,60,150)); stars(mu,200,(0,0,2048,250))
sunset_grid(mu,330,True,170,CYAN)
d=ImageDraw.Draw(mu)
for px in (180,420,1640,1880):   # palmeras
    d.line([(px,330),(px+20,170)],fill=(10,0,20),width=16)
    for a in range(0,360,45):
        d.line([(px+20,170),(px+20+90*math.cos(math.radians(a)),170+40*math.sin(math.radians(a))+25)],fill=(10,0,20),width=12)
glow_text(mu,(1024,90),"PIXEL 84",F(120),PINK,14,stroke=3)
save(mu,"mural")

# pósters
POST=[("TORNEO","VIERNES 8PM",PINK,"robot",(30,0,60)),("MEGA","COMBO x2",CYAN,"slime",(0,30,40)),
      ("ZONA","RETRO 1984",YEL,"cometa",(40,10,0)),("INSERT","COIN",GRN,"gato",(0,0,30))]
for i,(a,b,c,ch,bg) in enumerate(POST,1):
    p=grad(512,768,bg,(0,0,0)); stars(p,80)
    d=ImageDraw.Draw(p); d.rectangle([12,12,500,756],outline=c,width=8)
    CHARS[ch](d,256,420,120)
    glow_text(p,(256,110),a,F(96),c,10); glow_text(p,(256,660),b,F(56),WHITE,6)
    save(p,f"poster{i}")

# ---------------- RUEDA CÓSMICA ----------------
SEG=[10,25,5,50,10,100,20,5,250,15,30,"500"]
COLS=[(230,30,60),(255,200,30),(30,190,90),(40,120,255),(250,110,20),(160,50,230),(230,30,60),(255,200,30),(30,190,90),(40,120,255),(250,110,20),(20,20,20)]
n=len(SEG); W,H=1024,2400; bh=H//n
dr=Image.new("RGB",(W,H)); d=ImageDraw.Draw(dr)
for k,(v,c) in enumerate(zip(SEG,COLS)):
    y=k*bh; d.rectangle([0,y,W,y+bh],fill=c)
    d.rectangle([0,y,W,y+10],fill=WHITE); d.rectangle([0,y+bh-10,W,y+bh],fill=WHITE)
    for x in range(40,W,120): d.ellipse([x-9,y+20,x+9,y+38],fill=(255,250,200))
    txt=str(v) if v!="500" else "JACKPOT 500"
    col=YEL if v=="500" else WHITE
    d.text((W//2,y+bh//2+8),txt,font=F(110 if v!="500" else 96),fill=col,anchor="mm",stroke_width=8,stroke_fill=(0,0,0))
save(dr,"wheel_drum")
open(f"{OUT}/wheel_segments.txt","w").write(",".join(str(s) for s in SEG))

wb=grad(512,1024,(10,0,40),(60,0,120)); stars(wb,150)
d=ImageDraw.Draw(wb)
for k in range(8):
    y=650+k*45; d.arc([-300,y-200,812,y+200],200,340,fill=CYAN if k%2 else PINK,width=8)
char_saturno(d,256,300,90)
glow_text(wb,(256,860),"RUEDA",F(90),YEL,10); glow_text(wb,(256,955),"CÓSMICA",F(70),CYAN,10)
save(wb,"wheel_side")
wf=grad(1024,512,(40,0,90),(10,0,40)); stars(wf,80); d=ImageDraw.Draw(wf)
glow_text(wf,(512,200),"¡EMPUJA LA PALANCA!",F(70),PINK,10)
glow_text(wf,(512,350),"GANA HASTA 500 TICKETS",F(52),YEL,8)
save(wf,"wheel_front")
wt=Image.new("RGBA",(1024,700),(0,0,0,0)); d=ImageDraw.Draw(wt); char_saturno(d,512,330,200)
wt.save(f"{OUT}/wheel_topper.png")

# ---------------- basket ----------------
bb=Image.new("RGB",(1024,768),WHITE); d=ImageDraw.Draw(bb)
d.rectangle([0,0,1023,767],outline=(220,40,40),width=40)
d.rectangle([352,380,672,640],outline=(220,40,40),width=22)
d.rectangle([60,60,964,150],fill=(20,20,40)); glow_text(bb,(512,105),"MINI BASKET",F(60),ORNG,6)
save(bb,"backboard")
ball=Image.new("RGB",(1024,512),(235,110,25)); d=ImageDraw.Draw(ball)
for _ in range(4000):
    x=random.randint(0,1023); y=random.randint(0,511); d.point((x,y),fill=(200,85,15))
for x in (0,256,512,768,1023): d.line([(x,0),(x,512)],fill=(20,10,5),width=10)
d.line([(0,256),(1024,256)],fill=(20,10,5),width=10)
for off in (128,640):
    pts=[(off+120*math.sin(t/511*math.pi)*(1 if off==128 else -1), t) for t in range(0,512,8)]
    d.line(pts,fill=(20,10,5),width=10)
save(ball,"basketball")
bs=grad(1024,512,(80,10,0),(10,0,30),True); stars(bs,80); d=ImageDraw.Draw(bs)
for k in range(6): d.polygon([(100+k*150,512),(160+k*150,250-k*10),(220+k*150,512)],fill=(255,120-k*10,0))
glow_text(bs,(512,180),"¡ENCESTA!",F(110),YEL,12,stroke=3)
save(bs,"basket_side")

# ---------------- tiro al blanco ----------------
tg=Image.new("RGBA",(256,256),(0,0,0,0)); d=ImageDraw.Draw(tg)
for k,c in enumerate((WHITE,(220,20,40),WHITE,(220,20,40),WHITE,(220,20,40))):
    r=124-k*20; d.ellipse([128-r,128-r,128+r,128+r],fill=c)
d.ellipse([118,118,138,138],fill=YEL); tg.save(f"{OUT}/target.png")
bd=grad(2048,1024,(10,0,40),(90,20,120)); stars(bd,300,(0,0,2048,500))
d=ImageDraw.Draw(bd); d.ellipse([1500,90,1720,310],fill=(255,240,200))
# ciudad neón
for x in range(0,2048,70):
    h=random.randint(150,420); c=random.choice(((30,10,60),(40,15,80),(25,5,50)))
    d.rectangle([x,700-h,x+62,1024],fill=c)
    for wy in range(700-h+15,690,28):
        for wx in range(x+8,x+56,16):
            if random.random()<0.5: d.rectangle([wx,wy,wx+8,wy+12],fill=random.choice((YEL,CYAN,PINK,(255,230,150))))
d.rectangle([0,700,2048,1024],fill=(20,5,40))
for k in range(0,2048,60): d.polygon([(k,1024),(k+30,880),(k+60,1024)],fill=(30,120,60))
save(bd,"gallery_back")
gs=grad(1024,256,(160,10,30),(80,0,20),True); d=ImageDraw.Draw(gs)
for x in range(0,1024,128): d.rectangle([x,0,x+64,256],fill=(200,20,40))
glow_text(gs,(512,128),"TIRO AL BLANCO",F(90),YEL,8,stroke=3)
save(gs,"gallery_sign")

# ---------------- topo ----------------
ts=grad(512,768,(60,30,0),(200,100,20)); stars(ts,40); d=ImageDraw.Draw(ts)
char_topo(d,256,430,130)
for k in range(5): d.ellipse([40+k*95,650,110+k*95,700],fill=(40,20,0))
glow_text(ts,(256,80),"GOLPEA",F(80),YEL,10,stroke=3); glow_text(ts,(256,190),"EL TOPO",F(70),WHITE,8,stroke=3)
save(ts,"mole_side")
mf=Image.new("RGB",(512,256),(140,90,50)); d=ImageDraw.Draw(mf); char_topo(d,256,150,80)
save(mf,"mole_face")

# ---------------- recepción, nevera, premios ----------------
rc=grad(1024,512,(60,0,90),(20,0,40),True); stars(rc,100); d=ImageDraw.Draw(rc)
glow_text(rc,(512,170),"CANJEA TUS",F(90),CYAN,10); glow_text(rc,(512,320),"TICKETS",F(120),YEL,12,stroke=3)
save(rc,"counter_front")
can=Image.new("RGB",(512,256),(200,20,40)); d=ImageDraw.Draw(can)
for x in range(0,512,40): d.arc([x-60,120,x+60,260],180,360,fill=WHITE,width=6)
d.text((256,90),"BURBU",font=F(80),fill=WHITE,anchor="mm",stroke_width=4,stroke_fill=(120,0,20))
save(can,"can_burbu")
can2=Image.new("RGB",(512,256),(20,160,60)); d=ImageDraw.Draw(can2)
for x in range(0,512,30): d.line([(x,0),(x+60,256)],fill=(60,220,100),width=8)
d.text((256,100),"LIMA",font=F(80),fill=YEL,anchor="mm",stroke_width=4,stroke_fill=(0,60,0)); d.text((256,180),"ZAP",font=F(50),fill=WHITE,anchor="mm")
save(can2,"can_lima")
fh=grad(1024,256,(200,20,40),(120,0,20),True); d=ImageDraw.Draw(fh)
d.text((512,128),"BURBU ¡HELADA!",font=F(100),fill=WHITE,anchor="mm",stroke_width=6,stroke_fill=(80,0,10))
save(fh,"fridge_header")
rb=Image.new("RGB",(256,256),(15,15,15)); d=ImageDraw.Draw(rb)
cols=[(255,255,255),(255,213,0),(200,20,30),(255,110,0),(0,70,200),(0,160,70)]
for i in range(3):
    for j in range(3):
        d.rounded_rectangle([8+i*82,8+j*82,82+i*82,82+j*82],10,fill=random.choice(cols))
save(rb,"rubik")
for v in (50,80,120,200,300,500,750,1000):
    pt=Image.new("RGB",(256,128),YEL); d=ImageDraw.Draw(pt)
    d.rectangle([0,0,255,127],outline=(0,0,0),width=6)
    d.text((128,64),f"{v}",font=F(70),fill=(0,0,0),anchor="mm"); d.text((236,108),"T",font=F(26),fill=(200,20,40),anchor="mm")
    save(pt,f"price_{v}")
tk=Image.new("RGB",(256,128),(255,150,190)); d=ImageDraw.Draw(tk)
d.rectangle([4,4,251,123],outline=(200,20,90),width=4); d.text((128,64),"TICKET",font=F(46),fill=(150,0,60),anchor="mm")
save(tk,"ticket")
print("listo")

# frente del topo
mf2=grad(1024,640,(120,50,0),(230,120,20)); stars(mf2,60); d=ImageDraw.Draw(mf2)
for k in range(7): d.ellipse([60+k*135,520,160+k*135,580],fill=(60,30,0))
char_topo(d,170,330,95); char_topo(d,854,330,95)
glow_text(mf2,(512,230),"GOLPEA",F(130),YEL,12,stroke=3); glow_text(mf2,(512,390),"EL TOPO",F(110),WHITE,10,stroke=3)
save(mf2,"mole_front")
