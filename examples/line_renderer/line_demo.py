from pathlib import Path

import moderngl
import moderngl_window as mglw
import numpy as np
from pyrr import Matrix44
from squaternion import Quaternion


class BasicWindow(mglw.WindowConfig):
    gl_version = (3, 3)
    title = "Basic Window"
    window_size = (1280, 720)
    aspect_ratio = 16 / 9
    resizable = True
    samples = 4

    def __init__(self, **kwargs):
        pass

    def __call__(self, ctx=None, wnd=None, timer=None, **kwargs):
        # overriding init calling stuff in run_window_config so I can actually init the class and have class variables
        super().__init__(ctx, wnd, timer)
        return self

    def run(self):
        mglw.run_window_config(self)


def bake_line(line, closed=False):
    line = line.astype(np.float32)
    epsilon = 1e-10
    n = len(line)
    if closed and ((line[0] - line[-1]) ** 2).sum() > epsilon:
        line = np.append(line, line[0])
        line = line.reshape(n + 1, 3)
        n = n + 1
    v = np.zeros(((1 + n + 1), 2, 3), dtype=np.float32)
    uv = np.zeros((n, 2, 2), dtype=np.float32)
    v_prev, v_curr, v_next = v[:-2], v[1:-1], v[2:]
    v_curr[..., 0] = line[:, np.newaxis, 0]
    v_curr[..., 1] = line[:, np.newaxis, 1]
    v_curr[..., 2] = line[:, np.newaxis, 2]
    length = np.cumsum(np.sqrt(((line[1:] - line[:-1]) ** 2).sum(axis=-1))).reshape(n - 1, 1)
    uv[1:, :, 0] = length
    uv[..., 1] = 1, -1
    if closed:
        v[0], v[-1] = v[-3], v[2]
    else:
        v[0], v[-1] = v[1], v[-2]
    return v_prev, v_curr, v_next, uv, length[-1]


def bake_lines(lines):
    v_prev, v_curr, v_next = (np.zeros((0, 2, 3)),) * 3
    uv = np.zeros((0, 2, 2))
    length = np.zeros((0,))
    for line in lines:
        v_prev_2, v_curr_2, v_next_2, uv_2, l_2 = bake_line(np.array(line))
        v_prev = np.concatenate((v_prev, v_prev_2))
        v_curr = np.concatenate((v_curr, v_curr_2))
        v_next = np.concatenate((v_next, v_next_2))
        uv = np.concatenate((uv, uv_2))
        length = np.concatenate((length, l_2))
    return v_prev, v_curr, v_next, uv, length


class LineCloud(BasicWindow):
    title = "Line Cloud"

    def __init__(self, lines):
        super().__init__()
        self.lines = lines
        self.quaternion = Quaternion(0, 1, 0, 0).normalize

    def __call__(self, ctx=None, wnd=None, timer=None, **kwargs):
        # overriding init calling stuff in run_window_config so I can actually init the class and have class variables
        super().__call__(ctx, wnd, timer, **kwargs)

        self.prog = self.ctx.program(
            geometry_shader=open(str(Path.joinpath(Path(__file__).parent, "line_shader.vert"))).read(),
            fragment_shader=open(str(Path.joinpath(Path(__file__).parent, "line_shader.frag"))).read(),
        )

        self.prog['model'].write(Matrix44.identity().astype('f4'))
        self.prog['view'].write(Matrix44.from_translation([0, 0, -5]).astype('f4'))
        self.prog['projection'].write(
            Matrix44.perspective_projection(45.0, self.aspect_ratio, 0.1, 1000.0).astype('f4'))
        #self.prog['viewport'] = self.window_size
        self.prog["thickness"] = 20.0
        self.prog["antialias"] = 1.5

        v_prev, v_curr, v_next, uv, lengths = bake_lines(self.lines)
        self.instances = len(v_curr)*2
        render_indices = np.arange(self.instances)
        self.index_buffer = self.ctx.buffer(render_indices.astype('i4').tobytes())
        self.prev_vertex_buffer = self.ctx.buffer(v_prev.astype('f4').tobytes())
        self.curr_vertex_buffer = self.ctx.buffer(v_curr.astype('f4').tobytes())
        self.next_vertex_buffer = self.ctx.buffer(v_next.astype('f4').tobytes())
        self.uv_vertex_buffer = self.ctx.buffer(v_next.astype('f4').tobytes())

        vao_content = [

            (self.prev_vertex_buffer, '3f', 'prev'),
            (self.curr_vertex_buffer, '3f', 'curr'),
            (self.next_vertex_buffer, '3f', 'next'),

            (self.uv_vertex_buffer, '2f', 'uv'),
        ]

        self.vao = self.ctx.vertex_array(self.prog, vao_content, self.index_buffer)

        self.ctx.enable(moderngl.DEPTH_TEST)
        return self

    def resize(self, width: int, height: int):
        self.ctx.clear(1,1,1)
        self.prog['projection'].write(
            Matrix44.perspective_projection(30.0, self.aspect_ratio, 0.1, 1000.0).astype('f4'))
        #self.prog['viewport'] = (width, height)
        self.vao.render(moderngl.LINES, instances=self.instances)


    def render(self, time: float, frametime: float):
        self.ctx.clear(1,1,1)
        self.ctx.wireframe = True
        self.vao.render(moderngl.LINES, instances=self.instances)
        r = Quaternion.from_euler(.001, .002, .003)
        self.quaternion = r * self.quaternion * r.conjugate
        model = Matrix44.from_quaternion(self.quaternion)
        self.prog['model'].write(model.astype('f4').tobytes())


if __name__ == "__main__":
    lines = [
        [
            [0, 0, 0],
            [.1, .1, .1],
        ],
        [
            [.2, .2, .2],
            [.3, .3, .3],
            [.4, .5, .6],
            [.7, .8, .9],

        ]
    ]
    n = 2048
    T = np.linspace(0, 20 * 2 * np.pi, n, dtype=np.float32)
    R = np.linspace(.1, np.pi - .1, n, dtype=np.float32)
    X = np.cos(T) * np.sin(R)
    Y = np.sin(T) * np.sin(R)
    Z = np.cos(R)
    P = np.dstack((X, Y, Z)).squeeze()

    LineCloud([P]).run()
