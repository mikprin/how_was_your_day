
def format_conversation_from_list(conversation):
    """Format conversation from list"""
    formatted_conversation = ""
    for pice in conversation:
        pice = pice.replace("\n", "")
        formatted_conversation += f"{pice}\n"
    return formatted_conversation