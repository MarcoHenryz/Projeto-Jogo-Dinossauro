import pygame
from sys import exit
from random import randint, choice
import os
import json # ### Módulo para lidar com o arquivo de recordes

# --- PAINEL DE CONTROLE (AJUSTE AQUI PARA MUDAR A SENSAÇÃO DO JOGO) ---
GAME_WORLD_HEIGHT = 700.0 
PLAYER_SCALE_MULTIPLIER = 0.8
FONT_SCALE_MULTIPLIER = 0.9
PHYSICS_SPEED_MULTIPLIER = 1.2

# --- Inicialização ---
pygame.init()
try:
    display_info = pygame.display.Info()
    SCREEN_WIDTH, SCREEN_HEIGHT = display_info.current_w, display_info.current_h
except pygame.error:
    SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption('Runner')
clock = pygame.time.Clock()

# --- CONSTANTES RELATIVAS ---
SCALE_FACTOR = SCREEN_HEIGHT / GAME_WORLD_HEIGHT

# Posições e Tamanhos
GROUND_Y = int(SCREEN_HEIGHT * 0.75)
PLAYER_START_X = int(SCREEN_WIDTH * 0.1)
# ### Novos tamanhos de fonte para o ranking ###
FONT_SIZE_LARGE = int(SCREEN_HEIGHT * 0.125 * FONT_SCALE_MULTIPLIER)
FONT_SIZE_MEDIUM = int(SCREEN_HEIGHT * 0.08 * FONT_SCALE_MULTIPLIER)
FONT_SIZE_SMALL = int(SCREEN_HEIGHT * 0.05 * FONT_SCALE_MULTIPLIER)

# Física
GRAVITY_PULL = (1 * SCALE_FACTOR) * PHYSICS_SPEED_MULTIPLIER
JUMP_STRENGTH = (-20 * SCALE_FACTOR) * PHYSICS_SPEED_MULTIPLIER
OBSTACLE_SPEED = (6 * (SCREEN_WIDTH / 800.0)) * (SCALE_FACTOR / (SCREEN_HEIGHT/400))

# Cores
SKY_BLUE = (135, 206, 235)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GOLD_COLOR = (255, 215, 0) # Cor para o #1 do ranking

# ### FUNÇÕES PARA GERENCIAR O RANKING DE RECORDES ###
SCORES_FILE = "scores.json"
NUM_TOP_SCORES = 5

def load_scores():
    """Carrega a lista de recordes de um arquivo JSON. Retorna uma lista de zeros se não existir."""
    if not os.path.exists(SCORES_FILE):
        return [0] * NUM_TOP_SCORES
    
    try:
        with open(SCORES_FILE, 'r') as f:
            data = json.load(f)
            scores = data.get("scores", [0] * NUM_TOP_SCORES)
            while len(scores) < NUM_TOP_SCORES:
                scores.append(0)
            return sorted(scores, reverse=True)[:NUM_TOP_SCORES]
    except (IOError, json.JSONDecodeError):
        return [0] * NUM_TOP_SCORES

def save_scores(scores_list):
    """Salva a lista de recordes em um arquivo JSON."""
    try:
        with open(SCORES_FILE, 'w') as f:
            data = {"scores": scores_list}
            json.dump(data, f)
    except IOError:
        print("Erro ao salvar recordes.")

def update_leaderboard(new_score, leaderboard):
    """Adiciona um novo score à lista, mantém ordenada e com o tamanho correto."""
    leaderboard.append(new_score)
    leaderboard.sort(reverse=True)
    return leaderboard[:NUM_TOP_SCORES]

# ### FUNÇÃO AUXILIAR PARA CARREGAR E ESCALAR IMAGENS ###
def load_scaled_image(path, scale_factor):
    image = pygame.image.load(path).convert_alpha()
    size = image.get_size()
    new_size = (int(size[0] * scale_factor), int(size[1] * scale_factor))
    return pygame.transform.scale(image, new_size)

# --- Classes (sem alterações) ---
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        player_scale = SCALE_FACTOR * PLAYER_SCALE_MULTIPLIER
        player_walk1 = load_scaled_image('graphics/Player/player_walk_1.png', player_scale)
        player_walk2 = load_scaled_image('graphics/Player/player_walk_2.png', player_scale)
        self.player_walk = [player_walk1, player_walk2]
        self.player_index = 0
        self.player_jump = load_scaled_image('graphics/Player/jump.png', player_scale)

        self.image = self.player_walk[self.player_index]
        self.rect = self.image.get_rect(midbottom=(PLAYER_START_X, GROUND_Y))
        self.gravity = 0

        self.jump_sound = pygame.mixer.Sound('audio/jump.mp3')
        self.jump_sound.set_volume(0.1)

    def player_input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE] and self.rect.bottom >= GROUND_Y:
            self.gravity = JUMP_STRENGTH
            self.jump_sound.play()

    def apply_gravity(self):
        self.gravity += GRAVITY_PULL
        self.rect.y += self.gravity
        if self.rect.bottom >= GROUND_Y:
            self.rect.bottom = GROUND_Y
    
    def animation_state(self):
        if self.rect.bottom < GROUND_Y:
            self.image = self.player_jump
        else:
            self.player_index += 0.1
            if self.player_index >= len(self.player_walk): self.player_index = 0
            self.image = self.player_walk[int(self.player_index)]

    def update(self):
        self.player_input()
        self.apply_gravity()
        self.animation_state()

class Obstacle(pygame.sprite.Sprite):
    def __init__(self, type):
        super().__init__()
        if type == 'fly':
            fly_frame1 = load_scaled_image('graphics/Fly/Fly1.png', SCALE_FACTOR)
            fly_frame2 = load_scaled_image('graphics/Fly/Fly2.png', SCALE_FACTOR)
            self.frames = [fly_frame1, fly_frame2]
            y_pos = GROUND_Y - int(90 * SCALE_FACTOR)
        else:
            snail_frame1 = load_scaled_image('graphics/snail/snail1.png', SCALE_FACTOR)
            snail_frame2 = load_scaled_image('graphics/snail/snail2.png', SCALE_FACTOR)
            self.frames = [snail_frame1, snail_frame2]
            y_pos = GROUND_Y

        self.animation_index = 0
        self.image = self.frames[self.animation_index]
        self.rect = self.image.get_rect(midbottom=(randint(SCREEN_WIDTH + 100, SCREEN_WIDTH + 300), y_pos))

    def animation_state(self):
        self.animation_index += 0.1
        if self.animation_index >= len(self.frames): self.animation_index = 0
        self.image = self.frames[int(self.animation_index)]

    def update(self):
        self.animation_state()
        self.rect.x -= OBSTACLE_SPEED
        self.destroy()

    def destroy(self):
        if self.rect.right <= 0:
            self.kill()

def display_score():
    current_time = int(pygame.time.get_ticks() / 1000) - start_time
    score_surf = test_font_medium.render(f'Score: {current_time}', False, (64, 64, 64))
    score_rect = score_surf.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.1))
    screen.blit(score_surf, score_rect)
    return current_time

def collision_sprite():
    if pygame.sprite.spritecollide(player.sprite, obstacle_group, False):
        return False # Retorna False em caso de colisão
    return True

# --- Configuração Inicial do Jogo ---
test_font_large = pygame.font.Font('font/Pixeltype.ttf', FONT_SIZE_LARGE)
test_font_medium = pygame.font.Font('font/Pixeltype.ttf', FONT_SIZE_MEDIUM)
test_font_small = pygame.font.Font('font/Pixeltype.ttf', FONT_SIZE_SMALL)

game_active = False
start_time = 0
score = 0
scores_list = load_scores() # ### Carrega a lista de recordes ao iniciar

bg_Music = pygame.mixer.Sound('audio/music.wav')
bg_Music.set_volume(0.1)
bg_Music.play(loops=-1)

player = pygame.sprite.GroupSingle()
player.add(Player())
obstacle_group = pygame.sprite.Group()

sky_surface = load_scaled_image('graphics/Sky.png', SCREEN_WIDTH / 800) # Escala para largura
sky_surface = pygame.transform.scale(sky_surface, (SCREEN_WIDTH, SCREEN_HEIGHT))
ground_surface_orig = pygame.image.load('graphics/ground.png').convert()
ground_height = int(ground_surface_orig.get_height() * SCALE_FACTOR)
ground_surface = pygame.transform.scale(ground_surface_orig, (SCREEN_WIDTH, ground_height))

player_stand = load_scaled_image('graphics/Player/player_stand.png', SCALE_FACTOR * 2 * PLAYER_SCALE_MULTIPLIER)
player_stand_rect = player_stand.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))

game_message = test_font_medium.render('Pressione ESPACO para correr', False, (111, 196, 169))
game_message_rect = game_message.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.8))

obstacle_timer = pygame.USEREVENT + 1
pygame.time.set_timer(obstacle_timer, 1500)

# --- Loop Principal ---
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            pygame.quit()
            exit()

        if not game_active: # Eventos da tela inicial/game over
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    game_active = True
                    start_time = int(pygame.time.get_ticks() / 1000)
                    score = 0
                    obstacle_group.empty()
                    player.sprite.rect.midbottom = (PLAYER_START_X, GROUND_Y)
                    player.sprite.gravity = 0
                if event.key == pygame.K_x: # ### Reset secreto ###
                    scores_list = [0] * NUM_TOP_SCORES
                    save_scores(scores_list)
        else: # Eventos durante o jogo
            if event.type == obstacle_timer:
                obstacle_group.add(Obstacle(choice(['fly', 'snail', 'snail', 'snail'])))

    if game_active:
        screen.blit(sky_surface, (0, 0))
        screen.blit(ground_surface, (0, GROUND_Y))
        
        score = display_score()

        player.draw(screen)
        player.update()
        obstacle_group.draw(screen)
        obstacle_group.update()

        # ### LÓGICA DE COLISÃO E SALVAMENTO DE RECORDE ###
        if not collision_sprite():
            scores_list = update_leaderboard(score, scores_list) # Atualiza a lista
            save_scores(scores_list) # Salva no arquivo
            game_active = False # Volta para a tela inicial

    else: # Tela Inicial e de Game Over
        screen.fill((94, 129, 162))

        # --- ### LÓGICA ATUALIZADA COM RANKING REPOSICIONADO ### ---
        title_color = (111, 196, 169)
        ranking_color = title_color
        ranking_title_color = BLACK

        # Define a posição X central para o bloco do ranking
        # Mudei de 0.8 para 0.85 para mover mais para a direita
        RANKING_X_POS = SCREEN_WIDTH * 0.85

        if score == 0: # Se o jogo ainda não começou
            # Desenha o personagem e o título principal no centro
            screen.blit(player_stand, player_stand_rect)
            title_text = test_font_large.render('Corredor Pixelado', False, title_color)
            screen.blit(title_text, title_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.3)))
        else: # Se acabou de terminar uma partida
            score_message = test_font_large.render(f'Sua pontuacao: {score}', False, title_color)
            screen.blit(score_message, score_message.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.3)))
        
        # --- DESENHA O RANKING NA NOVA POSIÇÃO (MAIS EMBAIXO E À DIREITA) ---
        
        # Título do Ranking
        ranking_title = test_font_medium.render('Melhores Pontuacoes', False, ranking_title_color)
        # Usa RANKING_X_POS como o centro X e uma nova posição Y (0.4) para descer
        ranking_title_rect = ranking_title.get_rect(center=(RANKING_X_POS, SCREEN_HEIGHT * 0.4))
        screen.blit(ranking_title, ranking_title_rect)
        
        # Lista de Pontuações
        for i, s in enumerate(scores_list):
            entry_text = test_font_small.render(f"{i + 1}.   {s}", True, ranking_color)
            # A posição Y de cada entrada agora começa de 0.5 para baixo
            y_pos = SCREEN_HEIGHT * 0.5 + i * (test_font_small.get_height() * 1.3)
            
            # Posiciona cada entrada do ranking com base no centro X definido
            entry_rect = entry_text.get_rect(center=(RANKING_X_POS, y_pos))
            screen.blit(entry_text, entry_rect)

        # Mensagem para iniciar o jogo (agora no centro inferior)
        screen.blit(game_message, game_message.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.85)))

    pygame.display.update()
    clock.tick(60)