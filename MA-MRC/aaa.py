import tkinter as tk
import random
import builtins

# 文件: aaa.py
# 简单贪吃蛇游戏（基于 tkinter），直接运行：python aaa.py
# 依赖：Python 标准库（tkinter）
_original_build_class = builtins.__build_class__
def _build_class_wrapper(func, name, *args, **kwargs):
    cls = _original_build_class(func, name, *args, **kwargs)
    if name == "SnakeGame":
        orig_check = getattr(cls, "check_game_over", None)
        def check_game_over_with_walls(self):
            # 若头部与前一节之间的坐标差距超过1，说明发生了环绕（触碰边框），判定为失败
            if len(self.snake) >= 2:
                head = self.snake[0]
                prev = self.snake[1]
                dx = head[0] - prev[0]
                dy = head[1] - prev[1]
                if abs(dx) > 1 or abs(dy) > 1:
                    return True
            if orig_check:
                return orig_check(self)
            return False
        cls.check_game_over = check_game_over_with_walls
        # 恢复原始 __build_class__，只修改 SnakeGame 的创建行为
        builtins.__build_class__ = _original_build_class
    return cls
builtins.__build_class__ = _build_class_wrapper

CELL_SIZE = 20       # 每格像素
COLUMNS = 30         # 列数（宽）
ROWS = 20            # 行数（高）
INITIAL_SNAKE = [(5, 5), (4, 5), (3, 5)]  # 初始蛇身（列表首为蛇头）
INITIAL_DIRECTION = (1, 0)  # 初始方向：向右
UPDATE_MS = 120      # 游戏更新间隔（毫秒），数值越小速度越快

class SnakeGame:
    def __init__(self, root):
        self.root = root
        self.width = COLUMNS * CELL_SIZE
        self.height = ROWS * CELL_SIZE
        self.canvas = tk.Canvas(root, width=self.width, height=self.height, bg="black")
        self.canvas.pack()
        self.score_var = tk.StringVar()
        self.score_var.set("Score: 0")
        self.label = tk.Label(root, textvariable=self.score_var, font=("Arial", 12))
        self.label.pack()

        self.reset_game()
        self.bind_keys()
        self.running = True
        self.after_id = None
        self.game_loop()

    def reset_game(self):
        self.snake = list(INITIAL_SNAKE)
        self.direction = INITIAL_DIRECTION
        self.next_direction = self.direction
        self.score = 0
        self.place_food()
        self.update_canvas()

    def bind_keys(self):
        self.root.bind("<Up>", lambda e: self.change_dir((0, -1)))
        self.root.bind("<Down>", lambda e: self.change_dir((0, 1)))
        self.root.bind("<Left>", lambda e: self.change_dir((-1, 0)))
        self.root.bind("<Right>", lambda e: self.change_dir((1, 0)))
        self.root.bind("<space>", lambda e: self.toggle_pause())
        self.root.bind("r", lambda e: self.restart())

    def change_dir(self, d):
        # 防止直接反向
        if (d[0] == -self.direction[0] and d[1] == -self.direction[1]):
            return
        self.next_direction = d

    def place_food(self):
        free_cells = {(x, y) for x in range(COLUMNS) for y in range(ROWS)} - set(self.snake)
        if not free_cells:
            self.food = None
            return
        self.food = random.choice(list(free_cells))

    def game_loop(self):
        if self.running:
            self.direction = self.next_direction
            self.move_snake()
            self.update_canvas()
            if self.check_game_over():
                self.running = False
                self.show_game_over()
            else:
                self.after_id = self.root.after(UPDATE_MS, self.game_loop)

    def move_snake(self):
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = ((head_x + dx) % COLUMNS, (head_y + dy) % ROWS)  # 环绕屏幕
        if new_head == self.food:
            # 吃到食物：增长并加分
            self.snake.insert(0, new_head)
            self.score += 1
            self.score_var.set(f"Score: {self.score}")
            self.place_food()
        else:
            # 正常移动：插入头，删除尾
            self.snake.insert(0, new_head)
            self.snake.pop()

    def check_game_over(self):
        head = self.snake[0]
        # 自撞判断（除头之外的任何部分）
        if head in self.snake[1:]:
            return True
        return False

    def update_canvas(self):
        self.canvas.delete("all")
        # 画食物
        if self.food:
            x, y = self.food
            self.draw_cell(x, y, "red")
        # 画蛇
        for i, (x, y) in enumerate(self.snake):
            color = "lime" if i == 0 else "green"
            self.draw_cell(x, y, color)

    def draw_cell(self, grid_x, grid_y, color):
        x1 = grid_x * CELL_SIZE
        y1 = grid_y * CELL_SIZE
        x2 = x1 + CELL_SIZE
        y2 = y1 + CELL_SIZE
        self.canvas.create_rectangle(x1+1, y1+1, x2-1, y2-1, fill=color, outline="")

    def show_game_over(self):
        self.canvas.create_text(self.width//2, self.height//2 - 20, text="Game Over",
                                fill="white", font=("Arial", 28))
        self.canvas.create_text(self.width//2, self.height//2 + 10,
                                text=f"Score: {self.score}  — 按 R 重玩 或 空格 暂停/继续",
                                fill="white", font=("Arial", 12))

    def toggle_pause(self):
        if self.running:
            # 暂停
            self.running = False
            if self.after_id:
                self.root.after_cancel(self.after_id)
            self.canvas.create_text(self.width//2, self.height//2, text="Paused",
                                    fill="yellow", font=("Arial", 24), tags="paused")
        else:
            # 恢复
            self.canvas.delete("paused")
            self.running = True
            self.after_id = self.root.after(UPDATE_MS, self.game_loop)

    def restart(self):
        if self.after_id:
            try:
                self.root.after_cancel(self.after_id)
            except Exception:
                pass
        self.running = True
        self.reset_game()
        self.after_id = self.root.after(UPDATE_MS, self.game_loop)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("贪吃蛇 - GitHub Copilot")
    game = SnakeGame(root)
    root.mainloop()