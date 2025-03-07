from leafnode import LeafNode
from textnode import TextNode, TextType
from blocktype import BlockType
import re


def text_node_to_html_node(text_node):
    match text_node.text_type:
        case TextType.TEXT:
            leaf_node = LeafNode(
                None,
                text_node.text
            )
        case TextType.BOLD:
            leaf_node = LeafNode(
                "b",
                text_node.text
            )
        case TextType.ITALIC:
            leaf_node = LeafNode(
                "i",
                text_node.text
            )
        case TextType.CODE:
            leaf_node = LeafNode(
                "code",
                text_node.text
            )
        case TextType.LINK:
            leaf_node = LeafNode(
                "a",
                text_node.text,
                {"href": text_node.url}
            )
        case TextType.IMAGE:
            leaf_node = LeafNode(
                "img",
                "",
                {
                    "src": text_node.url,
                    "alt": text_node.text
                }
            )
        case _:
            raise Exception("Wrong type")
    
    return leaf_node


def split_nodes_delimiter(old_nodes, delimiter, text_type):
    """
    It takes a list of "old nodes", a delimiter, and a text type. It should return a new list of nodes, 
    where any "text" type nodes in the input list are (potentially) split into multiple nodes based on 
    the syntax.
    """

    new_nodes = []
    for old_node in old_nodes:
        if old_node.text_type != TextType.TEXT:
            new_nodes.append(old_node)
            continue
        parts = old_node.text.split(delimiter)
        if len(parts) % 2 == 0:
            raise Exception(f"Unmatched delimiter '{delimiter}' in text: {old_node.text}")
        for i, part in enumerate(parts):
            type_to_use = text_type if i % 2 == 1 else TextType.TEXT
            if part:
                new_nodes.append(TextNode(part, type_to_use))
    return new_nodes


def extract_markdown_images(text):
    matches = re.findall(r"!\[([^\[\]]*)\]\(([^\(\)]*)\)", text)
    return matches


def extract_markdown_links(text):
    matches = re.findall(r"\[([^\[\]]*)\]\(([^\(\)]*)\)", text)
    return matches


def split_nodes_link(old_nodes):
    """
    It takes a list of "old nodes". It should return a new list of nodes, 
    where any "text" type nodes in the input list are (potentially) split into multiple nodes that are either texts or links.
    """

    new_nodes = []
    for old_node in old_nodes:
        if old_node.text_type != TextType.TEXT:
            new_nodes.append(old_node)
            continue
        links = extract_markdown_links(old_node.text)
        if not links:
            new_nodes.append(old_node)
        else:
            current_text = old_node.text
            for link in links:
                text_parts = current_text.split(f"[{link[0]}]({link[1]})", 1)
                if text_parts[0]:
                    new_nodes.append(TextNode(text_parts[0], TextType.TEXT))
                new_nodes.append(TextNode(link[0], TextType.LINK, link[1]))
                current_text = text_parts[1]
            if current_text:
                new_nodes.append(TextNode(current_text, TextType.TEXT))                         
    return new_nodes


def split_nodes_image(old_nodes):
    """
    It takes a list of "old nodes". It should return a new list of nodes, 
    where any "text" type nodes in the input list are (potentially) split into multiple nodes that are either texts or images.
    """

    new_nodes = []
    for old_node in old_nodes:
        if old_node.text_type != TextType.TEXT:
            new_nodes.append(old_node)
            continue
        images = extract_markdown_images(old_node.text)
        if not images:
            new_nodes.append(old_node)
        else:
            current_text = old_node.text
            for image in images:
                text_parts = current_text.split(f"![{image[0]}]({image[1]})", 1)
                if text_parts[0]:
                    new_nodes.append(TextNode(text_parts[0], TextType.TEXT))
                new_nodes.append(TextNode(image[0], TextType.IMAGE, image[1]))
                current_text = text_parts[1]
            if current_text:
                new_nodes.append(TextNode(current_text, TextType.TEXT))                         
    return new_nodes


def text_to_textnodes(text):
    textnode = TextNode(text, TextType.TEXT)
    nodes = split_nodes_delimiter([textnode], "**", TextType.BOLD)
    nodes = split_nodes_delimiter(nodes, "_", TextType.ITALIC)
    nodes = split_nodes_delimiter(nodes, "`", TextType.CODE)
    nodes = split_nodes_image(nodes)
    nodes = split_nodes_link(nodes)
    return nodes


def markdown_to_blocks(markdown):
    """
    It takes a raw Markdown string (representing a full document) as input and returns a list of "block" strings.
    """
    
    result = []
    blocks = markdown.split("\n\n")
    for block in blocks:
        block = block.strip()
        if block:
            lines = block.split("\n")
            cleaned_lines = [line.strip() for line in lines]
            cleaned_block = "\n".join(cleaned_lines)
            result.append(cleaned_block)
    return result


def block_to_block_type(markdown):
    lines = markdown.split("\n")
    match markdown:
        case markdown if re.search("^#{1,6}\s{1}.+$", markdown):
            return BlockType.HEADING
        case markdown if re.search("^`{3}.+`{3}$", markdown):
            return BlockType.CODE
        case markdown if all(re.search("^\>.+$", line) for line in lines):
            return BlockType.QUOTE
        case markdown if all(re.search("^\- .+$", line) for line in lines):
            return BlockType.UNORDERED_LIST
        case markdown if all(re.search("^\d\. .+$", line) for line in lines):
            return BlockType.ORDERED_LIST
        case _:
            return BlockType.PARAGRAPH
