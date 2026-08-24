content = get_webpage("www.informations.com")
result = content if not (content is None) else "The content of www.informations.com could not be retrieved."
result