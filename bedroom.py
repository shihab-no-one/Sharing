import glfw
from OpenGL.GL import *
import glm
import numpy as np
import ctypes
import sys


# ============================================================
# SHADERS
# ============================================================

VERTEX_SHADER = """
#version 330 core

layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aNormal;

out vec3 FragPos;
out vec3 Normal;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

void main()
{
    FragPos = vec3(model * vec4(aPos, 1.0));

    Normal = mat3(transpose(inverse(model))) * aNormal;

    gl_Position = projection * view * vec4(FragPos, 1.0);
}
"""


FRAGMENT_SHADER = """
#version 330 core

out vec4 FragColor;

in vec3 FragPos;
in vec3 Normal;

uniform vec3 viewPos;
uniform vec3 objectColor;


/* ==============================
   Directional Light
   ============================== */

uniform vec3 dirLightDirection;
uniform vec3 dirLightColor;
uniform bool dirLightEnabled;


/* ==============================
   Point Light
   ============================== */

uniform vec3 pointLightPosition;
uniform vec3 pointLightColor;
uniform bool pointLightEnabled;


/* ==============================
   Spot Light
   ============================== */

uniform vec3 spotLightPosition;
uniform vec3 spotLightDirection;
uniform vec3 spotLightColor;

uniform float spotCutOff;
uniform float spotOuterCutOff;

uniform bool spotLightEnabled;


void main()
{
    vec3 N = normalize(Normal);

    vec3 result = vec3(0.0);


    // ========================================================
    // AMBIENT LIGHT
    // ========================================================

    vec3 ambient = 0.12 * vec3(1.0);
    result += ambient;


    // ========================================================
    // DIRECTIONAL LIGHT
    // ========================================================

    if (dirLightEnabled)
    {
        vec3 L = normalize(-dirLightDirection);

        float diff = max(dot(N, L), 0.0);

        vec3 diffuse = diff * dirLightColor;

        vec3 V = normalize(viewPos - FragPos);
        vec3 R = reflect(-L, N);

        float spec = pow(max(dot(V, R), 0.0), 32.0);

        vec3 specular = 0.35 * spec * dirLightColor;

        result += diffuse + specular;
    }


    // ========================================================
    // POINT LIGHT
    // ========================================================

    if (pointLightEnabled)
    {
        vec3 L = normalize(pointLightPosition - FragPos);

        float diff = max(dot(N, L), 0.0);

        vec3 diffuse = diff * pointLightColor;

        vec3 V = normalize(viewPos - FragPos);
        vec3 R = reflect(-L, N);

        float spec = pow(max(dot(V, R), 0.0), 32.0);

        vec3 specular = 0.45 * spec * pointLightColor;


        // Distance attenuation

        float distance = length(pointLightPosition - FragPos);

        float constant = 1.0;
        float linear = 0.09;
        float quadratic = 0.032;

        float attenuation =
            1.0 /
            (constant +
             linear * distance +
             quadratic * distance * distance);

        result += (diffuse + specular) * attenuation;
    }


    // ========================================================
    // SPOT LIGHT
    // ========================================================

    if (spotLightEnabled)
    {
        vec3 L = normalize(spotLightPosition - FragPos);

        float diff = max(dot(N, L), 0.0);

        vec3 diffuse = diff * spotLightColor;

        vec3 V = normalize(viewPos - FragPos);
        vec3 R = reflect(-L, N);

        float spec = pow(max(dot(V, R), 0.0), 32.0);

        vec3 specular = 0.5 * spec * spotLightColor;


        // Distance attenuation

        float distance = length(spotLightPosition - FragPos);

        float constant = 1.0;
        float linear = 0.09;
        float quadratic = 0.032;

        float attenuation =
            1.0 /
            (constant +
             linear * distance +
             quadratic * distance * distance);


        // Spotlight cone

        float theta =
            dot(L, normalize(-spotLightDirection));

        float epsilon =
            spotCutOff - spotOuterCutOff;

        float intensity =
            clamp(
                (theta - spotOuterCutOff) / epsilon,
                0.0,
                1.0
            );


        result +=
            (diffuse + specular)
            * attenuation
            * intensity;
    }


    // ========================================================
    // FINAL COLOR
    // ========================================================

    vec3 finalColor = result * objectColor;

    FragColor = vec4(finalColor, 1.0);
}
"""


# ============================================================
# CUBE VERTICES
# POSITION + NORMAL
# ============================================================

cube_vertices = np.array([

    # Front
    -0.5, -0.5,  0.5,   0.0,  0.0,  1.0,
     0.5, -0.5,  0.5,   0.0,  0.0,  1.0,
     0.5,  0.5,  0.5,   0.0,  0.0,  1.0,

     0.5,  0.5,  0.5,   0.0,  0.0,  1.0,
    -0.5,  0.5,  0.5,   0.0,  0.0,  1.0,
    -0.5, -0.5,  0.5,   0.0,  0.0,  1.0,


    # Back
    -0.5, -0.5, -0.5,   0.0,  0.0, -1.0,
    -0.5,  0.5, -0.5,   0.0,  0.0, -1.0,
     0.5,  0.5, -0.5,   0.0,  0.0, -1.0,

     0.5,  0.5, -0.5,   0.0,  0.0, -1.0,
     0.5, -0.5, -0.5,   0.0,  0.0, -1.0,
    -0.5, -0.5, -0.5,   0.0,  0.0, -1.0,


    # Left
    -0.5,  0.5, -0.5,  -1.0, 0.0, 0.0,
    -0.5,  0.5,  0.5,  -1.0, 0.0, 0.0,
    -0.5, -0.5,  0.5,  -1.0, 0.0, 0.0,

    -0.5, -0.5,  0.5,  -1.0, 0.0, 0.0,
    -0.5, -0.5, -0.5,  -1.0, 0.0, 0.0,
    -0.5,  0.5, -0.5,  -1.0, 0.0, 0.0,


    # Right
     0.5,  0.5,  0.5,   1.0, 0.0, 0.0,
     0.5,  0.5, -0.5,   1.0, 0.0, 0.0,
     0.5, -0.5, -0.5,   1.0, 0.0, 0.0,

     0.5, -0.5, -0.5,   1.0, 0.0, 0.0,
     0.5, -0.5,  0.5,   1.0, 0.0, 0.0,
     0.5,  0.5,  0.5,   1.0, 0.0, 0.0,


    # Bottom
    -0.5, -0.5, -0.5,   0.0, -1.0, 0.0,
     0.5, -0.5, -0.5,   0.0, -1.0, 0.0,
     0.5, -0.5,  0.5,   0.0, -1.0, 0.0,

     0.5, -0.5,  0.5,   0.0, -1.0, 0.0,
    -0.5, -0.5,  0.5,   0.0, -1.0, 0.0,
    -0.5, -0.5, -0.5,   0.0, -1.0, 0.0,


    # Top
    -0.5,  0.5, -0.5,   0.0, 1.0, 0.0,
    -0.5,  0.5,  0.5,   0.0, 1.0, 0.0,
     0.5,  0.5,  0.5,   0.0, 1.0, 0.0,

     0.5,  0.5,  0.5,   0.0, 1.0, 0.0,
     0.5,  0.5, -0.5,   0.0, 1.0, 0.0,
    -0.5,  0.5, -0.5,   0.0, 1.0, 0.0

], dtype=np.float32)


# ============================================================
# CAMERA
# ============================================================

camera_pos = glm.vec3(0.0, 2.0, 8.0)

camera_front = glm.vec3(
    0.0,
    0.0,
    -1.0
)

camera_up = glm.vec3(
    0.0,
    1.0,
    0.0
)

yaw = -90.0
pitch = 0.0

last_x = 400
last_y = 300

first_mouse = True

delta_time = 0.0
last_frame = 0.0


# ============================================================
# LIGHT SETTINGS
# ============================================================

directional_enabled = True
point_enabled = True
spot_enabled = True


# Directional light
directional_direction = glm.vec3(
    -0.3,
    -1.0,
    -0.3
)


# Point light
point_light_position = glm.vec3(
    0.0,
    3.5,
    0.0
)


# ============================================================
# SHADER FUNCTIONS
# ============================================================

def compile_shader(source, shader_type):

    shader = glCreateShader(shader_type)

    glShaderSource(shader, source)

    glCompileShader(shader)

    if not glGetShaderiv(shader, GL_COMPILE_STATUS):

        error = glGetShaderInfoLog(shader).decode()

        print("Shader compilation error:")
        print(error)

        raise RuntimeError(error)

    return shader


def create_shader_program():

    vertex_shader = compile_shader(
        VERTEX_SHADER,
        GL_VERTEX_SHADER
    )

    fragment_shader = compile_shader(
        FRAGMENT_SHADER,
        GL_FRAGMENT_SHADER
    )

    program = glCreateProgram()

    glAttachShader(program, vertex_shader)

    glAttachShader(program, fragment_shader)

    glLinkProgram(program)

    if not glGetProgramiv(program, GL_LINK_STATUS):

        error = glGetProgramInfoLog(program).decode()

        print("Shader linking error:")
        print(error)

        raise RuntimeError(error)

    glDeleteShader(vertex_shader)

    glDeleteShader(fragment_shader)

    return program


def set_mat4(program, name, matrix):

    location = glGetUniformLocation(
        program,
        name
    )

    glUniformMatrix4fv(
        location,
        1,
        GL_FALSE,
        glm.value_ptr(matrix)
    )


def set_vec3(program, name, value):

    location = glGetUniformLocation(
        program,
        name
    )

    glUniform3fv(
        location,
        1,
        glm.value_ptr(value)
    )


def set_bool(program, name, value):

    location = glGetUniformLocation(
        program,
        name
    )

    glUniform1i(
        location,
        int(value)
    )


def set_float(program, name, value):

    location = glGetUniformLocation(
        program,
        name
    )

    glUniform1f(
        location,
        value
    )


# ============================================================
# CAMERA MOUSE
# ============================================================

def mouse_callback(window, xpos, ypos):

    global yaw
    global pitch
    global last_x
    global last_y
    global first_mouse
    global camera_front

    if first_mouse:

        last_x = xpos
        last_y = ypos

        first_mouse = False

    sensitivity = 0.1

    x_offset = (xpos - last_x) * sensitivity

    y_offset = (last_y - ypos) * sensitivity

    last_x = xpos
    last_y = ypos

    yaw += x_offset
    pitch += y_offset

    pitch = max(-89.0, min(89.0, pitch))


    front = glm.vec3(

        glm.cos(glm.radians(yaw))
        * glm.cos(glm.radians(pitch)),

        glm.sin(glm.radians(pitch)),

        glm.sin(glm.radians(yaw))
        * glm.cos(glm.radians(pitch))

    )

    camera_front = glm.normalize(front)


# ============================================================
# KEY INPUT
# ============================================================

def key_callback(window, key, scancode, action, mods):

    global directional_enabled
    global point_enabled
    global spot_enabled

    if action == glfw.PRESS:

        # 1 = Directional light
        if key == glfw.KEY_1:

            directional_enabled = not directional_enabled

            print(
                "Directional Light:",
                directional_enabled
            )


        # 2 = Point light
        elif key == glfw.KEY_2:

            point_enabled = not point_enabled

            print(
                "Point Light:",
                point_enabled
            )


        # 3 = Spot light
        elif key == glfw.KEY_3:

            spot_enabled = not spot_enabled

            print(
                "Spot Light:",
                spot_enabled
            )


# ============================================================
# MOVEMENT
# ============================================================

def process_input(window):

    global camera_pos

    speed = 3.0 * delta_time

    # Forward
    if glfw.get_key(
        window,
        glfw.KEY_W
    ) == glfw.PRESS:

        camera_pos += camera_front * speed


    # Backward
    if glfw.get_key(
        window,
        glfw.KEY_S
    ) == glfw.PRESS:

        camera_pos -= camera_front * speed


    # Left
    if glfw.get_key(
        window,
        glfw.KEY_A
    ) == glfw.PRESS:

        right = glm.normalize(
            glm.cross(
                camera_front,
                camera_up
            )
        )

        camera_pos -= right * speed


    # Right
    if glfw.get_key(
        window,
        glfw.KEY_D
    ) == glfw.PRESS:

        right = glm.normalize(
            glm.cross(
                camera_front,
                camera_up
            )
        )

        camera_pos += right * speed


    # ESC
    if glfw.get_key(
        window,
        glfw.KEY_ESCAPE
    ) == glfw.PRESS:

        glfw.set_window_should_close(
            window,
            True
        )


# ============================================================
# DRAW CUBE
# ============================================================

def draw_cube(
    program,
    vao,
    position,
    scale,
    color
):

    model = glm.mat4(1.0)

    model = glm.translate(
        model,
        position
    )

    model = glm.scale(
        model,
        scale
    )

    set_mat4(
        program,
        "model",
        model
    )

    set_vec3(
        program,
        "objectColor",
        color
    )

    glBindVertexArray(vao)

    glDrawArrays(
        GL_TRIANGLES,
        0,
        36
    )


# ============================================================
# MAIN
# ============================================================

def main():

    global delta_time
    global last_frame


    # ========================================================
    # GLFW
    # ========================================================

    if not glfw.init():

        print("Failed to initialize GLFW")

        return


    glfw.window_hint(
        glfw.CONTEXT_VERSION_MAJOR,
        3
    )

    glfw.window_hint(
        glfw.CONTEXT_VERSION_MINOR,
        3
    )

    glfw.window_hint(
        glfw.OPENGL_PROFILE,
        glfw.OPENGL_CORE_PROFILE
    )


    window = glfw.create_window(
        1000,
        700,
        "Computer Graphics - 3D Bedroom",
        None,
        None
    )


    if not window:

        print("Failed to create window")

        glfw.terminate()

        return


    glfw.make_context_current(window)


    # ========================================================
    # INPUT
    # ========================================================

    glfw.set_cursor_pos_callback(
        window,
        mouse_callback
    )

    glfw.set_key_callback(
        window,
        key_callback
    )

    glfw.set_input_mode(
        window,
        glfw.CURSOR,
        glfw.CURSOR_DISABLED
    )


    # ========================================================
    # OPENGL
    # ========================================================

    glEnable(GL_DEPTH_TEST)

    glEnable(GL_CULL_FACE)

    glCullFace(GL_BACK)


    # ========================================================
    # SHADER
    # ========================================================

    program = create_shader_program()


    # ========================================================
    # VAO / VBO
    # ========================================================

    vao = glGenVertexArrays(1)

    vbo = glGenBuffers(1)


    glBindVertexArray(vao)

    glBindBuffer(
        GL_ARRAY_BUFFER,
        vbo
    )


    glBufferData(
        GL_ARRAY_BUFFER,
        cube_vertices.nbytes,
        cube_vertices,
        GL_STATIC_DRAW
    )


    stride = 6 * ctypes.sizeof(
        ctypes.c_float
    )


    # Position
    glVertexAttribPointer(
        0,
        3,
        GL_FLOAT,
        GL_FALSE,
        stride,
        ctypes.c_void_p(0)
    )

    glEnableVertexAttribArray(0)


    # Normal
    glVertexAttribPointer(
        1,
        3,
        GL_FLOAT,
        GL_FALSE,
        stride,
        ctypes.c_void_p(
            3 * ctypes.sizeof(
                ctypes.c_float
            )
        )
    )

    glEnableVertexAttribArray(1)


    glBindVertexArray(0)


    # ========================================================
    # PROJECTION
    # ========================================================

    projection = glm.perspective(
        glm.radians(45.0),
        1000 / 700,
        0.1,
        100.0
    )


    # ========================================================
    # LIGHT COLORS
    # ========================================================

    directional_color = glm.vec3(
        0.45,
        0.45,
        0.50
    )


    point_color = glm.vec3(
        1.0,
        0.75,
        0.35
    )


    spot_color = glm.vec3(
        1.0,
        1.0,
        1.0
    )


    # ========================================================
    # MAIN LOOP
    # ========================================================

    while not glfw.window_should_close(window):


        # ----------------------------------------------------
        # TIME
        # ----------------------------------------------------

        current_frame = glfw.get_time()

        delta_time = (
            current_frame
            - last_frame
        )

        last_frame = current_frame


        # ----------------------------------------------------
        # INPUT
        # ----------------------------------------------------

        glfw.poll_events()

        process_input(window)


        # ----------------------------------------------------
        # CLEAR SCREEN
        # ----------------------------------------------------

        glClearColor(
            0.05,
            0.05,
            0.08,
            1.0
        )

        glClear(
            GL_COLOR_BUFFER_BIT
            | GL_DEPTH_BUFFER_BIT
        )


        # ----------------------------------------------------
        # CAMERA
        # ----------------------------------------------------

        view = glm.lookAt(
            camera_pos,
            camera_pos + camera_front,
            camera_up
        )


        # ----------------------------------------------------
        # SHADER
        # ----------------------------------------------------

        glUseProgram(program)


        set_mat4(
            program,
            "view",
            view
        )

        set_mat4(
            program,
            "projection",
            projection
        )


        set_vec3(
            program,
            "viewPos",
            camera_pos
        )


        # ====================================================
        # DIRECTIONAL LIGHT
        # ====================================================

        set_vec3(
            program,
            "dirLightDirection",
            directional_direction
        )

        set_vec3(
            program,
            "dirLightColor",
            directional_color
        )

        set_bool(
            program,
            "dirLightEnabled",
            directional_enabled
        )


        # ====================================================
        # POINT LIGHT
        # ====================================================

        set_vec3(
            program,
            "pointLightPosition",
            point_light_position
        )

        set_vec3(
            program,
            "pointLightColor",
            point_color
        )

        set_bool(
            program,
            "pointLightEnabled",
            point_enabled
        )


        # ====================================================
        # SPOT LIGHT
        # ====================================================

        # Spotlight follows the camera

        set_vec3(
            program,
            "spotLightPosition",
            camera_pos
        )

        set_vec3(
            program,
            "spotLightDirection",
            camera_front
        )

        set_vec3(
            program,
            "spotLightColor",
            spot_color
        )


        set_float(
            program,
            "spotCutOff",
            glm.cos(
                glm.radians(12.5)
            )
        )

        set_float(
            program,
            "spotOuterCutOff",
            glm.cos(
                glm.radians(17.5)
            )
        )


        set_bool(
            program,
            "spotLightEnabled",
            spot_enabled
        )


        # ====================================================
        # BEDROOM
        # ====================================================


        # ----------------------------------------------------
        # FLOOR
        # ----------------------------------------------------

        draw_cube(
            program,
            vao,
            glm.vec3(0.0, -0.15, 0.0),
            glm.vec3(10.0, 0.3, 10.0),
            glm.vec3(0.35, 0.25, 0.18)
        )


        # ----------------------------------------------------
        # BACK WALL
        # ----------------------------------------------------

        draw_cube(
            program,
            vao,
            glm.vec3(0.0, 3.0, -5.0),
            glm.vec3(10.0, 6.0, 0.3),
            glm.vec3(0.55, 0.45, 0.35)
        )


        # ----------------------------------------------------
        # LEFT WALL
        # ----------------------------------------------------

        draw_cube(
            program,
            vao,
            glm.vec3(-5.0, 3.0, 0.0),
            glm.vec3(0.3, 6.0, 10.0),
            glm.vec3(0.50, 0.40, 0.30)
        )


        # ----------------------------------------------------
        # RIGHT WALL
        # ----------------------------------------------------

        draw_cube(
            program,
            vao,
            glm.vec3(5.0, 3.0, 0.0),
            glm.vec3(0.3, 6.0, 10.0),
            glm.vec3(0.50, 0.40, 0.30)
        )


        # ----------------------------------------------------
        # CEILING
        # ----------------------------------------------------

        draw_cube(
            program,
            vao,
            glm.vec3(0.0, 6.0, 0.0),
            glm.vec3(10.0, 0.3, 10.0),
            glm.vec3(0.30, 0.30, 0.32)
        )


        # ====================================================
        # BED
        # ====================================================


        # ----------------------------------------------------
        # Bed base
        # ----------------------------------------------------

        draw_cube(
            program,
            vao,
            glm.vec3(-1.5, 0.65, -1.0),
            glm.vec3(3.5, 0.5, 5.5),
            glm.vec3(0.25, 0.12, 0.07)
        )


        # ----------------------------------------------------
        # Mattress
        # ----------------------------------------------------

        draw_cube(
            program,
            vao,
            glm.vec3(-1.5, 1.15, -1.0),
            glm.vec3(3.3, 0.55, 5.2),
            glm.vec3(0.75, 0.75, 0.72)
        )


        # ----------------------------------------------------
        # Pillow 1
        # ----------------------------------------------------

        draw_cube(
            program,
            vao,
            glm.vec3(-2.2, 1.55, -2.7),
            glm.vec3(1.2, 0.25, 0.7),
            glm.vec3(0.85, 0.85, 0.82)
        )


        # ----------------------------------------------------
        # Pillow 2
        # ----------------------------------------------------

        draw_cube(
            program,
            vao,
            glm.vec3(-0.8, 1.55, -2.7),
            glm.vec3(1.2, 0.25, 0.7),
            glm.vec3(0.85, 0.85, 0.82)
        )


        # ----------------------------------------------------
        # Headboard
        # ----------------------------------------------------

        draw_cube(
            program,
            vao,
            glm.vec3(-1.5, 2.3, -3.45),
            glm.vec3(3.6, 2.5, 0.25),
            glm.vec3(0.20, 0.10, 0.05)
        )


        # ----------------------------------------------------
        # Bed legs
        # ----------------------------------------------------

        bed_leg_color = glm.vec3(
            0.15,
            0.08,
            0.04
        )


        for x in [-2.8, -0.2]:

            for z in [-3.0, 1.3]:

                draw_cube(
                    program,
                    vao,
                    glm.vec3(x, 0.25, z),
                    glm.vec3(0.3, 0.6, 0.3),
                    bed_leg_color
                )


        # ====================================================
        # TABLE
        # ====================================================


        table_color = glm.vec3(
            0.35,
            0.18,
            0.08
        )


        # ----------------------------------------------------
        # Table top
        # ----------------------------------------------------

        draw_cube(
            program,
            vao,
            glm.vec3(2.8, 1.8, -2.8),
            glm.vec3(2.2, 0.3, 1.5),
            table_color
        )


        # ----------------------------------------------------
        # Table legs
        # ----------------------------------------------------

        for x in [2.0, 3.6]:

            for z in [-3.3, -2.3]:

                draw_cube(
                    program,
                    vao,
                    glm.vec3(x, 0.9, z),
                    glm.vec3(0.25, 1.8, 0.25),
                    table_color
                )


        # ====================================================
        # TABLE LAMP
        # ====================================================


        # Lamp stand

        draw_cube(
            program,
            vao,
            glm.vec3(2.8, 2.5, -2.8),
            glm.vec3(0.15, 1.2, 0.15),
            glm.vec3(0.12, 0.12, 0.12)
        )


        # Lamp shade

        draw_cube(
            program,
            vao,
            glm.vec3(2.8, 3.15, -2.8),
            glm.vec3(0.9, 0.45, 0.9),
            glm.vec3(0.95, 0.70, 0.25)
        )


        # ----------------------------------------------------
        # SWAP
        # ----------------------------------------------------

        glfw.swap_buffers(window)


    # ========================================================
    # CLEANUP
    # ========================================================

    glDeleteVertexArrays(
        1,
        [vao]
    )

    glDeleteBuffers(
        1,
        [vbo]
    )

    glDeleteProgram(program)

    glfw.terminate()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()