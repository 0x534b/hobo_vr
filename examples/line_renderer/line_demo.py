import moderngl_window as mglw


class BasicWindow(mglw.WindowConfig):
    gl_version = (3, 3)
    title = "Basic Window"
    window_size = (1280, 720)
    aspect_ratio = 16 / 9
    resizable = True
    samples = 4

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def run(cls):
        mglw.run_window_config(cls)

class LineDemo(BasicWindow):
    title = "Line Demo"