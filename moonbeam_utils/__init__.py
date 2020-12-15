def emojify(text):
    emojified_text = ''
    for char in text:
        if char.lower() in 'abcdefghijklmnopqrstuvwxyz':
            emojified_text += f':alphabet-white-{char}:'
        elif char == " ":
            emojified_text += "     "
        elif char == "@":
            emojified_text += ":alphabet-white-at:"
        elif char == "#":
            emojified_text += ":alphabet-white-hash:"
        elif char == "?":
            emojified_text += ":alphabet-white-question:"
        elif char == "!":
            emojified_text += ":alphabet-white-exclamation:"
        elif char == "":
            emojified_text += ":alphabet-white-:"
        elif char == "1":
            emojified_text += ":one:"
        elif char == "2":
            emojified_text += ":two:"
        elif char == "3":
            emojified_text += ":three:"
        elif char == "4":
            emojified_text += ":four:"
        elif char == "5":
            emojified_text += ":five:"
        elif char == "6":
            emojified_text += ":six:"
        elif char == "7":
            emojified_text += ":seven:"
        elif char == "8":
            emojified_text += ":eight:"
        elif char == "9":
            emojified_text += ":nine:"
        elif char == "0":
            emojified_text += ":zero:"
        elif char == '-':
            emojified_text += ":heavy_minus_sign:"
        elif char == "+":
            emojified_text += ":heavy_plus_sign:"
        elif char == "*":
            emojified_text += ":keycap_star:"
        elif char == ">":
            emojified_text += ":arrow_forward:"
        elif char == "<":
            emojified_text += ":arrow_backward:"
        elif char == ",":
            emojified_text += ":alphabet-white-comma:"
        elif char == ".":
            emojified_text += ":alphabet-white-period:"
        elif char == ":":
            emojified_text += ":alphabet-white-colon:"
        elif char == ";":
            emojified_text += ":alphabet-white-semicolon:"
        elif char == "_":
            emojified_text += ":alphabet-white-underscore:"
        else:
            emojified_text += char
    return emojified_text
