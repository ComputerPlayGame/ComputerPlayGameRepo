import PySimpleGUI as sg
import threading
from queue import Empty, Queue
import time

ROWS = 15
COLS = 15
CHESS_SIZE = 40
HALF_CHESS_SIZE = CHESS_SIZE // 2
WIDTH = COLS * CHESS_SIZE
HEIGHT = ROWS * CHESS_SIZE
BLACK_PLAYER = 1
WHITE_PLAYER = 2
EMPTY = 0
WIN_NUMBER = 5
MAX_SCORE = int(10e7)

def init_game():
    elements = []
    for i in range(ROWS):
        elements.append([EMPTY] * COLS)
    current_player = BLACK_PLAYER
    if sg.popup_yes_no("As black?") != "Yes":
        x, y = ROWS // 2, COLS // 2
        elements[x][y] = BLACK_PLAYER
        current_player = WHITE_PLAYER

    return elements, current_player 

def redraw_board(board, elements, highlight_xy = None):
    board.erase()
    for i in range(ROWS):
        board.draw_line((HALF_CHESS_SIZE, i * CHESS_SIZE + HALF_CHESS_SIZE), (WIDTH - HALF_CHESS_SIZE, i * CHESS_SIZE + HALF_CHESS_SIZE))
    for i in range(COLS):
        board.draw_line((i * CHESS_SIZE + HALF_CHESS_SIZE, HALF_CHESS_SIZE), (i * CHESS_SIZE + HALF_CHESS_SIZE, HEIGHT - HALF_CHESS_SIZE))

    for x in range(ROWS):
        for y in range(COLS):
            if elements[x][y] == BLACK_PLAYER:
                board.draw_circle((x * CHESS_SIZE + HALF_CHESS_SIZE, y * CHESS_SIZE + HALF_CHESS_SIZE), HALF_CHESS_SIZE, fill_color = "black")
            elif elements[x][y] == WHITE_PLAYER:
                board.draw_circle((x * CHESS_SIZE + HALF_CHESS_SIZE, y * CHESS_SIZE + HALF_CHESS_SIZE), HALF_CHESS_SIZE, fill_color = "white")

    if highlight_xy is not None:
        hx, hy = highlight_xy
        board.draw_rectangle((hx * CHESS_SIZE, hy * CHESS_SIZE), ((hx + 1) * CHESS_SIZE,  (hy + 1) * CHESS_SIZE), line_color = "red")

    x_range = [3, ROWS // 2, ROWS - 4]
    y_range = [3, COLS // 2, COLS - 4]
    for x in x_range:
        for y in y_range:
            board.draw_circle((x * CHESS_SIZE + HALF_CHESS_SIZE, y * CHESS_SIZE + HALF_CHESS_SIZE), 3, fill_color="black")

def screen_to_xy(screen_x, screen_y):
    return screen_x // CHESS_SIZE, screen_y // CHESS_SIZE

def change_player(current_player):
    if current_player == BLACK_PLAYER:
        current_player = WHITE_PLAYER
    else:
        current_player = BLACK_PLAYER
    return current_player

def count_number(elements, x, y, dx, dy, value):
    number = 0
    while x >= 0 and x < ROWS and y >= 0 and y < COLS and elements[x][y] == value:
        x += dx
        y += dy
        number += 1
    return number

def win(elements, x, y):
    value = elements[x][y]
    dirs = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]
    for i in range(0, len(dirs), 2):
        dx, dy = dirs[i]
        number = count_number(elements, x, y, dx, dy, value)
        dx, dy = dirs[i + 1]
        number += count_number(elements, x + dx, y + dy, dx, dy, value)
        if number >= WIN_NUMBER:
            return True
    return False

def win_message(player_value):
    if player_value == BLACK_PLAYER:
        return "Black win"
    else:
        return "White win"

def calc_score(value_number, left_empty_number, right_empty_number, right_value_number):
    if value_number >= WIN_NUMBER:
        return MAX_SCORE

    if value_number == WIN_NUMBER - 1 and left_empty_number > 0 and right_empty_number > 0:
        return MAX_SCORE // 2

    score = pow(3, value_number)
    if right_empty_number == 1:
        score = pow(3, value_number + right_value_number)

    if value_number + left_empty_number >= WIN_NUMBER and value_number + right_empty_number >= WIN_NUMBER:
        return score * 2 + min(left_empty_number, right_empty_number)

    return score + min(left_empty_number, right_empty_number)

def evaluate_one_dir(elements, player_value, sx, sy, lx, ly, dx, dy):
    score = 0
    while sx >= 0 and sx < ROWS and sy >= 0 and sy < COLS:
        x, y = sx, sy
        while x >= 0 and x < ROWS and y >= 0 and y < COLS:
            while x >= 0 and x < ROWS and y >= 0 and y < COLS and elements[x][y] != player_value:
                x += dx
                y += dy
            if x >= 0 and x < ROWS and y >= 0 and y < COLS:
                value_number = count_number(elements, x, y, dx, dy, player_value)
                left_empty_number = count_number(elements, x - dx, y - dy, -dx, -dy, EMPTY)
                right_empty_number = count_number(elements, x + value_number * dx, y + value_number * dy, dx, dy, EMPTY)
                right_value_number = count_number(elements, x + value_number * dx + right_empty_number * dx, y + value_number * dy + right_empty_number * dy, dx, dy, player_value)
                score += calc_score(value_number, left_empty_number, right_empty_number, right_value_number)
                x += (value_number + right_empty_number) * dx
                y += (value_number + right_empty_number) * dy
        sx += lx
        sy += ly
    return score
                
def evaluate(elements, player_value):
    score = 0
    score += evaluate_one_dir(elements, player_value, 0, 0, 1, 0, 0, 1)

    score += evaluate_one_dir(elements, player_value, 0, 0, 0, 1, 1, 0)
    
    score += evaluate_one_dir(elements, player_value, 0, 0, 1, 0, -1, 1)
    score += evaluate_one_dir(elements, player_value, ROWS - 1, 1, 0, 1, -1, 1)

    score += evaluate_one_dir(elements, player_value, ROWS - 1, 0, -1, 0, 1, 1)
    score += evaluate_one_dir(elements, player_value, 0, 1, 0, 1, 1, 1)
    return score

def evaluate_one_step(elements, x, y):
    value = elements[x][y]
    dirs = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]
    for i in range(0, len(dirs), 2):
        dx, dy = dirs[i]
        number = count_number(elements, x, y, dx, dy, value)
        dx, dy = dirs[i + 1]
        number += count_number(elements, x + dx, y + dy, dx, dy, value)

    return number

def in_range(elements, x, y):
    range_num = 2
    for i in range(range_num):
        cx = x + i
        cy = y
        if cx >= 0 and cx < ROWS and cy >= 0 and cy < COLS and elements[cx][cy] != EMPTY:
            return True
        cx = x + i
        cy = y + i
        if cx >= 0 and cx < ROWS and cy >= 0 and cy < COLS and elements[cx][cy] != EMPTY:
            return True
        cx = x + i
        cy = y - i
        if cx >= 0 and cx < ROWS and cy >= 0 and cy < COLS and elements[cx][cy] != EMPTY:
            return True
        cx = x - i
        cy = y
        if cx >= 0 and cx < ROWS and cy >= 0 and cy < COLS and elements[cx][cy] != EMPTY:
            return True
        cx = x - i
        cy = y + i
        if cx >= 0 and cx < ROWS and cy >= 0 and cy < COLS and elements[cx][cy] != EMPTY:
            return True
        cx = x - i
        cy = y - i
        if cx >= 0 and cx < ROWS and cy >= 0 and cy < COLS and elements[cx][cy] != EMPTY:
            return True
        cx = x
        cy = y + i
        if cx >= 0 and cx < ROWS and cy >= 0 and cy < COLS and elements[cx][cy] != EMPTY:
            return True
        cx = x
        cy = y - i
        if cx >= 0 and cx < ROWS and cy >= 0 and cy < COLS and elements[cx][cy] != EMPTY:
            return True

    return False

def alpha_beta_search(elements, player_value, depth, alpha, beta):
    best_score, best_x, best_y = -MAX_SCORE - 1, None, None

    search_list = []
    for x in range(ROWS):
        for y in range(COLS):
            if elements[x][y] == EMPTY and in_range(elements, x, y):
                elements[x][y] = player_value
                search_list.append((-evaluate_one_step(elements, x, y), x, y))
                elements[x][y] = EMPTY
    search_list.sort()
    for _, x, y in search_list:
        elements[x][y] = player_value
        if win(elements, x, y):
            elements[x][y] = EMPTY
            return MAX_SCORE, x, y
        if depth > 1:
            score, _, _ = alpha_beta_search(elements, change_player(player_value), depth-1, -beta, -alpha)
            score = -score
        else:
            score = evaluate(elements, player_value) - int(evaluate(elements, change_player(player_value)) * 1.2)
        elements[x][y] = EMPTY
        if score >= beta:
            return score, x, y
        if score > best_score or (score == best_score and best_x is None):
            best_score, best_x, best_y = score, x, y
        if best_score > alpha:
            alpha = best_score
    return best_score, best_x, best_y

def computer_move(elements, player_value):
    score, x, y = alpha_beta_search(elements, player_value, 4, -MAX_SCORE, MAX_SCORE)
    elements[x][y] = player_value
    return score, x, y

def computer_move_thread(elements, player_value, message_queue):
    st = time.time()
    score, x, y = computer_move(elements, player_value)
    et = time.time()
    print(f"it takes {et - st}, score = {score}, x = {x}, y = {y}")
    message_queue.put((x, y))


if __name__ == "__main__":
    board = sg.Graph((WIDTH, HEIGHT), (0, 0), (WIDTH, HEIGHT), background_color='white', key='-GRAPH-', change_submits=True)
    layout = [[board], [sg.Button("New")]]
    window = sg.Window("Gobang", layout)
    elements = None
    current_player = BLACK_PLAYER
    human_player = None
    message_queue = Queue()
    while True:
        event, values = window.read(timeout=200)
        if event == sg.WIN_CLOSED:
            break
        elif event == "New":
            elements, current_player = init_game()
            human_player = current_player
            redraw_board(board, elements)
        elif event == "-GRAPH-" and human_player == current_player:
            if elements is not None:
                screen_x, screen_y = values["-GRAPH-"]
                x, y = screen_to_xy(screen_x, screen_y)
                print(x, y, current_player)
                elements[x][y] = current_player
                redraw_board(board, elements, (x, y))
                if win(elements, x, y):
                    sg.popup(win_message(current_player))
                else:
                    current_player = change_player(current_player)
                    threading.Thread(target = computer_move_thread, args = (elements, current_player, message_queue)).start()

        try:
            x, y = message_queue.get_nowait()
            elements[x][y] = current_player
            redraw_board(board, elements, (x, y))
            if win(elements, x, y):
                sg.popup(win_message(current_player))
            else:
                current_player = change_player(current_player)
        except Empty:
            pass

    window.close()
