from PIL import Image, ImageDraw

# 32x32, RGBA, simple pixel-art style generator
OUT_DIR = r"e:\jupy_work\vansurv\assets\icons"

def save(img, name):
    img.save(f"{OUT_DIR}\\{name}.png", "PNG")

# Helper: draw block pixel (x,y) size 1

def sword():
    img = Image.new('RGBA', (32,32), (0,0,0,0))
    d = ImageDraw.Draw(img)
    # draw blade: light gray pixels, diagonal
    blade = [(12,4),(13,5),(14,6),(15,7),(16,8),(17,9),(18,10),(19,11),(20,12)]
    for (x,y) in blade:
        d.rectangle([x,y,x+1,y+1], fill=(220,220,220,255))
    # thicker top
    d.rectangle([11,3,13,5], fill=(200,200,200,255))
    # guard
    d.rectangle([10,12,22,14], fill=(160,120,80,255))
    # handle (brown)
    for i in range(14,22):
        d.rectangle([16, i, 17, i+1], fill=(110,60,20,255))
    # pommel
    d.rectangle([15,22,18,24], fill=(140,100,60,255))
    # outline
    d.rectangle([10,3,21,24], outline=(0,0,0,120))
    return img


def magic_wand():
    img = Image.new('RGBA', (32,32), (0,0,0,0))
    d = ImageDraw.Draw(img)
    # shaft
    for i in range(8,24):
        d.rectangle([14, i, 15, i+1], fill=(90,50,140,255))
    # handle tip
    d.rectangle([13,23,16,25], fill=(60,30,100,255))
    # magical orb at top
    orb_center = (15,7)
    for dy in range(-3,4):
        for dx in range(-3,4):
            if dx*dx+dy*dy <= 9:
                x = orb_center[0]+dx
                y = orb_center[1]+dy
                d.rectangle([x,y,x+1,y+1], fill=(180,90,220,255))
    # glow pixels
    glow = [(11,5),(19,5),(10,7),(20,7),(11,9),(19,9)]
    for x,y in glow:
        d.rectangle([x,y,x+1,y+1], fill=(230,160,255,140))
    # sparkles
    sparks = [(8,4),(23,6),(6,10),(24,10)]
    for x,y in sparks:
        d.rectangle([x,y,x+1,y+1], fill=(255,240,140,200))
    # outline
    d.rectangle([12,4,18,10], outline=(0,0,0,100))
    return img


def stone():
    img = Image.new('RGBA', (32,32), (0,0,0,0))
    d = ImageDraw.Draw(img)
    # base blob (gray)
    blob = [(8,14),(9,12),(10,11),(12,10),(14,9),(16,9),(18,10),(20,11),(22,13),(23,15),(22,17),(20,19),(18,20),(15,20),(12,19),(10,18),(9,17)]
    for x,y in blob:
        d.rectangle([x,y,x+2,y+2], fill=(150,150,150,255))
    # darker shading
    shade = [(12,12),(14,11),(16,11),(18,12),(19,14),(18,16),(16,17),(13,17),(11,16)]
    for x,y in shade:
        d.rectangle([x,y,x+1,y+1], fill=(120,120,120,255))
    # cracks
    cracks = [(13,13),(15,14),(17,15),(14,16)]
    for x,y in cracks:
        d.rectangle([x,y,x+1,y+1], fill=(90,90,90,255))
    # small highlight
    highlights = [(10,13),(11,14),(12,15)]
    for x,y in highlights:
        d.rectangle([x,y,x+1,y+1], fill=(200,200,200,200))
    return img


def whip():
    img = Image.new('RGBA', (32,32), (0,0,0,0))
    d = ImageDraw.Draw(img)
    # handle
    d.rectangle([6,18,12,24], fill=(110,60,20,255))
    d.rectangle([5,17,13,18], fill=(90,50,20,255))
    # coil segments
    segs = [(13,18,17,20),(16,16,20,18),(19,14,23,16),(21,12,25,14)]
    for x1,y1,x2,y2 in segs:
        d.rectangle([x1,y1,x2,y2], fill=(200,170,80,255))
        d.rectangle([x1,y1,x2,y2], outline=(60,40,20))
    # tip
    d.rectangle([24,11,26,13], fill=(220,220,100,255))
    return img


def holy_water():
    img = Image.new('RGBA', (32,32), (0,0,0,0))
    d = ImageDraw.Draw(img)
    # bottle body
    d.rectangle([10,6,22,22], fill=(220,240,255,220), outline=(30,30,30))
    # liquid
    d.rectangle([12,12,20,20], fill=(120,220,230,220))
    # neck
    d.rectangle([14,4,18,7], fill=(200,220,235,255))
    # cross symbol on bottle
    d.rectangle([15,10,16,14], fill=(220,240,250,255))
    d.rectangle([13,12,18,13], fill=(220,240,250,255))
    # sparkle
    d.rectangle([9,8,10,9], fill=(255,250,180,200))
    return img


def garlic():
    img = Image.new('RGBA', (32,32), (0,0,0,0))
    d = ImageDraw.Draw(img)
    # main cloves (three lobes)
    d.ellipse([9,10,18,20], fill=(240,240,230,255))
    d.ellipse([13,8,23,20], fill=(245,245,235,255))
    d.ellipse([7,12,15,22], fill=(235,235,225,255))
    # stem
    d.rectangle([16,6,17,10], fill=(80,140,60,255))
    # shadows/cracks
    d.rectangle([12,16,13,17], fill=(200,200,190,200))
    d.rectangle([17,14,18,15], fill=(200,200,190,200))
    return img


def axe():
    img = Image.new('RGBA', (32,32), (0,0,0,0))
    d = ImageDraw.Draw(img)
    # handle
    d.rectangle([14,14,16,26], fill=(110,60,20,255))
    d.rectangle([13,13,17,14], fill=(90,50,20,255))
    # axe head
    d.polygon([(8,8),(22,8),(22,18),(16,18),(12,14),(10,14)], fill=(200,200,200,255))
    # blade edge highlight
    d.line([(9,9),(21,9)], fill=(255,255,255,180))
    # rivet
    d.rectangle([17,12,18,13], fill=(120,120,120,255))
    return img

# --- Crystal icons for subitems ---

def crystal(color):
    """Generate a simple 32x32 crystal/gem with basic shading."""
    img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = 16, 14
    # core polygon (diamond)
    core = [(cx, cy-8), (cx+6, cy), (cx, cy+8), (cx-6, cy)]
    d.polygon(core, fill=color+(255,))
    # inner highlight (smaller, lighter)
    hl = (min(255, color[0]+60), min(255, color[1]+60), min(255, color[2]+60), 200)
    inner = [(cx, cy-5), (cx+3, cy), (cx, cy+5), (cx-3, cy)]
    d.polygon(inner, fill=hl)
    # facets (darker lines)
    dark = (max(0, color[0]-50), max(0, color[1]-50), max(0, color[2]-50), 200)
    d.line([core[0], core[1], core[2], core[3], core[0]], fill=dark, width=1)
    # small sparkle
    d.rectangle([cx+7, cy-8, cx+8, cy-7], fill=(255,255,255,200))
    d.rectangle([cx+8, cy-6, cx+9, cy-5], fill=(255,255,255,120))
    return img


def crystal_hp():
    return crystal((80,200,120))  # green

def crystal_base_damage():
    return crystal((220,60,60))  # red

def crystal_defense():
    return crystal((255,160,60))  # orange

def crystal_speed():
    return crystal((90,200,240))  # light blue

def crystal_effect_range():
    return crystal((240,220,70))  # yellow

def crystal_effect_time():
    return crystal((0,180,150))  # teal / 青緑

def crystal_extra_projectiles():
    return crystal((80,120,220))  # blue

def crystal_projectile_speed():
    return crystal((150,90,40))  # brown


if __name__ == '__main__':
    # save(sword(), 'sword')
    # save(magic_wand(), 'magic_wand')
    # save(stone(), 'stone')
    # save(whip(), 'whip')
    # save(holy_water(), 'holy_water')
    # save(garlic(), 'garlic')
    # save(axe(), 'axe')
    # save crystals for subitems
    save(crystal_hp(), 'hp')
    save(crystal_base_damage(), 'base_damage')
    save(crystal_defense(), 'defense')
    save(crystal_speed(), 'speed')
    save(crystal_effect_range(), 'effect_range')
    save(crystal_effect_time(), 'effect_time')
    save(crystal_extra_projectiles(), 'extra_projectiles')
    save(crystal_projectile_speed(), 'projectile_speed')
    print('Icons generated in', OUT_DIR)
