def replace_text(text, swapped=False):
    replacements = {
        '\\': 'á',
        '/': 'é',
        ':': 'í',
        '*': 'ó',
        '<': 'ú',
        '>': 'Á',
        '|': 'É',
        '.': 'Í'
    }

    if swapped:
        replacements = {v: k for k, v in replacements.items()}


    for original, new in replacements.items():
        text = text.replace(original, new)

    return text