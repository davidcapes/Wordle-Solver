import pygame
import sys
import string

from WordleSolver import *

# Define Static Parameters
BOX_SIZE = 100
DIMENSIONS = (COLUMNS * BOX_SIZE, (ROWS + 1) * BOX_SIZE)

NULL_WORD = [NULL_CHAR for _ in range(ROWS)]
ALPHABET = string.ascii_lowercase

# Initialize Game
pygame.init()
screen = pygame.display.set_mode(DIMENSIONS)
pygame.display.set_caption("Wordle Solver")
pygame.display.set_icon(pygame.image.load('../skins/Icon.png'))

# Load Images
GREEN_IMAGE = pygame.image.load('../skins/colors/Green.png')
GREY_IMAGE = pygame.image.load('../skins/colors/Grey.png')
YELLOW_IMAGE = pygame.image.load('../skins/colors/Yellow.png')

SELECTED_IMAGE = pygame.image.load('../skins/misc/Selected.png')
TEXTBOX_IMAGE = pygame.image.load('../skins/misc/Textbox.png')

char_image_dict = {}
for c in ALPHABET:
    char_image_dict[c] = pygame.image.load('../skins/letters/' + c + '.png')
char_image_dict[NULL_CHAR] = pygame.image.load('../skins/letters/null.png')
color_image_dict = {Color.GREEN: GREEN_IMAGE, Color.GREY: GREY_IMAGE, Color.YELLOW: YELLOW_IMAGE}

# Initialize dynamic variables.
selected_row = 0
selected_column = 0
choice_word = NULL_WORD
constraints = Constraints()
words_to_exclude = set()

# Main loop.
while True:
    for event in pygame.event.get():

        # Exit Game.
        if event.type == pygame.QUIT:
            sys.exit()

        # Select different cell with mouse.
        if event.type == pygame.MOUSEBUTTONDOWN:
            clicked_row = event.pos[1] // BOX_SIZE
            clicked_column = event.pos[0] // BOX_SIZE
            if clicked_row == selected_row and clicked_column == selected_column:
                if constraints.grid[selected_row][selected_column].char != NULL_CHAR:
                    color = constraints.grid[selected_row][selected_column].color.next_color()
                    constraints.grid[selected_row][selected_column].color = color
                    choice_word = NULL_WORD
                    words_to_exclude.clear()
            elif 0 <= clicked_row < ROWS and 0 <= clicked_column < COLUMNS:
                selected_row = clicked_row
                selected_column = clicked_column

        # Get keyboard key.
        if event.type == pygame.KEYDOWN:

            # Exit window.
            if event.key == pygame.K_ESCAPE:
                exit()

            # Change cell color.
            if event.key == pygame.K_SPACE:
                if constraints.grid[selected_row][selected_column].char != NULL_CHAR:
                    color = constraints.grid[selected_row][selected_column].color.next_color()
                    constraints.grid[selected_row][selected_column].color = color
                    choice_word = NULL_WORD
                    words_to_exclude.clear()

            # Select different cell with arrows.
            if event.key == pygame.K_UP:
                selected_row = max(selected_row - 1, 0)
            if event.key == pygame.K_DOWN:
                selected_row = min(selected_row + 1, ROWS - 1)
            if event.key == pygame.K_LEFT:
                selected_column = max(selected_column - 1, 0)
            if event.key == pygame.K_RIGHT:
                selected_column = min(selected_column + 1, COLUMNS - 1)

            # Type letter.
            char = NULL_CHAR
            for c in ALPHABET:
                if event.key == pygame.key.key_code(c):
                    char = c
                    break
            if char != NULL_CHAR:
                if constraints.get_first_blank() is not None:
                    selected_row, selected_column = constraints.get_first_blank()
                    constraints.grid[selected_row][selected_column].char = char
                    choice_word = NULL_WORD
                    words_to_exclude.clear()

            # Delete letter.
            if event.key == pygame.K_BACKSPACE:
                if constraints.get_last_char() is not None:
                    selected_row, selected_column = constraints.get_last_char()
                    constraints.grid[selected_row][selected_column].char = NULL_CHAR
                    constraints.grid[selected_row][selected_column].color = Color.GREY
                    choice_word = NULL_WORD
                    words_to_exclude.clear()
                    if constraints.get_last_char() is not None:
                        selected_row, selected_column = constraints.get_last_char()
                    else:
                        selected_row, selected_column = 0, 0

            # Calculate the best choice word.
            if event.key == pygame.K_RETURN:
                choice_word = choose_word(constraints, words_to_exclude=words_to_exclude)

            # Exclude current choice word from possible guess words.
            if event.key == pygame.K_RSHIFT or event.key == pygame.K_LSHIFT:
                if choice_word not in words_to_exclude and choice_word != NULL_WORD:
                    words_to_exclude.add(choice_word)
                choice_word = choose_word(constraints, words_to_exclude=words_to_exclude)

            # Clear list of excluded guess words.
            if event.key == pygame.K_TAB:
                words_to_exclude.clear()
                choice_word = choose_word(constraints, words_to_exclude=words_to_exclude)

    # Display wordle grid.
    for row in range(ROWS):
        for column in range(COLUMNS):
            color = constraints.grid[row][column].color
            if color in color_image_dict:
                screen.blit(color_image_dict[color], (column * BOX_SIZE, row * BOX_SIZE))
            char = constraints.grid[row][column].char
            if char != NULL_CHAR:
                screen.blit(char_image_dict[char], (column * BOX_SIZE, row * BOX_SIZE))
    screen.blit(SELECTED_IMAGE, (selected_column * BOX_SIZE, selected_row * BOX_SIZE))

    # Display solution word.
    screen.blit(TEXTBOX_IMAGE, (0, ROWS * BOX_SIZE))
    for column in range(COLUMNS):
        if choice_word != NULL_WORD:
            char = choice_word[column]
            screen.blit(char_image_dict[char], (column * BOX_SIZE, ROWS * BOX_SIZE))

    pygame.display.update()
