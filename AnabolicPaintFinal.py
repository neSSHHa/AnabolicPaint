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
        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack(side=tk.TOP)
        self.canvas_frame = tk.Frame(root)
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="white", width=self.screen_width-120, height=self.screen_height-200, cursor="sizing", highlightthickness=2,highlightbackground="blue", relief='ridge')
        self.active_drawing = False
        self.canvas.pack(anchor="nw")
        self.pasted_items = [] 
        
        self.dots = []
        self.pasted_images = [] 
        self.rectangle = None
        self.MouseInfo1 = (0, 0)
        self.MouseInfo2 = (0, 0)
        self.moving_item = None
        self.label1 = tk.Label(self.button_frame, text="Mouse starting point: " + self.convertTuple(self.MouseInfo1))
        self.label2 = tk.Label(self.button_frame, text="Mouse ending point: " + self.convertTuple(self.MouseInfo2))
        
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

        
        
        self.original_items = {}  

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

        self.drawn_objects = []

    def setup_toolbar(self):
        self.toolbar = tk.Frame(self.root)
        self.toolbar.pack(fill="x")
        
        self.active_select = False
        self.create_styled_button(self.button_frame, "Pencil", self.use_pencil_tool)
        self.create_styled_button(self.button_frame, "Resize Canvas", self.resize_canvas)
        self.create_styled_button(self.button_frame, "Eraser", self.use_eraser_tool)
        self.create_styled_button(self.button_frame, "Color Panel", self.open_color_panel)
        self.create_styled_button(self.button_frame, "Line Thickness", self.open_thickness_dialog)
        self.create_styled_button(self.button_frame, "Straight Line", self.draw_straight_line)
        self.create_styled_button(self.button_frame, "Brush", self.use_spray_paint_brush)
        self.create_styled_button(self.button_frame, "Triangle", self.draw_triangle)
        self.create_styled_button(self.button_frame, "Rectangle", self.draw_rectangle)
        self.create_styled_button(self.button_frame, "Square", self.draw_square)
        self.create_styled_button(self.button_frame, "Circle", self.draw_circle)
        self.create_styled_button(self.button_frame, "Copy", self.copy_selection)
        self.create_styled_button(self.button_frame, "Paste", self.paste_selection)
        self.create_styled_button(self.button_frame, "Cut", self.cut_selected)
        self.create_styled_button(self.button_frame, "Move", self.start_move_mode)
        self.create_styled_button(self.button_frame, "Apply", self.end_move_mode)
        self.create_styled_button(self.button_frame, "Select", self.select_mode)
        self.create_styled_button(self.button_frame, "Clear", self.clear_canvas)

        
        self.canvas.bind("<Button-1>", self.update_last_click_point)
        self.canvas.bind("<B1-Motion>", self.draw_temp_shape)
        self.canvas.bind("<ButtonRelease-1>", self.end_draw_shape)
        

    def create_tool_button(self, parent, text, command):
        button = tk.Button(parent, text=text, command=command)
        button.pack(side=tk.LEFT)
    def create_styled_button(self,parent, text, command):
            button = ttk.Button(parent, text=text, command=command, style="TButton")
            button.pack(side=tk.LEFT, padx=4, pady=4)
            return button
    def clear_canvas(self):
        self.canvas.delete("all")

    def resize_canvas(self):
        self.canvas.bind("<ButtonPress-1>", self.start_resizing_action)
        self.canvas.bind("<B1-Motion>", self.handle_resizing_action)
        self.canvas.bind("<ButtonRelease-1>", self.stop_resizing_action)
        

    def unbind_current_tool(self):
        if self.current_brush == "Eraser":
            self.canvas.unbind("<Button-1>")
            self.canvas.unbind("<B1-Motion>")
        if self.current_brush == "Pencil":
            self.canvas.unbind("<Button-1>")
            self.canvas.unbind("<B1-Motion>")
        if self.current_brush == "Brush":
            self.canvas.unbind("<Button-1>")
            self.canvas.unbind("<B1-Motion>")

    def use_eraser_tool(self):
        self.unbind_current_tool()
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
        self.unbind_current_tool()
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

            self.drawn_objects.append(("Pencil", x, y, color, brush_size))

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

        self.drawn_objects.append(("Straight Line", self.line_start_x, self.line_start_y, self.current_color, self.current_thickness))

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
        self.unbind_current_tool()
        self.current_brush = "Brush"
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

            self.canvas.create_polygon(rotated_x1, rotated_y1, rotated_x2, rotated_y2, rotated_x3, rotated_y3, fill=self.current_color, outline="", width=0)
            
            self.drawn_triangles.append((rotated_x1, rotated_y1, rotated_x2, rotated_y2, rotated_x3, rotated_y3, self.current_color))

        elif shape_type == "rectangle":
            self.canvas.create_rectangle(
                self.shape_start_x, self.shape_start_y,
                x, y, fill=self.current_color, outline="", width=0
            )
            self.drawn_objects.append((shape_type, self.shape_start_x, self.shape_start_y, x, y, self.current_color))

        elif shape_type == "square":
            size = max(abs(x - self.shape_start_x), abs(y - self.shape_start_y))
            if x < self.shape_start_x:
                x = self.shape_start_x - size
            else:
                x = self.shape_start_x + size
            if y < self.shape_start_y:
                y = self.shape_start_y - size
            else:
                y = self.shape_start_y + size

            self.canvas.create_rectangle(
                self.shape_start_x, self.shape_start_y,
                x, y, fill=self.current_color, outline="", width=0
            )
            self.drawn_objects.append((shape_type, self.shape_start_x, self.shape_start_y, x, y, self.current_color))

        elif shape_type == "circle":
            radius = math.sqrt((x - self.shape_start_x)**2 + (y - self.shape_start_y)**2)
            self.canvas.create_oval(
                self.shape_start_x - radius, self.shape_start_y - radius,
                self.shape_start_x + radius, self.shape_start_y + radius,
                fill=self.current_color, outline="", width=0
            )
            self.drawn_objects.append((shape_type, self.shape_start_x, self.shape_start_y, radius, self.current_color))

        self.is_drawing_triangle = False
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")

    def draw_temp_shape(self, event):
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

            self.canvas.create_polygon(rotated_x1, rotated_y1, rotated_x2, rotated_y2, rotated_x3, rotated_y3, fill=self.current_color, outline="", width=0, tags="temp_shape")

        elif shape_type == "rectangle":
            self.canvas.create_rectangle(
                self.shape_start_x, self.shape_start_y,
                x, y, fill=self.current_color, outline="", width=0, tags="temp_shape"
            )

        elif shape_type == "square":
            size = max(abs(x - self.shape_start_x), abs(y - self.shape_start_y))
            if x < self.shape_start_x:
                x = self.shape_start_x - size
            else:
                x = self.shape_start_x + size
            if y < self.shape_start_y:
                y = self.shape_start_y - size
            else:
                y = self.shape_start_y + size

            self.canvas.create_rectangle(
                self.shape_start_x, self.shape_start_y,
                x, y, fill=self.current_color, outline="", width=0, tags="temp_shape"
            )

        elif shape_type == "circle":
            radius = math.sqrt((x - self.shape_start_x)**2 + (y - self.shape_start_y)**2)
            self.canvas.create_oval(
                self.shape_start_x - radius, self.shape_start_y - radius,
                self.shape_start_x + radius, self.shape_start_y + radius,
                fill=self.current_color, outline="", width=0, tags="temp_shape"
            )

    def update_last_click_point(self, event):
        self.last_click_point = (event.x, event.y)

    def copy_selection(self):
        if not self.move_mode:
            self.serialized_selection = self.serialize_selection()
            self.clear_selection()

    def serialize_selection(self):
        if self.move_mode:
            return None

        selection_bbox = self.get_selection_bbox()
        if selection_bbox:
            x1, y1, x2, y2 = selection_bbox
            serialized_selection = {
                "type": "image",
                "data": self.copy_image_area(x1, y1, x2, y2),
                "position": (x1, y1),
                "size": (x2 - x1, y2 - y1),
            }
            return serialized_selection
        else:
            return None

    def get_selection_bbox(self):
        if self.border:
            x1, y1, x2, y2 = self.canvas.coords(self.border)
            return x1, y1, x2, y2
        else:
            return None

    def copy_image_area(self, x1, y1, x2, y2):
        if x2 > x1 and y2 > y1:
            return self.draw.crop((x1, y1, x2, y2))
        else:
            return None

    def clear_selection(self):
        self.canvas.delete("selection")
        self.canvas.delete("border")
        self.serialized_selection = None
        self.border = None

    def paste_selection(self):
        if self.serialized_selection:
            data = self.serialized_selection["data"]
            position = self.serialized_selection["position"]
            size = self.serialized_selection["size"]

            self.pasted_items.append((data, position))
            image = ImageTk.PhotoImage(data)

            image_item = self.canvas.create_image(
                position[0] + size[0] / 2, position[1] + size[1] / 2,
                image=image, anchor=tk.CENTER, tags=("image", "pasted")
            )
            self.canvas.lower(image_item)
            self.canvas.update_idletasks()
            self.canvas.tag_bind(image_item, "<Button-1>", lambda e, item=image_item: self.select_pasted_item(item))
            self.pasted_image_item = image_item

    def cut_selected(self):
        if not self.move_mode:
            self.serialized_selection = self.serialize_selection()
            self.delete_selection()

    def delete_selection(self):
        if self.border:
            self.canvas.delete("selection")
            self.canvas.delete("border")
            self.serialized_selection = None
            self.border = None

    def start_move_mode(self):
        self.move_mode = True
        self.canvas.config(cursor="fleur")
        self.canvas.tag_bind("pasted", "<Button-1>", self.select_pasted_item)
        self.canvas.bind("<Button-1>", self.move_pasted_item)
        self.canvas.bind("<B1-Motion>", self.move_pasted_item)

    def end_move_mode(self):
        self.move_mode = False
        self.canvas.config(cursor="sizing")
        self.canvas.tag_unbind("pasted", "<Button-1>")
        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<B1-Motion>")
        self.pasted_image_item = None
        self.blue_border = None
        self.move_mode = False

    def select_pasted_item(self, item):
        if not self.move_mode:
            return

        if self.blue_border:
            self.canvas.delete(self.blue_border)

        self.pasted_image_item = item
        bbox = self.canvas.bbox(item)
        x1, y1, x2, y2 = bbox
        self.blue_border = self.canvas.create_rectangle(x1 - 5, y1 - 5, x2 + 5, y2 + 5, outline="blue", width=2, tags="border")

    def move_pasted_item(self, event):
        if not self.move_mode or not self.pasted_image_item:
            return

        x, y = event.x, event.y
        if self.last_x is not None and self.last_y is not None:
            dx, dy = x - self.last_x, y - self.last_y
            self.canvas.move(self.pasted_image_item, dx, dy)
            self.canvas.move(self.blue_border, dx, dy)
        self.last_x, self.last_y = x, y

    def select_mode(self):
        self.move_mode = False
        self.canvas.config(cursor="sizing")
        self.canvas.tag_unbind("pasted", "<Button-1>")
        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<B1-Motion>")
        self.pasted_image_item = None
        self.blue_border = None

    def zoom(self, event):
        central_point = (event.x, event.y)
        zoom_factor = 1.1 if event.delta > 0 else 1 / 1.1  
        self.zoom_canvas(central_point, zoom_factor)


    def zoom_canvas(self, central_point, zoom_factor):
       canvas_width = int(self.canvas_width * zoom_factor)
       canvas_height = int(self.canvas_height * zoom_factor)

       dx = central_point[0] - self.canvas.winfo_width() / 2
       dy = central_point[1] - self.canvas.winfo_height() / 2

       canvas_x = self.canvas.canvasx(central_point[0]) - dx * zoom_factor
       canvas_y = self.canvas.canvasy(central_point[1]) - dy * zoom_factor

       self.canvas.scale("all", central_point[0], central_point[1], zoom_factor, zoom_factor)
       self.zoom_factor *= zoom_factor

       self.canvas.xview_moveto(canvas_x / canvas_width)
       self.canvas.yview_moveto(canvas_y / canvas_height)
       self.canvas.update()

       for item, (x, y) in self.original_items.items():
           new_x = x * self.zoom_factor
           new_y = y * self.zoom_factor
           self.canvas.coords(item, new_x, new_y)
    def save_image(self):
        filename = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
        if filename:
            self.draw.save(filename)

    def open_image(self):
        filename = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")])
        if filename:
            self.draw = Image.open(filename)
            self.image_draw = ImageDraw.Draw(self.draw)
            self.update_canvas()

    def update_canvas(self):
        self.canvas.delete("all")
        image = ImageTk.PhotoImage(self.draw)
        self.canvas.create_image(0, 0, image=image, anchor="nw")  
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        self.canvas.image = image

    def convertTuple(self, tup):
        str_ = ''.join(tup)
        return str_

    def resizeCanvas(self, w, h):
        self.canvas.config(width=w, height=h)

    def start_resizing_action(self, event):
        x, y = event.x, event.y
        if self.border:
            self.resizing = True
            self.active_select = False
            self.clear_selection()
            self.last_x = x
            self.last_y = y

    def handle_resizing_action(self, event):
        if self.resizing:
            x, y = event.x, event.y
            bbox = self.canvas.coords(self.border)
            dx, dy = x - self.last_x, y - self.last_y
            if dx > 0 and bbox[2] + dx > self.canvas_width:
                dx = self.canvas_width - bbox[2]
            if dx < 0 and bbox[0] + dx < 0:
                dx = -bbox[0]
            if dy > 0 and bbox[3] + dy > self.canvas_height:
                dy = self.canvas_height - bbox[3]
            if dy < 0 and bbox[1] + dy < 0:
                dy = -bbox[1]
            self.canvas.move(self.border, dx, dy)
            self.last_x = x
            self.last_y = y
            self.update_selection()

    def stop_resizing_action(self, event):
        self.resizing = False

    def update_selection(self):
        if self.border:
            x1, y1, x2, y2 = self.canvas.coords(self.border)
            self.canvas.coords("selection", x1 + self.border_width, y1 + self.border_width, x2 - self.border_width, y2 - self.border_width)

    def create_rectangle(self, x1, y1, x2, y2):
        x1, y1, x2, y2 = self.correct_coords(x1, y1, x2, y2)
        self.border = self.canvas.create_rectangle(x1, y1, x2, y2, outline="blue", width=self.border_width, tags="selection")

    def correct_coords(self, x1, y1, x2, y2):
        if x1 < 0:
            x1 = 0
        if y1 < 0:
            y1 = 0
        if x2 > self.canvas_width:
            x2 = self.canvas_width
        if y2 > self.canvas_height:
            y2 = self.canvas_height
        return x1, y1, x2, y2

    def save_image(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if file_path:
            x = self.canvas_frame.winfo_rootx() + self.canvas.winfo_x()
            y = self.canvas_frame.winfo_rooty() + self.canvas.winfo_y()
            x1 = x + self.canvas.winfo_width()
            y1 = y + self.canvas.winfo_height()
            original_highlightthickness = self.canvas.cget("highlightthickness")
            original_borderwidth = self.canvas.cget("borderwidth")
            self.canvas.config(highlightthickness=0, borderwidth=0)
            self.canvas.update_idletasks()  
            ImageGrab.grab(bbox=(x, y, x1, y1)).save(file_path)
            self.canvas.config(highlightthickness=original_highlightthickness, borderwidth=original_borderwidth)
            self.canvas.update_idletasks()  

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

        canvas_width = self.canvas.winfo_width()  
        canvas_height = self.canvas.winfo_height() 
        
        dot_coords = [
            (0 - dot_size, 0 - dot_size),                  
            (0 - dot_size, canvas_height + dot_size),     
            (canvas_width + dot_size, canvas_height + dot_size),  
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

            self.canvas.create_rectangle(x1, y1, x2, y2, fill="white", outline="")

    def paste_selection(self):
        if self.serialized_selection:
            image = Image.open(self.serialized_selection)
            pasted_image = ImageTk.PhotoImage(image)

            canvas_x, canvas_y = self.canvas.winfo_rootx(), self.canvas.winfo_rooty()

            x1, y1, x2, y2 = map(int, self.canvas.coords(self.rectangle))
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
        self.canvas.bind("<ButtonPress-1>", lambda event: self.start_move(event, self.moving_item))
        self.canvas.bind("<B1-Motion>", lambda event: self.move_image(event, self.moving_item))


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