import pyautogui
from PIL import Image, ImageTk, ImageDraw, ImageGrab
import tempfile
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, simpledialog
from tkinter.colorchooser import askcolor
import math
from tkinter.colorchooser import askcolor
import random


class ResizableCanvasApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Resizable Canvas")
        self.screen_width = root.winfo_screenwidth()
        self.screen_height = root.winfo_screenheight()
        self.canvas_frame = tk.Frame(root)
        self.canvas_frame.pack(fill=tk.BOTH, expand=False)
    
        self.canvas = tk.Canvas(self.canvas_frame, bg="white", width=self.screen_width-150, height=self.screen_height-150, cursor="sizing", highlightthickness=2,highlightbackground="blue", relief='ridge')
        self.active_drawing = False
        self.canvas.pack(anchor="nw")  
        self.pasted_items = []  
        
        self.dots = []
        self.pasted_images = [] 
        self.rectangle = None
        self.MouseInfo1 = (0, 0)
        self.MouseInfo2 = (0, 0)

        self.label1 = tk.Label(root, text="Mouse starting point: " + self.convertTuple(self.MouseInfo1))
        self.label2 = tk.Label(root, text="Mouse ending point: " + self.convertTuple(self.MouseInfo2))
        self.label1.pack()
        self.label2.pack()
        self.border = None

        self.zoom_factor = 1.0
        self.canvas_scrollbar = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL)
        self.canvas_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas_scrollbar.config(command=self.canvas.yview)
        self.root.bind("<MouseWheel>", self.zoom)
        self.current_color = "black"
        self.current_thickness = 2
        self.current_brush = None

        self.triangle_rotation = 0
        self.drawn_triangles = []
        self.is_drawing_triangle = False

        self.current_zoom = 100
        self.last_click_point = (0, 0)

        self.border_width = 2


        self.copy_button = tk.Button(root, text="Copy", command=self.copy_selection)
        self.paste_button = tk.Button(root, text="Paste", command=self.paste_selection)
        self.cut_button = tk.Button(root, text="Cut", command=self.cut_selected)

        self.move_button = tk.Button(root, text="Move", command=self.start_move_mode)
        self.apply_button = tk.Button(root, text="Apply", command=self.end_move_mode)
        self.select_button = tk.Button(root, text="Select", command=self.select_mode)
        
        self.select_button.pack()
        self.copy_button.pack()
        self.paste_button.pack()
        self.move_button.pack()
        self.apply_button.pack()
        self.cut_button.pack()

        self.draw = Image.new("RGB", (800, 800), "white")
        self.image_draw = ImageDraw.Draw(self.draw)

        self.setup_toolbar()
        self.setup_menu()


        self.serialized_selection = None

        self.move_mode = False

        self.pasted_image_item = None

        self.dashed_border = None

        self.blue_border = None

        self.canvas.bind("<ButtonPress-1>", self.start_resizing_action)
        self.canvas.bind("<B1-Motion>", self.handle_resizing_action)
        self.canvas.bind("<ButtonRelease-1>", self.stop_resizing_action)

        self.action = None
        self.resizing = False
        self.moving = False
        self.last_x = None
        self.last_y = None
        self.canvas_width = self.canvas.winfo_reqwidth()
        self.canvas_height = self.canvas.winfo_reqheight()
        self.resize_threshold = 5 
        self.min_canvas_size = 50  
        self.create_rectangle(1, 1, 1, 1)
    def setup_toolbar(self):
        self.toolbar = tk.Frame(self.root)
        self.toolbar.pack(fill="x")
        self.zoom_label = ttk.Label(self.toolbar, text="Zoom: 100%")
        self.zoom_label.pack(side=tk.LEFT, padx=10)
        self.active_select = False
        self.create_tool_button(self.toolbar, "Pencil", self.use_pencil_tool)
        self.create_tool_button(self.toolbar, "Eraser", self.use_eraser_tool)
        self.create_tool_button(self.toolbar, "Color Panel", self.open_color_panel)
        self.create_tool_button(self.toolbar, "Line Thickness", self.open_thickness_dialog)
        self.create_tool_button(self.toolbar, "Straight Line", self.draw_straight_line)
        self.create_tool_button(self.toolbar, "Brushe (Spray Paint)", self.use_spray_paint_brush)
        self.save_button = tk.Button(self.toolbar, text="Save", command=self.save_image)
        self.create_tool_button(self.toolbar, "Triangle", self.draw_triangle)
        self.create_tool_button(self.toolbar, "Rectangle", self.draw_rectangle)
        self.create_tool_button(self.toolbar, "Square", self.draw_square)
        self.create_tool_button(self.toolbar, "Circle", self.draw_circle)

        self.canvas.bind("<Button-1>", self.update_last_click_point)
        self.canvas.bind("<B1-Motion>", self.draw_temp_shape)
        self.canvas.bind("<ButtonRelease-1>", self.end_draw_shape)
        self.save_button.pack(side="left")

        self.open_button = tk.Button(self.toolbar, text="Open", command=self.open_image)
        self.open_button.pack(side="left")
        


    def create_tool_button(self, parent, text, command):
        button = tk.Button(parent, text=text, command=command)
        button.pack(side=tk.LEFT)

    def use_eraser_tool(self):
        self.current_brush = "Eraser"
        self.canvas.bind("<Button-1>", self.start_eraser_tool)
        self.canvas.bind("<B1-Motion>", self.draw_eraser_tool, add="+")

    def start_eraser_tool(self, event):
        self.active_drawing = False
        self.prev_x, self.prev_y = event.x, event.y

    def draw_eraser_tool(self, event):
        x, y = event.x, event.y
        brush_size = self.current_thickness 
        color = "white"  
        self.canvas.create_line(
            self.prev_x, self.prev_y, x, y,
            fill=color, width=brush_size, capstyle=tk.ROUND, joinstyle=tk.ROUND
        )
        self.prev_x, self.prev_y = x, y

    def use_pencil_tool(self):
        self.current_brush = "Pencil"
        self.canvas.bind("<Button-1>", self.start_pencil_tool)
        self.canvas.bind("<B1-Motion>", self.draw_pencil_tool, add="+")

    def start_pencil_tool(self, event):
        self.active_select = False
        self.active_drawing = True
        self.clear_selection()
        self.prev_x, self.prev_y = event.x, event.y

    def draw_pencil_tool(self, event):
        if self.active_drawing:
            x, y = event.x, event.y
            brush_size = self.current_thickness
            color = self.current_color
            self.canvas.create_line(
                self.prev_x, self.prev_y, x, y,
                fill=color, width=brush_size, capstyle=tk.ROUND, joinstyle=tk.ROUND
            )
            self.prev_x, self.prev_y = x, y

    def open_color_panel(self):
        color = askcolor()[1]
        if color:
            self.current_color = color

    def open_thickness_dialog(self):
        response = simpledialog.askinteger(
            "Line Thickness",
            "Select line thickness (1-100):",
            initialvalue=self.current_thickness,
            minvalue=1,
            maxvalue=100,
            parent=self.root 
        )
        if response is not None:
            self.current_thickness = response

    def draw_straight_line(self):
        self.current_brush = "Straight Line"
        self.canvas.bind("<Button-1>", self.start_straight_line)

    def start_straight_line(self, event):
        self.line_start_x, self.line_start_y = event.x, event.y

        self.canvas.bind("<B1-Motion>", self.draw_temp_line)
        self.canvas.bind("<ButtonRelease-1>", self.end_straight_line)

    def end_straight_line(self, event):
        x, y = event.x, event.y
        self.canvas.delete("temp_line")
        self.canvas.create_line(
            self.line_start_x, self.line_start_y,
            x, y,
            fill=self.current_color, width=self.current_thickness
        )
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")

    def draw_temp_line(self, event):
        x, y = event.x, event.y
        self.canvas.delete("temp_line")
        self.canvas.create_line(
            self.line_start_x, self.line_start_y,
            x, y,
            fill=self.current_color, width=self.current_thickness,
            tags="temp_line"
        )

    def use_spray_paint_brush(self):
        self.current_brush = "Spray Paint Brush"
        self.canvas.bind("<Button-1>", self.start_spray_paint_brush)
        self.canvas.bind("<B1-Motion>", self.draw_spray_paint_brush, add="+")

    def start_spray_paint_brush(self, event):
        self.prev_x, self.prev_y = event.x, event.y

    def draw_spray_paint_brush(self, event):
        x, y = event.x, event.y
        brush_size = self.current_thickness
        color = self.current_color
        for _ in range(50):
            x_offset = x + random.randint(-brush_size, brush_size)
            y_offset = y + random.randint(-brush_size, brush_size)
            self.canvas.create_oval(
                x_offset, y_offset,
                x_offset + 2, y_offset + 2,
                fill=color, outline="", width=0, stipple="gray12"
            )

    def draw_triangle(self):
        self.current_brush = "Triangle"
        self.is_drawing_triangle = True
        self.canvas.bind("<Button-1>", self.start_draw_shape)

    def draw_rectangle(self):
        self.current_brush = "Rectangle"
        self.canvas.bind("<Button-1>", self.start_draw_shape)

    def draw_square(self):
        self.current_brush = "Square"
        self.canvas.bind("<Button-1>", self.start_draw_shape)

    def draw_circle(self):
        self.current_brush = "Circle"
        self.canvas.bind("<Button-1>", self.start_draw_shape)

    def start_draw_shape(self, event):
        self.shape_start_x, self
    def start_draw_shape(self, event):
        self.shape_start_x, self.shape_start_y = event.x, event.y

        self.canvas.bind("<B1-Motion>", self.draw_temp_shape)
        self.canvas.bind("<ButtonRelease-1>", self.end_draw_shape)

    def end_draw_shape(self, event):
        x, y = event.x, event.y
        self.canvas.delete("temp_shape")
        shape_type = self.current_brush.lower()

        if shape_type == "triangle" and self.is_drawing_triangle:
            base_width = abs(x - self.shape_start_x)
            height = base_width * math.sqrt(3) / 2

            if y < self.shape_start_y:
                y1, y2, y3 = y + height, y, y + height
            else:
                y1, y2, y3 = y - height, y, y - height

            if x < self.shape_start_x:
                x1, x2, x3 = x + base_width / 2, x, x - base_width / 2
            else:
                x1, x2, x3 = x - base_width / 2, x, x + base_width / 2

            rotation_offset = math.radians(self.triangle_rotation)

            rotated_x1 = (x1 - self.shape_start_x) * math.cos(rotation_offset) - (y1 - self.shape_start_y) * math.sin(rotation_offset) + self.shape_start_x
            rotated_y1 = (x1 - self.shape_start_x) * math.sin(rotation_offset) + (y1 - self.shape_start_y) * math.cos(rotation_offset) + self.shape_start_y
            rotated_x2 = (x2 - self.shape_start_x) * math.cos(rotation_offset) - (y2 - self.shape_start_y) * math.sin(rotation_offset) + self.shape_start_x
            rotated_y2 = (x2 - self.shape_start_x) * math.sin(rotation_offset) + (y2 - self.shape_start_y) * math.cos(rotation_offset) + self.shape_start_y
            rotated_x3 = (x3 - self.shape_start_x) * math.cos(rotation_offset) - (y3 - self.shape_start_y) * math.sin(rotation_offset) + self.shape_start_x
            rotated_y3 = (x3 - self.shape_start_x) * math.sin(rotation_offset) + (y3 - self.shape_start_y) * math.cos(rotation_offset) + self.shape_start_y

            self.drawn_triangles.append((rotated_x1, rotated_y1, rotated_x2, rotated_y2, rotated_x3, rotated_y3, self.current_color, self.current_thickness))

            self.canvas.create_polygon(
                rotated_x1, rotated_y1, rotated_x2, rotated_y2, rotated_x3, rotated_y3,
                outline=self.current_color, width=self.current_thickness,
                fill=self.current_color
            )

        elif shape_type == "rectangle":
            x1, y1, x2, y2 = (
                self.shape_start_x, self.shape_start_y,
                x, y
            )
            self.drawn_triangles.append((x1, y1, x2, y2, self.current_color, self.current_thickness))
            self.canvas.create_rectangle(
                x1, y1, x2, y2,
                outline=self.current_color, width=self.current_thickness,
                fill=self.current_color
            )

        elif shape_type == "square":
            side_length = max(abs(x - self.shape_start_x), abs(y - self.shape_start_y))
            if x < self.shape_start_x:
                x1 = self.shape_start_x - side_length
            else:
                x1 = self.shape_start_x
            if y < self.shape_start_y:
                y1 = self.shape_start_y - side_length
            else:
                y1 = self.shape_start_y
            x2, y2 = x1 + side_length, y1 + side_length

            self.drawn_triangles.append((x1, y1, x2, y2, self.current_color, self.current_thickness))
            self.canvas.create_rectangle(
                x1, y1, x2, y2,
                outline=self.current_color, width=self.current_thickness,
                fill=self.current_color
            )

        elif shape_type == "circle":
            radius = math.sqrt((x - self.shape_start_x)**2 + (y - self.shape_start_y)**2)
            x1, y1, x2, y2 = (
                self.shape_start_x - radius, self.shape_start_y - radius,
                self.shape_start_x + radius, self.shape_start_y + radius
            )
            self.drawn_triangles.append((x1, y1, x2, y2, self.current_color, self.current_thickness))
            self.canvas.create_oval(
                x1, y1, x2, y2,
                outline=self.current_color, width=self.current_thickness,
                fill=self.current_color
            )

        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")

    def rotate_triangle(self):
        self.triangle_rotation = (self.triangle_rotation + 90) % 360

    def draw_temp_shape(self, event):
        x, y = event.x, event.y
        self.canvas.delete("temp_shape")
        shape_type = self.current_brush.lower()

        if shape_type == "triangle":
            base_width = abs(x - self.shape_start_x)
            height = base_width * math.sqrt(3) / 2

            if y < self.shape_start_y:
                y1, y2, y3 = y + height, y, y + height
            else:
                y1, y2, y3 = y - height, y, y - height

            if x < self.shape_start_x:
                x1, x2, x3 = x + base_width / 2, x, x - base_width / 2
            else:
                x1, x2, x3 = x - base_width / 2, x, x + base_width / 2

            self.canvas.create_polygon(
                x1, y1, x2, y2, x3, y3,
                outline=self.current_color, width=self.current_thickness,
                fill=self.current_color,
                tags="temp_shape"
            )

        elif shape_type == "rectangle":
            x1, y1, x2, y2 = (
                self.shape_start_x, self.shape_start_y,
                x, y
            )
            self.canvas.create_rectangle(
                x1, y1, x2, y2,
                outline=self.current_color, width=self.current_thickness,
                fill=self.current_color,
                tags="temp_shape"
            )

        elif shape_type == "square":
            side_length = max(abs(x - self.shape_start_x), abs(y - self.shape_start_y))
            if x < self.shape_start_x:
                x1 = self.shape_start_x - side_length
            else:
                x1 = self.shape_start_x
            if y < self.shape_start_y:
                y1 = self.shape_start_y - side_length
            else:
                y1 = self.shape_start_y
            x2, y2 = x1 + side_length, y1 + side_length

            self.canvas.create_rectangle(
                x1, y1, x2, y2,
                outline=self.current_color, width=self.current_thickness,
                fill=self.current_color,
                tags="temp_shape"
            )

        elif shape_type == "circle":
            radius = math.sqrt((x - self.shape_start_x)**2 + (y - self.shape_start_y)**2)
            x1, y1, x2, y2 = (
                self.shape_start_x - radius, self.shape_start_y - radius,
                self.shape_start_x + radius, self.shape_start_y + radius
            )
            self.canvas.create_oval(
                x1, y1, x2, y2,
                outline=self.current_color, width=self.current_thickness,
                fill=self.current_color,
                tags="temp_shape"
            )

    def redraw_shapes(self):
        self.canvas.delete("all")
        for triangle_data in self.drawn_triangles:
            x1, y1, x2, y2, x3, y3, color, thickness = triangle_data
            self.canvas.create_polygon(
                x1, y1, x2, y2, x3, y3,
                outline=color, width=thickness,
                fill=color
            )

    def update_last_click_point(self, event):
        self.last_click_point = (event.x, event.y)

    def zoom(self, event):
        central_point = (event.x, event.y)
        zoom_factor = 1.2 if event.delta > 0 else 1 / 1.2
        self.zoom_canvas(central_point, zoom_factor)

    def zoom_canvas(self, central_point, zoom_factor):
        self.canvas.scale("all", central_point[0], central_point[1], zoom_factor, zoom_factor)
        self.zoom_factor *= zoom_factor
        self.update_zoom_label()
        self.update_canvas_size()
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

    def update_zoom_label(self):
        zoom_percentage = int(self.zoom_factor * 100)
        self.zoom_label.config(text=f"Zoom: {zoom_percentage}%")

    def update_canvas_size(self):
        canvas_width = int(self.canvas.winfo_width() * self.zoom_factor)
        canvas_height = int(self.canvas.winfo_height() * self.zoom_factor)

        if canvas_width > self.canvas_width:
            canvas_width = self.canvas_width

        if canvas_height > self.canvas_height:
            canvas_height = self.canvas_height

        self.canvas_width = canvas_width
        self.canvas_height = canvas_height

        self.canvas.config(scrollregion=(0, 0, self.canvas_width, self.canvas_height))

    def save_image(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if file_path:
            x = self.root.winfo_rootx() + self.canvas.winfo_x()
            y = self.root.winfo_rooty() + self.canvas.winfo_y()
            x1 = x + self.canvas.winfo_width()
            y1 = y + self.canvas.winfo_height()
            original_highlightthickness = self.canvas.cget("highlightthickness")
            original_borderwidth = self.canvas.cget("borderwidth")
            self.canvas.config(highlightthickness=0, borderwidth=0)
            self.canvas.update_idletasks()  # Update the canvas
            ImageGrab.grab(bbox=(x, y, x1, y1)).save(file_path)
            self.canvas.config(highlightthickness=original_highlightthickness, borderwidth=original_borderwidth)
            self.canvas.update_idletasks()  # Restore original canvas configuration

    def open_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")])
        if file_path:
            self.draw = Image.open(file_path)
            self.image_draw = ImageDraw.Draw(self.draw)
    
            image_width, image_height = self.draw.size
    
            if image_width > self.canvas_width - 150 or image_height > self.canvas_height - 150:

                max_width = self.canvas_width - 150
                max_height = self.canvas_height - 150
                width_ratio = max_width / image_width
                height_ratio = max_height / image_height
                min_ratio = min(width_ratio, height_ratio)
                new_width = int(image_width * min_ratio)
                new_height = int(image_height * min_ratio)


                self.draw = self.draw.resize((new_width, new_height), Image.ANTIALIAS)

            self.canvas.delete("all")
    
            self.image_tk = ImageTk.PhotoImage(self.draw)
            tmpImage = self.canvas.create_image(0, 0, anchor="nw", image=self.image_tk)
            
                
    def drawing_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")])
        if file_path:
            self.draw = Image.open(file_path)
            self.image_draw = ImageDraw.Draw(self.draw)
    
            image_width, image_height = self.draw.size
    
            self.canvas.config(width=image_width, height=image_height)
    
            self.canvas.delete("all")
    
            self.image_tk = ImageTk.PhotoImage(self.draw)
            self.canvas.create_image(0, 0, anchor="nw", image=self.image_tk)

        
            self.image_tk = ImageTk.PhotoImage(self.draw)
            self.canvas.create_image(0, 0, anchor="nw", image=self.image_tk)

    def setup_menu(self):
        self.menu = tk.Menu(self.root)
        self.root.config(menu=self.menu)

        self.file_menu = tk.Menu(self.menu)
        self.menu.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Save", command=self.save_image)
        self.file_menu.add_command(label="Open", command=self.open_image)
    def select_mode(self):

        self.canvas.bind("<ButtonPress-1>", self.start_selection)
        self.canvas.bind("<B1-Motion>", self.update_selection)

    def create_dots(self):
        for dot in self.dots:
            self.canvas.delete(dot)
        
        dot_size = 5

        canvas_width = self.canvas.winfo_width()  # Use the current canvas width
        canvas_height = self.canvas.winfo_height()  # Use the current canvas height
        
        dot_coords = [
            (0 - dot_size, 0 - dot_size),                  # top-left
            (0 - dot_size, canvas_height + dot_size),     # bottom-left
            (canvas_width + dot_size, canvas_height + dot_size),  # bottom-right
        ]
        
        self.dots = []
        
        for (dot_x, dot_y) in dot_coords:
            dot = self.canvas.create_oval(
                dot_x, dot_y,
                dot_x + dot_size * 2, dot_y + dot_size * 2,
                fill="grey",
                outline="grey"
            )
            self.dots.append(dot)

    def start_resizing_action(self, event):
        current_width = self.canvas.winfo_width()
        current_height = self.canvas.winfo_height()
        mx, my = event.x, event.y
        self.last_x = mx

        if mx >= current_width - self.resize_threshold:
            if my >= current_height - self.resize_threshold:
                self.action = "resize_diag_br"
            else:
                self.action = "resize_right"
        elif my >= current_height - self.resize_threshold:
            self.action = "resize_down"
        else:
            self.action = "move"
        self.canvas.config(cursor="sizing")
        self.last_x = mx
        self.last_y = my

    def stop_resizing_action(self, event):
        self.action = None
        self.resizing = False
        self.moving = False
        self.canvas.config(cursor="sizing")

    def handle_resizing_action(self, event):
        if self.action:
            if self.action == "resize_right":
                self.resize_right(event)
            elif self.action == "resize_down":
                self.resize_down(event)
            elif self.action == "move":
                self.move_canvas(event)
            elif self.action == "resize_diag_br":
                self.resize_diag_br(event)

    def resize_left(self, event):
        if not self.resizing:
            self.resizing = True
            self.last_x = event.x  

        current_width = self.canvas.winfo_width()
        mx = event.x

        delta_x = mx - self.last_x  
        new_width = current_width - delta_x

        if new_width >= self.min_canvas_size:
            self.canvas.config(width=new_width)
            self.create_dots()
        else:
            
            event.x = self.last_x + current_width - self.min_canvas_size
        self.last_x = event.x


    def resize_right(self, event):
        if not self.resizing:
            self.resizing = True

        current_width = self.canvas.winfo_width()
        mx = event.x

        delta_x = mx - self.last_x  
        new_width = current_width + delta_x

        if new_width >= self.min_canvas_size:
            self.canvas.config(width=event.x)
            self.create_dots()
        self.last_x = mx

    def resize_up(self, event):
        if not self.resizing:
            self.resizing = True
            self.last_y = event.y
    
        current_height = self.canvas.winfo_height()
        my = event.y
    
        delta_y = my - self.last_y
        new_height = current_height - delta_y
    
        if new_height >= self.min_canvas_size:
            self.canvas.config(height=new_height)
            self.create_dots()
        else:
        
            event.y = self.last_y + current_height - self.min_canvas_size
        self.last_y = event.y

    def resize_down(self, event):
        if not self.resizing:
            self.resizing = True
            self.last_y = event.y

        current_height = self.canvas.winfo_height()
        my = event.y

        delta_y = my - self.last_y
        new_height = current_height + delta_y

        if new_height >= self.min_canvas_size:
            self.canvas.config(height=event.y)
            self.create_dots()
        self.last_y = my

    def move_canvas(self, event):
        if not self.moving:
            self.moving = True
            self.last_x = event.x
            self.last_y = event.y

        if self.moving:
            mx, my = event.x, event.y
            delta_x = mx - self.last_x
            delta_y = my - self.last_y

            self.canvas.scan_dragto(-delta_x, -delta_y, gain=1)
            self.create_dots()
            self.last_x = mx
            self.last_y = my

    def resize_diag_br(self, event):
        if not self.resizing:
            self.resizing = True
            self.last_x = event.x
            self.last_y = event.y

        current_width = self.canvas.winfo_width()
        current_height = self.canvas.winfo_height()
        mx, my = event.x, event.y

        delta_x = mx - self.last_x
        delta_y = my - self.last_y

        new_width = current_width + delta_x
        new_height = current_height + delta_y

        if new_width >= self.min_canvas_size and new_height >= self.min_canvas_size:
            self.canvas.config(width=event.x, height=event.y)
            self.create_dots()
        self.last_x = mx
        self.last_y = my

    def create_rectangle(self, x1, y1, x2, y2):
        self.rectangle = self.canvas.create_rectangle(x1, y1, x2, y2, fill="black")

    def start_selection(self, event):
        
            self.active_select = True
            self.MouseInfo1 = event.x, event.y
            self.label1.config(text="Mouse starting point: ({}, {})".format(self.MouseInfo1[0], self.MouseInfo1[1]))

            
            self.clear_selection()

    def update_selection(self, event):
        
        if self.active_select:
            self.MouseInfo2 = event.x, event.y
            self.label2.config(text="Mouse ending point: ({}, {})".format(self.MouseInfo2[0], self.MouseInfo2[1]))

            self.draw_selection()

    def clear_selection(self):
        if self.border:
            self.canvas.delete(self.border)

    def draw_selection(self):
        if self.active_select:
            self.clear_selection()

            x1, y1 = min(self.MouseInfo1[0], self.MouseInfo2[0]), min(self.MouseInfo1[1], self.MouseInfo2[1])
            x2, y2 = max(self.MouseInfo1[0], self.MouseInfo2[0]), max(self.MouseInfo1[1], self.MouseInfo2[1])

            x1 = max(x1, 0)
            x2 = min(x2, self.canvas_width)
            y1 = max(y1, 0)
            y2 = min(y2, self.canvas_height)

            if 0 <= x1 <= self.canvas_width and 0 <= x2 <= self.canvas_width and 0 <= y1 <= self.canvas_height and 0 <= y2 <= self.canvas_height:
                self.border = self.canvas.create_rectangle(
                    x1, y1, x2, y2, outline="red", width=self.border_width, dash=(4, 4)
                )

    def convertTuple(self, tup):
        result_str = ''
        for item in tup:
            result_str += str(item)
        return result_str

    def copy_selection(self):
        if self.border:
            x1, y1, x2, y2 = map(int, self.canvas.coords(self.border))  
            self.canvas.itemconfigure(self.border, state=tk.HIDDEN)
            self.canvas.itemconfigure(self.dashed_border, state=tk.HIDDEN)

            canvas_x, canvas_y = self.canvas.winfo_rootx(), self.canvas.winfo_rooty()

            global_x1, global_y1, global_x2, global_y2 = (
                x1 + canvas_x, y1 + canvas_y, x2 + canvas_x, y2 + canvas_y
            )

            screenshot = pyautogui.screenshot(region=(global_x1 + 2, global_y1 + 2, global_x2 - global_x1 - 4, global_y2 - global_y1 - 4))
            
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                temp_filename = temp_file.name
                temp_file.close()
                screenshot.save(temp_filename, "PNG")
            self.canvas.itemconfigure(self.border, state=tk.NORMAL)
            self.canvas.itemconfigure(self.dashed_border, state=tk.NORMAL)
            self.serialized_selection = temp_filename

    def cut_selected(self):
        if self.border:
            x1, y1, x2, y2 = map(int, self.canvas.coords(self.border))  
            self.canvas.itemconfigure(self.border, state=tk.HIDDEN)
            self.canvas.itemconfigure(self.dashed_border, state=tk.HIDDEN)
            self.canvas.update_idletasks()  

            canvas_x, canvas_y = self.canvas.winfo_rootx(), self.canvas.winfo_rooty()

            global_x1, global_y1, global_x2, global_y2 = (
                x1 + canvas_x, y1 + canvas_y, x2 + canvas_x, y2 + canvas_y
            )

            screenshot = pyautogui.screenshot(region=(global_x1, global_y1, global_x2 - global_x1, global_y2 - global_y1))
            
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                temp_filename = temp_file.name
                temp_file.close()
                screenshot.save(temp_filename, "PNG")
            self.canvas.itemconfigure(self.border, state=tk.NORMAL)
            self.canvas.itemconfigure(self.dashed_border, state=tk.NORMAL)
            self.canvas.update_idletasks() 

            self.serialized_selection = temp_filename

            self.pasted_image_item = self.canvas.create_rectangle(x1, y1, x2, y2, fill="white", outline="")

    def paste_selection(self):
        if self.serialized_selection:
            image = Image.open(self.serialized_selection)
            pasted_image = ImageTk.PhotoImage(image)

            canvas_x, canvas_y = self.canvas.winfo_rootx(), self.canvas.winfo_rooty()

            x1, y1, x2, y2 = map(int, self.canvas.coords(self.border))
            x1 += canvas_x
            y1 += canvas_y
            x2 += canvas_x
            y2 += canvas_y
            pasted_image_item = self.canvas.create_image(x1, y1, anchor=tk.NW, image=pasted_image)

            self.pasted_items.append((pasted_image_item, pasted_image))

            self.canvas.unbind("<B1-Motion>")
            self.canvas.unbind("<ButtonRelease-1>")
            self.canvas.tag_bind(pasted_image_item, "<ButtonPress-1>", lambda event, item=pasted_image_item: self.start_move(event, item))
            self.canvas.tag_bind(pasted_image_item, "<B1-Motion>", lambda event, item=pasted_image_item: self.move_image(event, pasted_image_item))
            self.active_select = False

    def start_move_mode(self):
        self.move_mode = True
        self.canvas.bind("<ButtonPress-1>", self.start_move)
        self.canvas.bind("<B1-Motion>", self.move_image)

    def end_move_mode(self):
        self.move_mode = False
        if self.blue_border:
            self.canvas.delete(self.blue_border)
        self.canvas.bind("<ButtonPress-1>", self.start_selection)
        self.canvas.bind("<B1-Motion>", self.update_selection)

    def start_move(self, event, item):
        self.start_x, self.start_y = event.x, event.y
        self.moving_item = item

    def move_image(self, event, item):
        if item and self.move_mode:
            dx, dy = event.x - self.start_x, event.y - self.start_y

            self.canvas.move(item, dx, dy)

            self.start_x, self.start_y = event.x, event.y
if __name__ == "__main__":
    root = tk.Tk()
    app = ResizableCanvasApp(root)
    root.mainloop() 