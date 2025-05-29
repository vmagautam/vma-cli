from jinja2 import Environment, FileSystemLoader

def get_template_env(template_dir: str):
    return Environment(loader=FileSystemLoader(template_dir)) 