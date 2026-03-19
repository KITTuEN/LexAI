# Convert potentially UTF-16LE models_list.txt to UTF-8
with open('models_list.txt', 'rb') as f:
    content = f.read()
    try:
        text = content.decode('utf-16le')
        with open('models_list.txt', 'w', encoding='utf-8') as fw:
            fw.write(text)
        print("Converted models_list.txt to UTF-8")
    except Exception as e:
        print(f"Error converting: {e}")
