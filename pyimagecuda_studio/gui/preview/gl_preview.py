from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtCore import Qt

from OpenGL.GL import *
import ctypes
import struct

from pyimagecuda import ImageU8, GLResource


class GLPreviewWidget(QOpenGLWidget):

    INITIAL_ALLOCATION_SIZE = 2048
    
    def __init__(self) -> None:
        fmt = QSurfaceFormat()
        fmt.setVersion(3, 3)
        fmt.setProfile(QSurfaceFormat.CoreProfile)
        fmt.setAlphaBufferSize(8)
        QSurfaceFormat.setDefaultFormat(fmt)
        
        super().__init__()

        self.setAttribute(Qt.WA_AlwaysStackOnTop, False)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        
        self._texture_id = None
        self._pbo_id = None
        self._gl_resource = None
        self._allocated_width = 0
        self._allocated_height = 0
        self._shader_program = None
        self._vao = None

        self._current_image_width = 0
        self._current_image_height = 0

        self._viewport_x = 0
        self._viewport_y = 0
        self._viewport_w = 0
        self._viewport_h = 0
        
        self._resources_created = False
        
        self._bg_color = [0.2, 0.2, 0.2]
        self._update_background_color()
    
    def _update_background_color(self):
        bg_color = self.palette().color(self.backgroundRole())
        self._bg_color = [
            bg_color.redF(),
            bg_color.greenF(),
            bg_color.blueF()
        ]
    
    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == event.Type.PaletteChange:
            self._update_background_color()
            self.update()
    
    def initializeGL(self):
        bg = self._bg_color
        glClearColor(bg[0], bg[1], bg[2], 1.0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        vertex_shader = """
        #version 330 core
        layout (location = 0) in vec2 aPos;
        layout (location = 1) in vec2 aTexCoord;
        out vec2 TexCoord;
        void main() {
            gl_Position = vec4(aPos, 0.0, 1.0);
            TexCoord = aTexCoord;
        }
        """
        
        fragment_shader = """
        #version 330 core
        in vec2 TexCoord;
        out vec4 FragColor;
        uniform sampler2D texture1;
        uniform vec2 texScale;
        uniform vec2 imageSize;
        void main() {
            vec2 scaledCoord = TexCoord * texScale;
            vec4 texColor = texture(texture1, scaledCoord);
            
            vec2 pixelCoord = TexCoord * imageSize;
            float checkerSize = 16.0;
            float checker = mod(floor(pixelCoord.x / checkerSize) + floor(pixelCoord.y / checkerSize), 2.0);
            vec3 bgColor = mix(vec3(0.15), vec3(0.25), checker);
            
            FragColor = vec4(mix(bgColor, texColor.rgb, texColor.a), 1.0);
        }
        """
        
        vs = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vs, vertex_shader)
        glCompileShader(vs)
        
        fs = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fs, fragment_shader)
        glCompileShader(fs)
        
        self._shader_program = glCreateProgram()
        glAttachShader(self._shader_program, vs)
        glAttachShader(self._shader_program, fs)
        glLinkProgram(self._shader_program)
        
        glDeleteShader(vs)
        glDeleteShader(fs)

        vertices = [
            -1.0, -1.0,  0.0, 1.0,
             1.0, -1.0,  1.0, 1.0,
             1.0,  1.0,  1.0, 0.0,
            -1.0,  1.0,  0.0, 0.0,
        ]
        
        indices = [0, 1, 2, 2, 3, 0]

        vertices_data = struct.pack(f'{len(vertices)}f', *vertices)
        indices_data = struct.pack(f'{len(indices)}I', *indices)
        
        self._vao = glGenVertexArrays(1)
        vbo = glGenBuffers(1)
        ebo = glGenBuffers(1)
        
        glBindVertexArray(self._vao)
        
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, len(vertices_data), vertices_data, GL_STATIC_DRAW)
        
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(indices_data), indices_data, GL_STATIC_DRAW)
        
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 16, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 16, ctypes.c_void_p(8))
        glEnableVertexAttribArray(1)
        
        glBindVertexArray(0)

        self._allocate_resources(self.INITIAL_ALLOCATION_SIZE, self.INITIAL_ALLOCATION_SIZE)
        
        print("[GUI-GL] OpenGL initialized successfully (pre-allocated 2K)")
    
    def _needs_reallocation(self, width: int, height: int) -> bool:
        if not self._resources_created:
            return True
        
        if width > self._allocated_width or height > self._allocated_height:
            return True
        
        return False
    
    def _allocate_resources(self, width: int, height: int) -> None:
        self._free_resources()

        self._allocated_width = width
        self._allocated_height = height
        
        print(f"[GUI-GL] Allocating GL resources: {width}x{height}")

        self._texture_id = glGenTextures(1)
        if isinstance(self._texture_id, (list, tuple)):
            self._texture_id = int(self._texture_id[0])
        else:
            self._texture_id = int(self._texture_id)
        
        glBindTexture(GL_TEXTURE_2D, self._texture_id)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, 
                     self._allocated_width, self._allocated_height, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glBindTexture(GL_TEXTURE_2D, 0)
        
        print(f"[GUI-GL] Texture created: {self._texture_id}")

        pbo_result = glGenBuffers(1)
        if isinstance(pbo_result, (list, tuple)):
            self._pbo_id = int(pbo_result[0])
        else:
            self._pbo_id = int(pbo_result)
        
        glBindBuffer(GL_PIXEL_UNPACK_BUFFER, self._pbo_id)
        glBufferData(GL_PIXEL_UNPACK_BUFFER, 
                     self._allocated_width * self._allocated_height * 4, 
                     None, GL_STREAM_DRAW)
        glBindBuffer(GL_PIXEL_UNPACK_BUFFER, 0)
        
        print(f"[GUI-GL] PBO created: {self._pbo_id}")

        self._gl_resource = GLResource(self._pbo_id)
        print(f"[GUI-GL] GLResource created (CUDA registered)")

        glBindBuffer(GL_PIXEL_UNPACK_BUFFER, self._pbo_id)
        glBindTexture(GL_TEXTURE_2D, self._texture_id)
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, 1, 1,
                       GL_RGBA, GL_UNSIGNED_BYTE, None)
        glBindTexture(GL_TEXTURE_2D, 0)
        glBindBuffer(GL_PIXEL_UNPACK_BUFFER, 0)
        glFinish()
        
        self._resources_created = True
        print(f"[GUI-GL] Resources allocated and warmed up")
    
    def _free_resources(self):
        if not self._resources_created:
            return
        
        print(f"[GUI-GL] Freeing GL resources ({self._allocated_width}x{self._allocated_height})")
        
        if self._gl_resource:
            try:
                self._gl_resource.free()
            except Exception as e:
                print(f"[GUI-GL] Error freeing GLResource: {e}")
            self._gl_resource = None
        
        if self._texture_id:
            glDeleteTextures([self._texture_id])
            self._texture_id = None
        
        if self._pbo_id:
            glDeleteBuffers(1, [self._pbo_id])
            self._pbo_id = None
        
        self._allocated_width = 0
        self._allocated_height = 0
        self._resources_created = False
    
    def _calculate_viewport(self, widget_w: int, widget_h: int) -> None:
        if self._current_image_width == 0 or self._current_image_height == 0:
            self._viewport_x = 0
            self._viewport_y = 0
            self._viewport_w = widget_w
            self._viewport_h = widget_h
            return

        image_aspect = self._current_image_width / self._current_image_height
        widget_aspect = widget_w / widget_h
        
        if widget_aspect > image_aspect:
            self._viewport_h = widget_h
            self._viewport_w = int(widget_h * image_aspect)
            self._viewport_x = (widget_w - self._viewport_w) // 2
            self._viewport_y = 0
            return
        
        self._viewport_w = widget_w
        self._viewport_h = int(widget_w / image_aspect)
        self._viewport_x = 0
        self._viewport_y = (widget_h - self._viewport_h) // 2
    
    def paintGL(self):
        bg = self._bg_color
        glClearColor(bg[0], bg[1], bg[2], 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        
        if self._texture_id is None or self._current_image_width == 0:
            return

        glViewport(self._viewport_x, self._viewport_y, 
                   self._viewport_w, self._viewport_h)
        
        glUseProgram(self._shader_program)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self._texture_id)
        glUniform1i(glGetUniformLocation(self._shader_program, "texture1"), 0)

        tex_scale_x = self._current_image_width / self._allocated_width
        tex_scale_y = self._current_image_height / self._allocated_height
        glUniform2f(glGetUniformLocation(self._shader_program, "texScale"), 
                    tex_scale_x, tex_scale_y)

        glUniform2f(glGetUniformLocation(self._shader_program, "imageSize"),
                    float(self._current_image_width), float(self._current_image_height))
        
        glBindVertexArray(self._vao)
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
    
    def display(self, image: ImageU8) -> None:
        self.makeCurrent()

        if self._needs_reallocation(image.width, image.height):
            print(f"[GUI-GL] Reallocating for new size: {image.width}x{image.height}")
            self._allocate_resources(image.width, image.height)

        size_changed = (self._current_image_width != image.width or 
                       self._current_image_height != image.height)
        
        self._current_image_width = image.width
        self._current_image_height = image.height

        if size_changed:
            self._calculate_viewport(self.width(), self.height())

        self._gl_resource.copy_from(image)

        glBindTexture(GL_TEXTURE_2D, self._texture_id)
        glBindBuffer(GL_PIXEL_UNPACK_BUFFER, self._pbo_id)
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, 
                       image.width, image.height,
                       GL_RGBA, GL_UNSIGNED_BYTE, None)
        glBindBuffer(GL_PIXEL_UNPACK_BUFFER, 0)
        glBindTexture(GL_TEXTURE_2D, 0)
        
        self.doneCurrent()
        self.update()

    def resizeGL(self, w, h):
        self._calculate_viewport(w, h)

    def clear(self):
        self._current_image_width = 0
        self._current_image_height = 0
        self.update()
    
    def cleanup(self):
        if not self._resources_created:
            return
        
        self.makeCurrent()
        self._free_resources()
        self.doneCurrent()
        print("[GUI-GL] All resources cleaned up")