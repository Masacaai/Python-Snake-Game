import pygame
import sys
import os
import random
import mysql.connector as sqltor

# Centers the Pygame window on the user's screen
os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (100,100)
# Initializes the Pygame module
pygame.init()

########################################################################################################################

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

########################################################################################################################

''' 

This script is very long, so I've included a table of contents so it will be easier for people to navigate:

1. Common variables                                         - Line 46
2. Importing foreign assets                                 - Line 62
3. Classes used in the game                                 - Line 82
4. Functions related to MySQL connectivity                  - Line 294
5. General utility functions                                - Line 527
5. Functions related to controlling the snakes              - Line 575
6. Functions that are used in the flow of the game          - Line 662
7. Functions related to singleplayer modes of the game      - Line 822
8. Functions related to multiplayer modes of the game       - Line 1007
9. Introduction functions of the game                       - Line 1215
10. This is where the game starts                           - Line 1291

'''

########################################################################################################################

# Setting up all common variables in the game

FONT = pygame.font.Font(resource_path("8-bit.ttf"), 20)
COLOR_INACTIVE = pygame.Color('lightskyblue3')
COLOR_ACTIVE = pygame.Color('dodgerblue2')
width = 1200
height = 600
rows = 48
columns = 24
Blue = (55,105,148)
Yellow = (255,195,49)
Black = (0,0,0)
White = (255,255,255)

########################################################################################################################

# Setting up all the assets to be used in the game

win = pygame.display.set_mode((width, height))
pygame.display.set_caption("Python: The Game")
gameIcon = pygame.image.load(resource_path("Pictures\\Python_logo_icon.png"))
pygame.display.set_icon(gameIcon)
logo = pygame.image.load(resource_path("Pictures\\Python-icon.png"))
logo = pygame.transform.scale(logo, (200, 200))
singleplayer_easy_instructions = pygame.image.load(resource_path("Pictures\\Singleplayer_easy_instructions.PNG"))
singleplayer_hard_instructions = pygame.image.load(resource_path("Pictures\\Singleplayer_hard_instructions.PNG"))
multiplayer_coop_instructions = pygame.image.load(resource_path("Pictures\\Multiplayer_coop_instructions.PNG"))
multiplayer_computer_instructions = pygame.image.load(resource_path("Pictures\\Multiplayer_computer_instructions.PNG"))
click_sound = pygame.mixer.Sound(resource_path("Music\\click.wav"))
eat_sound = pygame.mixer.Sound(resource_path("Music\\eat.ogg"))
hit_sound = pygame.mixer.Sound(resource_path("Music\\hit.wav"))
gamestart_sound = pygame.mixer.Sound(resource_path("Music\\game_start.ogg"))
gameover_sound = pygame.mixer.Sound(resource_path("Music\\game_over.ogg"))

########################################################################################################################

# Classes used in the game

class cube(object):

    def __init__(self, start,color,dirnx=1, dirny=0):
        self.pos = start
        self.dirnx = dirnx
        self.dirny = dirny
        self.color = color

    def move(self, dirnx, dirny):
        self.dirnx = dirnx
        self.dirny = dirny
        self.pos = (self.pos[0] + self.dirnx, self.pos[1] + self.dirny)

    def draw(self, surface, eyes=False):
        dis = width // rows
        i = self.pos[0]
        j = self.pos[1]

        pygame.draw.rect(surface, self.color, (i * dis + 1, j * dis + 1, dis, dis))
        if eyes:
            centre = dis // 2
            radius = 3
            circleMiddle = (i * dis + centre - radius, j * dis + 8)
            circleMiddle2 = (i * dis + dis - radius * 2, j * dis + 8)
            pygame.draw.circle(surface, Black, circleMiddle, radius)
            pygame.draw.circle(surface, Black, circleMiddle2, radius)

class snake(object):
    body = []
    turns = {}

    def __init__(self, color, pos, left_key, right_key, up_key, down_key):
        self.color = color
        self.head = cube(pos, color)
        self.body = []
        self.turns = {}
        self.body.append(self.head)
        self.dirnx = 0
        self.dirny = 1
        self.left_key = left_key
        self.right_key = right_key
        self.up_key = up_key
        self.down_key = down_key

    def move(self):

        for i, c in enumerate(self.body):
            p = c.pos[:]
            if p in self.turns:
                turn = self.turns[p]
                c.move(turn[0], turn[1])
                if i == len(self.body) - 1:
                    self.turns.pop(p)
            else:
                if c.dirnx == -1 and c.pos[0] <= 0:
                    c.pos = (rows - 1, c.pos[1])
                elif c.dirnx == 1 and c.pos[0] >= rows - 1:
                    c.pos = (0, c.pos[1])
                elif c.dirny == 1 and c.pos[1] >= columns - 1:
                    c.pos = (c.pos[0], 0)
                elif c.dirny == -1 and c.pos[1] <= 0:
                    c.pos = (c.pos[0], columns - 1)
                else:
                    c.move(c.dirnx, c.dirny)

    def addCube(self):
        tail = self.body[-1]
        dx, dy = tail.dirnx, tail.dirny

        if dx == 1 and dy == 0:
            self.body.append(cube((tail.pos[0] - 1, tail.pos[1]), self.color))
        elif dx == -1 and dy == 0:
            self.body.append(cube((tail.pos[0] + 1, tail.pos[1]), self.color))
        elif dx == 0 and dy == 1:
            self.body.append(cube((tail.pos[0], tail.pos[1] - 1), self.color))
        elif dx == 0 and dy == -1:
            self.body.append(cube((tail.pos[0], tail.pos[1] + 1), self.color))

        self.body[-1].dirnx = dx
        self.body[-1].dirny = dy

    def draw(self, surface):
        for i, c in enumerate(self.body):
            if i == 0:
                c.draw(surface, True)
            else:
                c.draw(surface)

# A special class only used by Hard Mode to kill the snake when it reaches the edges of the game screen

class snakey(object):
    global sh
    body = []
    turns = {}

    def __init__(self, color, pos, left_key, right_key, up_key, down_key):
        self.color = color
        self.head = cube(pos, color)
        self.body = []
        self.turns = {}
        self.body.append(self.head)
        self.dirnx = 0
        self.dirny = 1
        self.left_key = left_key
        self.right_key = right_key
        self.up_key = up_key
        self.down_key = down_key

    def move(self):

        for i, c in enumerate(self.body):
            p = c.pos[:]
            if p in self.turns:
                turn = self.turns[p]
                c.move(turn[0], turn[1])
                if i == len(self.body) - 1:
                    self.turns.pop(p)
            else:
                if c.dirnx == -1 and c.pos[0] <= 0:
                    hit_sound.play()
                    pygame.time.delay(1000)
                    die(sh, "hard", singleplayer_hard)
                    break
                elif c.dirnx == 1 and c.pos[0] >= rows - 1:
                    hit_sound.play()
                    pygame.time.delay(1000)
                    die(sh, "hard", singleplayer_hard)
                    break
                elif c.dirny == 1 and c.pos[1] >= columns - 1:
                    hit_sound.play()
                    pygame.time.delay(1000)
                    die(sh, "hard", singleplayer_hard)
                    break
                elif c.dirny == -1 and c.pos[1] <= 0:
                    hit_sound.play()
                    pygame.time.delay(1000)
                    die(sh, "hard", singleplayer_hard)
                    break
                else:
                    c.move(c.dirnx, c.dirny)

    def addCube(self):
        tail = self.body[-1]
        dx, dy = tail.dirnx, tail.dirny

        if dx == 1 and dy == 0:
            self.body.append(cube((tail.pos[0] - 1, tail.pos[1]), self.color))
        elif dx == -1 and dy == 0:
            self.body.append(cube((tail.pos[0] + 1, tail.pos[1]), self.color))
        elif dx == 0 and dy == 1:
            self.body.append(cube((tail.pos[0], tail.pos[1] - 1), self.color))
        elif dx == 0 and dy == -1:
            self.body.append(cube((tail.pos[0], tail.pos[1] + 1), self.color))

        self.body[-1].dirnx = dx
        self.body[-1].dirny = dy

    def draw(self, surface):
        for i, c in enumerate(self.body):
            if i == 0:
                c.draw(surface, True)
            else:
                c.draw(surface)

#A class to handle the test input boxes used in the game

class InputBox:
    def __init__(self, x, y, w, h,text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = COLOR_INACTIVE
        self.text = text
        self.txt_surface = FONT.render(text, True, self.color)
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # If the user clicked on the input_box rect.
            if self.rect.collidepoint(event.pos):
                # Toggle the active variable.
                self.active = not self.active
            else:
                self.active = False
            # Change the current color of the input box.
            self.color = COLOR_ACTIVE if self.active else COLOR_INACTIVE
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                # Re-render the text.
                self.txt_surface = FONT.render(self.text, True, self.color)

    def update(self):
        # Resize the box if the text is too long.
        width = max(200, self.txt_surface.get_width()+10)
        self.rect.w = width

    def draw(self, screen):
        # Blit the text.
        screen.blit(self.txt_surface, (self.rect.x+5, self.rect.y+5))
        # Blit the rect.
        pygame.draw.rect(screen, self.color, self.rect, 2)

########################################################################################################################

# All the functions dealing with MySQL connectivity

def details(main,modey,scorey = 0):
    global host, user, passwd, name, mode, pts
    clock = pygame.time.Clock()
    mode = modey
    pts = scorey
    host = InputBox(150, 135, 140, 32)
    user = InputBox(150, 185, 140, 32)
    passwd = InputBox(550, 185, 140, 32)
    name= InputBox(150, 385, 140, 32)
    list = [host,user,passwd,name]
    done = False

    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                close()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    close()
            for box in list:
                box.handle_event(event)
                box.update()

        win.fill(White)
        words("Enter your MySQL details so your account can be accessed", 30, Black, width//2, 50)
        words("Host:", 20, Black, 100, 150)
        words("User:", 20, Black, 100, 200)
        words("Passwd:", 20, Black, 500, 200)
        words("Enter the name under which your score should be saved to the scoreboard", 25, Black, width//2, 300)
        words("Name:", 20, Black, 100, 400)

        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        if 500 < mouse[0] < 700 and 500 < mouse[1] < 550:
            drawButton(Blue, (500, 500, 200, 50), "Submit", White, 20)
            if click[0] == 1:
                click_sound.play()
                done = not done
                pygame.time.delay(150)
                submit(main)
        else:
            drawButton(Yellow, (500, 500, 200, 50), "Submit", Black, 20)

        for box in list:
            box.draw(win)

        pygame.display.update()
        clock.tick(30)

def submit(main):
    sql(mode,name.text,pts,counting_string)
    game_over("You ate " +str(pts)+ " apples before you lost!", main)

def sql(mode,name,score,time):

    mycon = sqltor.connect(host = host.text,user= user.text,passwd= passwd.text)
    cursor = mycon.cursor()
    cursor.execute("create database if not exists snake")
    cursor.execute("use snake")
    cursor.execute("create table if not exists "+mode+" (name varchar(20) not null, score integer not null, time char(5) not null)")
    cursor.execute("select * from "+mode)
    data = cursor.fetchall()
    found = False
    for row in data:
        if row[0] == name:
            if row [1] < score:
                found = True
                cursor.execute("update "+mode+" set score = {}, time = '{}' where name = '{}' ".format(score,time,name))
                break
            else:
                break
    if not found:
        cursor.execute("insert into "+mode+" values ('{}',{},'{}')".format(name,score,time))
    mycon.commit()
    mycon.close()

def scoreboard():

    win.fill(White)
    flag = True
    while flag:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                close()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    close()

        win.fill(White)

        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        if 500 < mouse[0] < 700 and 270 < mouse[1] < 320:
            drawButton(Blue,(500, 270, 200, 50), "Easy Mode", White, 20)
            if click[0] == 1:
                click_sound.play()
                flag = not flag
                pygame.time.delay(150)
                access("easy")
        else:
            drawButton(Yellow, (500, 270, 200, 50), "Easy Mode", Black, 20)


        if 500 < mouse[0] < 700 and 330 < mouse[1] < 380:
            drawButton(Blue,(500, 330, 200, 50), "Hard Mode", White, 20)
            if click[0] == 1:
                click_sound.play()
                flag = not flag
                pygame.time.delay(150)
                access("hard")
        else:
            drawButton(Yellow,(500, 330, 200, 50), "Hard Mode", Black, 20)

        pygame.display.update()

def access(mode):
    global host,user,passwd
    clock = pygame.time.Clock()
    host = InputBox(150, 135, 140, 32)
    user = InputBox(150, 185, 140, 32)
    passwd = InputBox(550, 185, 140, 32)
    list = [host, user, passwd]
    done = False

    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                close()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    close()
            for box in list:
                box.handle_event(event)
                box.update()

        win.fill(White)
        words("Enter your MySQL details so your account can be accessed", 30, Black, width // 2, 50)
        words("Host:", 20, Black, 100, 150)
        words("User:", 20, Black, 100, 200)
        words("Passwd:", 20, Black, 500, 200)

        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        if 500 < mouse[0] < 700 and 500 < mouse[1] < 550:
            drawButton(Blue, (500, 500, 200, 50), "Submit", White, 20)
            if click[0] == 1:
                click_sound.play()
                done = not done
                pygame.time.delay(150)
                access_submit(mode)
        else:
            drawButton(Yellow, (500, 500, 200, 50), "Submit", Black, 20)

        for box in list:
            box.draw(win)

        pygame.display.update()
        clock.tick(30)

def access_submit(mode):

    mycon = sqltor.connect(host=host.text, user=user.text, passwd=passwd.text)
    cursor = mycon.cursor()
    cursor.execute("create database if not exists snake")
    cursor.execute("use snake")
    cursor.execute("create table if not exists " + mode + " (name varchar(20) not null, score integer not null, time char(5) not null)")
    cursor.execute("select * from "+mode)
    data = cursor.fetchall()
    mycon.close()
    scoreboard_display(data,mode)

def scoreboard_display(data,mode):

    scoreio = True

    while scoreio:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                close()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    close()
        win.fill(White)
        words("('Name',Score,'Time Taken')",15,(255,0,0),width//2-20,50)

        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        if 1000 < mouse[0] < 1120 and 40 < mouse[1] < 65:
            drawButton(Blue, (1000, 40, 120, 25), "Delete all scores", White, 10)
            if click[0] == 1:
                click_sound.play()
                scoreio = not scoreio
                pygame.time.delay(150)
                delete_scores(mode)
        else:
            drawButton(Yellow, (1000, 40, 120, 25), "Delete all scores", Black, 10)
        if 1000 < mouse[0] < 1120 and 70 < mouse[1] < 95:
            drawButton(Blue, (1000, 70, 120, 25), "Back to Main Menu", White, 10)
            if click[0] == 1:
                click_sound.play()
                scoreio = not scoreio
                pygame.time.delay(150)
                main_menu()
        else:
            drawButton(Yellow, (1000, 70, 120, 25), "Back to Main Menu", Black, 10)

        x = 30
        y = 100
        count = 0
        for row in data:
            count+=1
            words(str(count), 15, (255,0,0),x,y)
            words(str(row),15,Black,x+135,y)
            y += 50
            if y == height:

                x += 350
                y = 100
        pygame.display.update()

def delete_scores(mode):
    mycon = sqltor.connect(host=host.text, user=user.text, passwd=passwd.text)
    cursor = mycon.cursor()
    cursor.execute("use snake")
    cursor.execute("drop table "+mode)
    mycon.close()
    main_menu()

########################################################################################################################

# General utility functions used throughout the game

def words(text,size,color,x_location,y_location):
    font = resource_path("8-bit.ttf")
    type = pygame.font.Font(font, size)
    words = type.render(text,True,color)
    wordsRect = words.get_rect()
    wordsRect.center = (x_location,y_location)
    win.blit(words, wordsRect)

def score(size,x,y,snake,color = Black):
    score_keeper = "Score: "+str(len(snake.body)-1)
    words(score_keeper,size,color,x,y)

def timer(size,x,y,start_time):
    global counting_string
    counting_time = pygame.time.get_ticks() - start_time

    # change milliseconds into minutes, seconds, milliseconds
    counting_minutes = str(counting_time // 60000).zfill(2)
    counting_seconds = str((counting_time % 60000) // 1000).zfill(2)

    counting_string = "%s:%s" % (counting_minutes, counting_seconds)
    words(counting_string,size,Black,x,y)

def drawGrid():
    sizebtnr = height//columns
    sizebtnc = width//rows
    x = 0
    for i in range(columns+23):
        x = x + sizebtnr
        y = 25
        for j in range(rows-26):
            y = y + sizebtnc
            pygame.draw.circle(win, (150, 150, 150), (x,y), 3)


def drawButton(color,position,text,text_color,size):
    pygame.draw.rect(win, color, position)
    words(text, size, text_color, position[0] + (position[2] // 2), position[1] + (position[3] // 2))


def close():
    pygame.quit()
    sys.exit()

########################################################################################################################

# All the functions related to controlling the snakes

def movement(snake, keys):

    if keys[snake.left_key]:
        if snake.dirnx == 1 and snake.dirny == 0:
            pass
        else:
            snake.dirnx = -1
            snake.dirny = 0
            snake.turns[snake.head.pos[:]] = [snake.dirnx, snake.dirny]

    elif keys[snake.right_key]:
        if snake.dirnx == -1 and snake.dirny == 0:
            pass
        else:
            snake.dirnx = 1
            snake.dirny = 0
            snake.turns[snake.head.pos[:]] = [snake.dirnx, snake.dirny]

    elif keys[snake.up_key]:
        if snake.dirnx == 0 and snake.dirny == 1 and len(snake.body) > 1:
            pass
        else:
            snake.dirnx = 0
            snake.dirny = -1
            snake.turns[snake.head.pos[:]] = [snake.dirnx, snake.dirny]

    elif keys[snake.down_key]:
        if snake.dirnx == 0 and snake.dirny == -1:
            pass
        else:
            snake.dirnx = 0
            snake.dirny = 1
            snake.turns[snake.head.pos[:]] = [snake.dirnx, snake.dirny]

# Edward the Algorithm. This is a rudimentary algorithm that guides the snake head to the target fruit.

def moveAI(snake,snack):
    head = snake.body[0]
    if snake.dirnx == 1:
        if snack.pos[1] > head.pos[1]:
            snake.dirnx = 0
            snake.dirny = 1
            snake.turns[snake.head.pos[:]] = [snake.dirnx, snake.dirny]
        elif snack.pos[1] < head.pos[1]:
            snake.dirnx = 0
            snake.dirny = -1
            snake.turns[snake.head.pos[:]] = [snake.dirnx, snake.dirny]
        else:
            pass
    elif snake.dirnx == -1:
        if snack.pos[1] > head.pos[1]:
            snake.dirnx = 0
            snake.dirny = 1
            snake.turns[snake.head.pos[:]] = [snake.dirnx, snake.dirny]
        elif snack.pos[1] < head.pos[1]:
            snake.dirnx = 0
            snake.dirny = -1
            snake.turns[snake.head.pos[:]] = [snake.dirnx, snake.dirny]
        else:
            pass
    elif snake.dirny == 1:
        if snack.pos[0] > head.pos[0]:
            snake.dirnx = 1
            snake.dirny = 0
            snake.turns[snake.head.pos[:]] = [snake.dirnx, snake.dirny]
        elif snack.pos[0] < head.pos[0]:
            snake.dirnx = -1
            snake.dirny = 0
            snake.turns[snake.head.pos[:]] = [snake.dirnx, snake.dirny]
        else:
            pass
    elif snake.dirny == -1:
        if snack.pos[0] > head.pos[0]:
            snake.dirnx = 1
            snake.dirny = 0
            snake.turns[snake.head.pos[:]] = [snake.dirnx, snake.dirny]
        elif snack.pos[0] < head.pos[0]:
            snake.dirnx = -1
            snake.dirny = 0
            snake.turns[snake.head.pos[:]] = [snake.dirnx, snake.dirny]
        else:
            pass

########################################################################################################################

# General functions related to the flow of the game

def game_over(end_text,play_again):

    over = True
    while over:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                close()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    close()
        win.fill(White)
        words("GAME OVER",50,Black,width//2,(height//2)-20)
        words(end_text,30,Black,width//2,(height//2)+30)

        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        if 610 < mouse[0] < 810 and 400 < mouse[1] < 450:
            drawButton(Blue, (610, 400, 200, 50), "Main Menu", White, 20)
            if click[0] == 1:
                click_sound.play()
                over = not over
                pygame.time.delay(150)
                pygame.mixer.music.load(resource_path("Music\\Menu music.mp3"))
                pygame.mixer.music.set_volume(0.70)
                pygame.mixer.music.play(-1)
                main_menu()
        else:
            drawButton(Yellow, (610, 400, 200, 50), "Main Menu", Black, 20)


        if 400 < mouse[0] < 600 and 400 < mouse[1] < 450:
            drawButton(Blue, (400, 400, 200, 50), "Play again", White, 20)
            if click[0] == 1:
                click_sound.play()
                over = not over
                play_again()
        else:
            drawButton(Yellow, (400, 400, 200, 50), "Play again", Black, 20)

        pygame.display.update()


def randomSnack(item):

    while True:
        x = random.randrange(1, rows - 1)
        y = random.randrange(2, columns - 1)
        if len(list(filter(lambda z: z.pos == (x, y), item))) > 0:
            continue
        else:
            break

    return (x,y)

def die(snake,mode,main):
    end = True
    size = 25
    xw = 90
    yh = 20
    pygame.mixer.music.fadeout(100)
    gameover_sound.play()
    score(size, xw, yh,snake)
    while end:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                close()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    close()
        win.fill(White)
        while size < 83 or xw < (width // 2) or yh < (height // 2):
            win.fill(White)
            if size < 83:
                size += 1
            if xw < (width // 2):
                xw += 1
            if yh < (height// 2):
                yh += 1
            score(size, xw, yh,snake)
            pygame.display.update()
        if size == 83:
            pygame.time.delay(1000)
            details(main,mode,len(snake.body)-1)
        pygame.display.update

# die2 is a the die function used by multiplayer modes

def die2(s,ss,main):
    end = True
    size = 25
    x1 = 90
    y1 = 20
    x2 = 1100
    y2 = 20
    pygame.mixer.music.fadeout(100)
    gameover_sound.play()
    score(size, x1, y1, s,Blue)
    score(size,x2,y2,ss, Yellow)
    while end:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                close()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    close()
        win.fill(White)
        while size < 60 or x1 < (width // 2) or y1 < ((height // 2)-30) or x2 > (width // 2) or y2 < ((height // 2)+30):
            win.fill(White)
            if size < 60:
                size += 1
            if x1 < (width // 2):
                x1 += 1
            if y1 < ((height // 2)-30):
                y1 += 1
            if x2 > (width // 2):
                x2 -= 1
            if y2 < ((height // 2)+30):
                y2 += 1

            score(size, x1, y1, s, Blue)
            score(size, x2, y2, ss, Yellow)
            pygame.display.update()
        if size == 60:
            pygame.time.delay(1000)
            if len(s.body)> len(ss.body):
                game_over("Blue won by " + str(len(s.body) - len(ss.body)) + " point(s)!", main)
            elif len(s.body) < len(ss.body):
                game_over("Yellow won by " + str(len(ss.body) - len(s.body)) + " point(s)!", main)
            else:
                game_over("It's a tie!", main)

        pygame.display.update


def redrawWindow(snake,snack,start_time):
    win.fill(White)
    snake.draw(win)
    drawGrid()
    snack.draw(win)
    score(20,90,20, snake)
    timer(20,1100,20,start_time)
    pygame.display.update()

#redrawWindow2 is only used by the multiplayer modes

def redrawWindow2(s,ss,snack,start_time):
    win.fill(White)
    s.draw(win)
    ss.draw(win)
    drawGrid()
    snack.draw(win)
    score(20,90,20,s,Blue)
    score(20,1100,20,ss, Yellow)
    timer(20,590,20, start_time)
    pygame.display.update()

########################################################################################################################

# All the game functions regarding the Singleplayer modes

def singleplayer_easy():
    pygame.time.delay(2000)
    pygame.mixer.music.load(resource_path("Music\\Game music.mp3"))
    pygame.mixer.music.set_volume(0.70)
    pygame.mixer.music.play(-1)
    s = snake(Blue, (10, 10), pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN)
    snack = cube(randomSnack(s.body), color=(255, 0, 0))

    clock = pygame.time.Clock()
    start_time = pygame.time.get_ticks()
    running = True

    while running:
        pygame.time.delay(75)
        clock.tick(60)
        s.move()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                close()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    close()
                keys = pygame.key.get_pressed()

                for key in keys:
                    movement(s, keys)

        if s.body[0].pos == snack.pos:
            eat_sound.play()
            s.addCube()
            snack = cube(randomSnack(s.body), color=(255, 0, 0))

        for x in range(len(s.body)):
            if s.body[x].pos in list(map(lambda z: z.pos, s.body[x + 1:])):
                hit_sound.play()
                pygame.time.delay(1000)
                die(s, "easy", singleplayer_easy)
                break

        redrawWindow(s, snack, start_time)

def singleplayer_hard():
    global sh
    pygame.time.delay(2000)
    pygame.mixer.music.load(resource_path("Music\\Game music.mp3"))
    pygame.mixer.music.set_volume(0.70)
    pygame.mixer.music.play(-1)
    sh = snakey(Blue, (10, 10), pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN)
    snack = cube(randomSnack(sh.body), color=(255, 0, 0))

    clock = pygame.time.Clock()
    start_time = pygame.time.get_ticks()

    running = True
    while running:
        t = 81
        for i in sh.body:
            t -= 1
        pygame.time.delay(t)
        clock.tick(60)
        sh.move()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                close()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    close()
                keys = pygame.key.get_pressed()

                for key in keys:
                    movement(sh, keys)
        if sh.body[0].pos == snack.pos:
            eat_sound.play()
            sh.addCube()
            snack = cube(randomSnack(sh.body), color=(255, 0, 0))

        for x in range(len(sh.body)):
            if sh.body[x].pos in list(map(lambda z: z.pos, sh.body[x + 1:])):
                hit_sound.play()
                pygame.time.delay(1000)
                die(sh, "hard", singleplayer_hard)
                break

        redrawWindow(sh, snack, start_time)

def singleplayer_e_instructions():
    win.fill(White)
    pygame.mixer.music.fadeout(3000)

    flag = True
    while flag:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                close()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    close()
        win.blit(singleplayer_easy_instructions,(120,80))
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        if 900 < mouse[0] < 1100 and 525 < mouse[1] < 575:
            drawButton(Blue, (900, 525, 200, 50), "Proceed", White, 20)
            if click[0] == 1:
                click_sound.play()
                flag = not flag

        else:
            drawButton(Yellow, (900, 525, 200, 50), "Proceed", Black, 20)
        pygame.display.update()


def singleplayer_h_instructions():
    win.fill(White)
    pygame.mixer.music.fadeout(3000)
    flag = True
    while flag:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                close()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    close()
        win.blit(singleplayer_hard_instructions,(120,80))
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        if 900 < mouse[0] < 1100 and 525 < mouse[1] < 575:
            drawButton(Blue, (900, 525, 200, 50), "Proceed", White, 20)
            if click[0] == 1:
                click_sound.play()
                flag = not flag

        else:
            drawButton(Yellow, (900, 525, 200, 50), "Proceed", Black, 20)
        pygame.display.update()



def singleplayer():
    win.fill(White)
    flag = True
    while flag:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                close()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    close()
        win.fill(White)

        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        if 500 < mouse[0] < 700 and 270 < mouse[1] < 320:
            drawButton(Blue, (500, 270, 200, 50), "Easy Mode", White, 20)
            if click[0] == 1:
                click_sound.play()
                flag = not flag
                pygame.time.delay(150)
                singleplayer_e_instructions()
                gamestart_sound.play()
                singleplayer_easy()
        else:
            drawButton(Yellow, (500, 270, 200, 50), "Easy Mode", Black, 20)



        if 500 < mouse[0] < 700 and 330 < mouse[1] < 380:
            drawButton(Blue, (500, 330, 200, 50), "Hard Mode", White, 20)
            if click[0] == 1:
                click_sound.play()
                flag = not flag
                pygame.time.delay(150)
                singleplayer_h_instructions()
                gamestart_sound.play()
                singleplayer_hard()
        else:
            drawButton(Yellow, (500, 330, 200, 50), "Hard Mode", Black, 20)

        pygame.display.update()

########################################################################################################################

# All the game functions related to the multiplayer modes of the game

def multiplayer_coop():
    pygame.time.delay(2000)
    pygame.mixer.music.load(resource_path("Music\\Game music.mp3"))
    pygame.mixer.music.set_volume(0.70)
    pygame.mixer.music.play(-1)
    s = snake(Blue, (10, 10), pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN)
    ss = snake(Yellow, (30, 10), pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s)
    snack = cube(randomSnack(s.body + ss.body), color=(255, 0, 0))

    clock = pygame.time.Clock()
    start_time = pygame.time.get_ticks()

    running = True

    while running:
        pygame.time.delay(85)
        clock.tick(60)
        s.move()
        ss.move()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                close()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    close()
                keys = pygame.key.get_pressed()

                for key in keys:
                    movement(s, keys)
                    movement(ss, keys)
        if s.body[0].pos == snack.pos:
            eat_sound.play()
            s.addCube()
            snack = cube(randomSnack(s.body + ss.body), color=(255, 0, 0))
        elif ss.body[0].pos == snack.pos:
            eat_sound.play()
            ss.addCube()
            snack = cube(randomSnack(s.body + ss.body), color=(255, 0, 0))

        for x in range(len(s.body)):
            if s.body[x].pos in list(map(lambda z: z.pos, s.body[x + 1:])) or s.body[x].pos in list(map(lambda z: z.pos, ss.body[x:])):
                hit_sound.play()
                pygame.time.delay(1000)
                die2(s, ss, multiplayer_coop)
                break
        for x in range(len(ss.body)):
            if ss.body[x].pos in list(map(lambda z: z.pos, ss.body[x + 1:])) or ss.body[x].pos in list(map(lambda z: z.pos, s.body[x:])):
                hit_sound.play()
                pygame.time.delay(1000)
                die2(s, ss, multiplayer_coop)
                break

        redrawWindow2(s, ss, snack, start_time)


def multiplayer_computer():
    pygame.time.delay(2000)
    pygame.mixer.music.load(resource_path("Music\\Game music.mp3"))
    pygame.mixer.music.set_volume(0.70)
    pygame.mixer.music.play(-1)
    s = snake(Blue, (10, 10), pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN)
    ss = snake(Yellow, (30, 10), pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s)
    snack = cube(randomSnack(s.body + ss.body), color=(255, 0, 0))

    clock = pygame.time.Clock()
    start_time = pygame.time.get_ticks()

    running = True

    while running:
        pygame.time.delay(85)
        clock.tick(60)
        s.move()
        ss.move()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                close()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    close()
                keys = pygame.key.get_pressed()

                for key in keys:
                    movement(s, keys)
        moveAI(ss, snack)
        if s.body[0].pos == snack.pos:
            eat_sound.play()
            s.addCube()
            snack = cube(randomSnack(s.body + ss.body), color=(255, 0, 0))
        elif ss.body[0].pos == snack.pos:
            eat_sound.play()
            ss.addCube()
            snack = cube(randomSnack(s.body + ss.body), color=(255, 0, 0))

        for x in range(len(s.body)):
            if s.body[x].pos in list(map(lambda z: z.pos, s.body[x + 1:])) or s.body[x].pos in list(map(lambda z: z.pos, ss.body[x:])):
                hit_sound.play()
                pygame.time.delay(1000)
                die2(s, ss, multiplayer_computer)
                break
        for x in range(len(ss.body)):
            if ss.body[x].pos in list(map(lambda z: z.pos, ss.body[x + 1:])) or ss.body[x].pos in list(map(lambda z: z.pos, s.body[x:])):
                hit_sound.play()
                pygame.time.delay(1000)
                die2( s, ss, multiplayer_computer)
                break

        redrawWindow2(s, ss, snack, start_time)

def multiplayer_co_op_instructions():
    win.fill(White)
    pygame.mixer.music.fadeout(3000)
    flag = True
    while flag:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                close()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    close()
        win.blit(multiplayer_coop_instructions,(120,80))
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        if 900 < mouse[0] < 1100 and 525 < mouse[1] < 575:
            drawButton(Blue, (900, 525, 200, 50), "Proceed", White, 20)
            if click[0] == 1:
                click_sound.play()
                flag = not flag

        else:
            drawButton(Yellow, (900, 525, 200, 50), "Proceed", Black, 20)
        pygame.display.update()

def multiplayer_comp_instructions():
    win.fill(White)
    pygame.mixer.music.fadeout(3000)

    flag = True
    while flag:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                close()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    close()
        win.blit(multiplayer_computer_instructions,(120,50))
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        if 900 < mouse[0] < 1100 and 525 < mouse[1] < 575:
            drawButton(Blue, (900, 525, 200, 50), "Proceed", White, 20)
            if click[0] == 1:
                click_sound.play()
                flag = not flag

        else:
            drawButton(Yellow, (900, 525, 200, 50), "Proceed", Black, 20)
        pygame.display.update()


def multiplayer():
    win.fill(White)
    flag = True
    while flag:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                close()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    close()

        win.fill(White)

        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        if 500 < mouse[0] < 700 and 270 < mouse[1] < 320:
            drawButton(Blue, (500, 270, 200, 50), "Co-Op Mode", White, 20)
            if click[0] == 1:
                click_sound.play()
                flag = not flag
                pygame.time.delay(150)
                multiplayer_co_op_instructions()
                gamestart_sound.play()
                multiplayer_coop()
        else:
            drawButton(Yellow, (500, 270, 200, 50), "Co-Op Mode", Black, 20)



        if 500 < mouse[0] < 700 and 330 < mouse[1] < 380:
            drawButton(Blue, (500, 330, 200, 50), "Computer Mode", White, 20)
            if click[0] == 1:
                click_sound.play()
                flag = not flag
                pygame.time.delay(150)
                multiplayer_comp_instructions()
                gamestart_sound.play()
                multiplayer_computer()
        else:
            drawButton(Yellow, (500, 330, 200, 50), "Computer Mode", Black, 20)

        pygame.display.update()

########################################################################################################################

# Intro functions of the game

def game_intro():
    pygame.mixer.music.load(resource_path("Music\\Menu music.mp3"))
    pygame.mixer.music.set_volume(0.70)
    pygame.mixer.music.play(-1)
    intro = True
    while intro:
        win.fill(White)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                close()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    close()
        words("Welcome!", 83, Black, width // 2,height // 2)
        pygame.display.update()
        pygame.time.delay(1000)
        intro = False
        main_menu()

def main_menu():

    menu = True
    while menu:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                close()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    close()
        win.fill(White)
        win.blit(logo,((width//2)-350,(height//2)-150))
        words("Python: The Game",55,Black,(width//2)+150,(height//2)-75)
        words("A game about pythons, made in Python!",25,(100,100,100),(width//2)+155,(height//2)-25)

        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        if 510 < mouse[0] < 710 and 350 < mouse[1] < 400:
            drawButton(Blue, (510, 350, 200, 50), "Singleplayer", White, 20)
            if click[0] == 1:
                click_sound.play()
                menu = not menu
                pygame.time.delay(150)
                singleplayer()
        else:
            drawButton(Yellow, (510, 350, 200, 50), "Singleplayer", Black, 20)



        if 510 < mouse[0] < 710 and 425 < mouse[1] < 475:
            drawButton(Blue, (510, 425, 200, 50), "Multiplayer", White, 20)
            if click[0] == 1:
                click_sound.play()
                menu = not menu
                pygame.time.delay(150)
                multiplayer()
        else:
            drawButton(Yellow, (510, 425, 200, 50), "Multiplayer", Black, 20)



        if 510 < mouse[0] < 710 and 500 < mouse[1] < 550:
            drawButton(Blue, (510, 500, 200, 50), "Scoreboards", White, 20)
            if click[0] == 1:
                click_sound.play()
                menu = not menu
                pygame.time.delay(150)
                scoreboard()
        else:
            drawButton(Yellow, (510, 500, 200, 50), "Scoreboards", Black, 20)

        pygame.display.update()

########################################################################################################################

#This is where the game starts

game_intro()
