"""
Copyright (c) Cutleast
"""

import xml.etree.ElementTree as ET
from xml.dom.minidom import Document, parseString


def split_frames(xml_element: ET.Element) -> ET.Element:
    """
    Split frames in an XML element recursively and return the
    modified XML element with frames.

    Args:
        xml_element (ET.Element): XML element to split.

    Returns:
        ET.Element: Modified XML element with frames.
    """

    new_frame = ET.Element("frame")
    current_frame: int = 1
    new_frame.set("frameId", str(current_frame))
    new_frame_subtags = ET.Element("subTags")
    new_frame.append(new_frame_subtags)

    frame_delimiters: list[ET.Element] = xml_element.findall(
        "./item[@type='ShowFrameTag']"
    )

    # Iterate over all child elements
    children: list[ET.Element] = xml_element.findall("./")
    for child in children:
        # Split child recursively
        child = split_frames(child)

        # If child is not a frame delimiter
        if len(frame_delimiters) > 1:
            # Remove child from xml_element
            xml_element.remove(child)

            # If child is not a frame delimiter
            if child.get("type") != "ShowFrameTag":
                # Append child to current frame
                new_frame_subtags.append(child)

            # If child is a frame delimiter
            elif child in frame_delimiters:
                xml_element.append(new_frame)
                # Create new frame
                new_frame = ET.Element("frame")
                current_frame += 1
                new_frame.set("frameId", str(current_frame))
                new_frame_subtags = ET.Element("subTags")
                new_frame.append(new_frame_subtags)

    return xml_element


def unsplit_frames(xml_element: ET.Element) -> ET.Element:
    """
    This function is a reverse of `split_frames`.

    Args:
        xml_element (ET.Element): XML element to revert.

    Returns:
        ET.Element: Reverted XML element.
    """

    children: list[ET.Element] = xml_element.findall("./")
    for child in children:
        frames: list[ET.Element] = child.findall("./frame")

        for frame in frames:
            child.remove(frame)

            for frame_child in frame.findall("./subTags/"):
                child.append(frame_child)

            frame_tag = ET.Element("item")
            frame_tag.set("type", "ShowFrameTag")
            child.append(frame_tag)

        unsplit_frames(child)

    return xml_element


def beautify_xml(xml_string: str) -> str:
    """
    Beautify an XML string.

    Args:
        xml_string (str): XML string to beautify.

    Returns:
        str: Beautified XML string.
    """

    try:
        dom: Document = parseString(xml_string)
        pretty_xml: str = dom.toprettyxml()

        lines: list[str] = pretty_xml.splitlines()
        lines = [line + "\n" for line in lines if line.strip()]
        return "".join(lines)
    except Exception as ex:
        print(ex)

        return xml_string
