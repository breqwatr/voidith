""" Library for rendering Jinja2 templates """

import os

from jinja2 import Template

import voithos.lib


def apply_template(jinja2_file, output_file, replacements):
    """ Replace the replacements values in jinja2_file, write to output_file

        jinja2_file is a relative path, prefixed with the site-packages location of
        voithos/lib/files. To call the horizon.conf.j2 file you'd use 'horizon/horizon.conf.j2'
    """
    files_dir = "{}/files".format(os.path.dirname(voithos.lib.__file__))
    jinja2_file_full_path = f"{files_dir}/{jinja2_file}"
    with open(jinja2_file_full_path, "r") as j2_file:
        j2_text = j2_file.read()
    template = Template(j2_text)
    replaced_text = template.render(**replacements)
    with open(output_file, "w+") as write_file:
        write_file.write(replaced_text)
