//from: https://blog.tammearu.eu/posts/gllines/
#version 330 core
layout (lines_adjacency) in;
layout (triangle_strip, max_vertices = 4) out;
in vec4 v_color[4];
out vec4 g_color;

uniform mat4 _ModelToClip;
uniform float _LineWidth;

void main() {
    vec3 prev = gl_in[0].gl_Position.xyz;
    vec3 start = gl_in[1].gl_Position.xyz;
    vec3 end = gl_in[2].gl_Position.xyz;
    vec3 next = gl_in[3].gl_Position.xyz;

    vec3 lhs = cross(normalize(end-start), vec3(0.0, 0.0, -1.0));

    // is previous line segment a zero vector?
    bool colStart = length(start-prev) < 0.0001; // 0.0001 is arbitrary epsilon
    // is next line segment a zero vector?
    bool colEnd = length(end-next) < 0.0001;

    vec3 a = normalize(start-prev);
    vec3 b = normalize(start-end);
    vec3 c = (a+b)*0.5;
    vec3 startLhs = normalize(c) * sign(dot(c, lhs));
    a = normalize(end-start);
    b = normalize(end-next);
    c = (a+b)*0.5;
    vec3 endLhs = normalize(c) * sign(dot(c, lhs));

    if(colStart)
        startLhs = lhs;
    if(colEnd)
        endLhs = lhs;

    float startInvScale = dot(startLhs, lhs);
    float endInvScale = dot(endLhs, lhs);

    startLhs *= _LineWidth*0.5;
    endLhs *= _LineWidth*0.5;

    gl_Position = _ModelToClip*vec4(start+startLhs/startInvScale, 1.0);
    g_color = v_color[1];
    EmitVertex();
    gl_Position = _ModelToClip*vec4(start-startLhs/startInvScale, 1.0);
    EmitVertex();
    gl_Position = _ModelToClip*vec4(end+endLhs/endInvScale, 1.0);
    g_color = v_color[2];
    EmitVertex();
    gl_Position = _ModelToClip*vec4(end-endLhs/endInvScale, 1.0);
    EmitVertex();
    EndPrimitive();
}