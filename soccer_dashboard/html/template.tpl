{% extends "template.tpl" %}
{% block styles %}
<style>
@font-face {
    font-family: 'Rubik Mono One';
    src: url('https://raw.githubusercontent.com/google/fonts/main/ofl/rubikmonoone/RubikMonoOne-Regular.ttf') format('truetype');
}
@font-face {
    font-family: 'Ubuntu';
    src: url('https://raw.githubusercontent.com/google/fonts/main/ufl/ubuntu/Ubuntu-Bold.ttf') format('truetype');
}
@font-face {
    font-family: 'Lato';
    src: url('https://raw.githubusercontent.com/google/fonts/main/ofl/lato/Lato-Bold.ttf') format('truetype');
}
@font-face {
    font-family: 'Roboto Mono';
    src: url('https://raw.githubusercontent.com/google/fonts/main/apache/robotomono/RobotoMono[wght].ttf') format('truetype');
}
@font-face {
    font-family: 'Inter';
    src: url('https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter[slnt,wght].ttf') format('truetype');
}
.scrollable-table {
    overflow-x: auto;
    white-space: nowrap;
}
#T_{{ uuid }} th, #T_{{ uuid }} td {
    font-family: 'RubikMonoOne', sans-serif; /* Default font */
    color: gold;
    border-color: #ffbd6d;
}
#T_{{ uuid }} .blank.level0 {
    background-color: transparent;
    color: floralwhite;
    border-color: #ffbd6d;
    text-align: center;
}
#T_{{ uuid }} .blank.hover {
    background-color: transparent;
    color: black;
    border-color: #ffbd6d;
    text-align: center;
}
{% for column in gradient_columns %}
#T_{{ uuid }} td.col{{ loop.index0 }} {
    background: linear-gradient(to bottom, #ffbd6d, #1f4068);
}
{% endfor %}
</style>
{% endblock styles %}
{% block table %}
<div class="scrollable-table">
    {{ super() }}
</div>
{% endblock table %}
