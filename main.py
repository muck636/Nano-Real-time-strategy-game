"""Run the game python main.py"""

import time

import pygame

import config as C
from ai import SimpleAI
from game import Game
from music import MusicController
from ui import UI, draw_start, start_choice_at


# Combine keyboard and screen-edge input into a camera movement direction.
def camera_pan_direction(keys, mouse_pos=None):
    horizontal = int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(keys[pygame.K_a] or keys[pygame.K_LEFT])
    vertical = int(keys[pygame.K_s] or keys[pygame.K_DOWN]) - int(keys[pygame.K_w] or keys[pygame.K_UP])
    if mouse_pos is not None:
        x, y = mouse_pos
        if 0 <= x < C.MAP_WIDTH and 0 <= y < C.HEIGHT:
            margin = C.CAMERA_EDGE_SCROLL_MARGIN
            edge_x = int(x >= C.MAP_WIDTH - margin) - int(x < margin)
            edge_y = int(y >= C.HEIGHT - margin) - int(y < margin)
            horizontal = horizontal or edge_x
            vertical = vertical or edge_y
    return horizontal, vertical


# Initialize Pygame and run the menu, input, simulation, rendering, and music loop.
def main():
    pygame.init()
    try:
        screen = pygame.display.set_mode((C.WIDTH, C.HEIGHT), pygame.SCALED, vsync=1)
    except (pygame.error, TypeError):
        screen = pygame.display.set_mode((C.WIDTH, C.HEIGHT))
    pygame.display.set_caption("Nano RTS")
    clock = pygame.time.Clock()
    previous_frame = time.perf_counter()
    simulation_step = 1 / C.FPS
    accumulator = 0.0
    ui = UI()
    music = MusicController()
    game = None
    computer = None
    running = True
    while running:
        clock.tick(C.RENDER_FPS)
        current_frame = time.perf_counter()
        dt = min(current_frame - previous_frame, 0.25)
        previous_frame = current_frame
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif game is None:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    faction = start_choice_at(event.pos)
                    if faction is not None:
                        game = Game(faction)
                    if game:
                        computer = SimpleAI(game.enemy)
                        ui = UI()
                        ui.center_on(*C.STARTS[game.player][0])
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
            else:
                if ui.console_open:
                    if event.type == pygame.KEYDOWN:
                        ui.handle_console_key(event, game)
                    continue
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and game.winner is None:
                        ui.console_open = True
                        ui.console_text = ""
                    elif event.key == pygame.K_ESCAPE:
                        if game.winner is not None:
                            running = False
                        else:
                            ui.build_kind = None
                    elif event.key == pygame.K_r:
                        game = None
                        computer = None
                        ui = UI()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    ui.handle_mouse_down(event, game)
                elif event.type == pygame.MOUSEBUTTONUP:
                    ui.handle_mouse_up(event, game)
        if game is None:
            accumulator = 0.0
            draw_start(screen, ui)
        else:
            if not ui.console_open:
                keys = pygame.key.get_pressed()
                mouse_pos = None
                if game.winner is None and pygame.mouse.get_focused() and pygame.key.get_focused():
                    mouse_pos = pygame.mouse.get_pos()
                horizontal, vertical = camera_pan_direction(keys, mouse_pos)
                if horizontal or vertical:
                    ui.pan(horizontal * C.CAMERA_SPEED * dt, vertical * C.CAMERA_SPEED * dt)
                accumulator = min(accumulator + dt, simulation_step * 5)
                while accumulator >= simulation_step and game.winner is None:
                    computer.update(game, simulation_step)
                    game.update(simulation_step)
                    accumulator -= simulation_step
                alpha = 1.0 if game.winner is not None else accumulator / simulation_step
            else:
                accumulator = 0.0
                alpha = 1.0
            ui.draw(screen, game, alpha)
        music.update(game)
        pygame.display.flip()
    music.stop()
    pygame.quit()


if __name__ == "__main__":
    main()
