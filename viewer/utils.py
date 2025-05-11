def center_window(master, width, height):
    screen_width = master.winfo_screenwidth()
    screen_height = master.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    master.geometry(f"{width}x{height}+{x}+{y}")