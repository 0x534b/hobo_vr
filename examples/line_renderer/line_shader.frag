#version 330
uniform float antialias;
uniform float thickness;
uniform float linelength;
in float v_thickness;
in vec2 v_uv;
in vec3 v_normal;
out vec4 fragColor;
void main() {
    float d = 0;
    float w = v_thickness/2.0 - antialias;

    vec3 color = vec3(0.0, 0.0, 0.0);
    if (v_normal.z < 0)
        color = 0.75*vec3(pow(abs(v_normal.z),.5)); //*vec3(0.95, 0.75, 0.75);

    // Cap at start
    if (v_uv.x < 0)
        d = length(v_uv) - w;
    // Cap at end
    else if (v_uv.x >= linelength)
        d = length(v_uv - vec2(linelength,0)) - w;
    // Body
    else
        d = abs(v_uv.y) - w;
    if( d < 0) {
        fragColor = vec4(color, 1.0);
    } else {
        d /= antialias;
        fragColor = vec4(color, exp(-d*d));
    }
} 