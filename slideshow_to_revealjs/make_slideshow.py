#!/usr/bin/env python3
"""
This script is designed to convert OpenOffice/LibreOffice Impress slideshows
to JavaScript-based slideshows using Reveal.js. It is far from perfect but does
manage to correctly extract more or less all of the text and to preserve the
formatting using semantic-type tagging, which is a start. Much hand-editing of
the results is required.

This script is copyright 2026 by Patrick Mooney. It is licensed under the GNU
GPL, either version 3 or (at your option) any later version. See the file
LICENSE.md for details.

System: Linux
Dependencies: LibreOffice 24.8, Pandoc, HTML Tidy, BeautifulSoup4
"""


import re
import shutil
import subprocess
import sys
import zipfile

from pathlib import Path
from typing import Dict, List, Optional, Set, Union

from bs4 import BeautifulSoup, NavigableString, Tag     # https://beautiful-soup-4.readthedocs.io/en/latest/#


# Constants
SOFFICE_PATH: Path = Path("/home/patrick/bin/libreoffice24/program/soffice")
PANDOC_PATH: Path = Path(shutil.which("pandoc"))
TIDY_PATH: Path = Path(shutil.which("tidy"))


def sanitize_filename_string(filename: str) -> str:
    """
    Sanitizes file names by replacing spaces, punctuation, and all non-alphanumeric
    special characters with clean, uniform underscores.
    """
    assert isinstance(filename, str)
    changed: bool = True            # run through the replacement loop at least once
    prev: str

    while changed:
        changed, prev = False, filename
        sanitized: str = re.sub(r'[^a-zA-Z0-9-]+', '-', filename)
        sanitized = sanitized.replace('--', '-')
        changed = sanitized != prev
        filename = sanitized

    return filename.strip('-').casefold()


def extract_odp_images(odp_path: Path,
                       output_base_name: str,
                       output_dir: Path) -> Optional[Path]:
    """
    Unzips the internal media payload from an ODP file using local relative paths
    and drops its contents into a presentation-isolated sanitized assets directory
    ending with the '_images' suffix.
    """
    assert isinstance(odp_path, Path)
    assert isinstance(output_dir, Path)
    assert isinstance(output_base_name, str)
    assert odp_path.is_file()
    assert output_dir.is_dir()

    target_img_dir: Path = output_dir / f"{output_base_name}_images"

    if not zipfile.is_zipfile(odp_path):
        print(f"    [!] Error: '{odp_path.name}' is not recognized as a valid zip archive.")
        return None

    with zipfile.ZipFile(odp_path, 'r') as archive:
        picture_files: list[str] = [f for f in archive.namelist() if f.startswith('Pictures/')]

        if not picture_files:
            print("    [-] Note: No embedded slide images located inside this presentation archive.")
            return None

        target_img_dir.mkdir(parents=True, exist_ok=True)
        print(f"    [+] Extracting {len(picture_files)} embedded image assets into './{target_img_dir.name}/'...")

        file_info_name: str
        for file_info_name in picture_files:
            source_path: Path = Path(file_info_name)
            destination_file_path: Path = target_img_dir / source_path.name

            file_data: bytes = archive.read(file_info_name)
            destination_file_path.write_bytes(file_data)

    return target_img_dir


def repair_lists(soup: BeautifulSoup) -> BeautifulSoup:
    """Pandoc sometimes generates malformed nested lists. This function detects and
    fixes such lists.       #FIXME: do we want to do this with ordered lists too?
    """
    assert isinstance(soup, BeautifulSoup)
    sub_ul: Tag
    for sub_ul in soup.find_all('ul'):
        parent: Optional[Tag] = sub_ul.parent
        if parent and parent.name == 'ul':
            prev_li: Optional[Tag] = sub_ul.find_previous_sibling('li')
            if prev_li:
                prev_li.append(sub_ul.extract())

    return soup


def purge_page_breaks(soup: BeautifulSoup) -> BeautifulSoup:
    """Pandoc's export sometimes includes page breaks embedded in tag styles as part
    of the exported outline. This function removes them.
    """
    assert isinstance(soup, BeautifulSoup)
    tag: Tag
    for tag in soup.find_all(style=True):
        style_str: str = tag['style']
        # Remove page-break definitions while leaving other styles unaltered
        purged_style: str = re.sub(r'page-break-(before|after|inside)\s*:\s*[^;]+;?',
                                   '', style_str, flags=re.IGNORECASE)
        purged_style = purged_style.strip()
        if purged_style:
            tag['style'] = purged_style
        else:
            del tag['style']

    return soup


def partition_into_slides(soup: BeautifulSoup) -> BeautifulSoup:
    """Partition the outline into slides suing <section> elements.
    """
    assert isinstance(soup, BeautifulSoup)
    body: Optional[Tag] = soup.body

    elements: list = list(body.contents)
    body.clear()

    current_section: Optional[Tag] = None
    el: Union[Tag, str]
    for el in elements:
        if isinstance(el, str) and not el.strip():
            continue

        tag_name: Optional[str] = getattr(el, 'name', None)

        if tag_name in ['h1', 'h2']:
            is_stacked_header: bool = False
            if current_section and len(current_section.contents) > 0:
                last_element: any = current_section.contents[-1]
                if getattr(last_element, 'name', None) in ['h1', 'h2']:
                    is_stacked_header = True

            if is_stacked_header:
                current_section.append(el)
            else:
                if current_section:
                    body.append(current_section)
                current_section = soup.new_tag('section')
                current_section.append(el)
        else:
            if current_section:
                current_section.append(el)
            else:
                current_section = soup.new_tag('section')
                current_section.append(el)

    if current_section:
        has_only_headers: bool = True
        child: any
        for child in current_section.contents:
            if getattr(child, 'name', None) not in ['h1', 'h2', None]:
                has_only_headers = False
                break
        if has_only_headers:
            current_section.append(soup.new_string(""))
        body.append(current_section)

    return soup


def collapse_adjacent_h2s(soup: BeautifulSoup) -> BeautifulSoup:
    """Take the tag structure represented by SOUP and find any strings of consecutive
    <h2> tags, and collapse them into a single <div> that contains all the content
    of those header tags.
    """
    h2_tags: List[Tag] = soup.find_all("h2")
    processed: List[Tag] = list()

    try:
        for h2 in h2_tags:
            if h2 in processed:
                continue

            # 1. Gather adjacent h2 elements
            adjacent_h2s: List[Tag] = [h2]
            current: Optional[Union[Tag, NavigableString]] = h2.next_sibling

            while current:
                if isinstance(current, NavigableString) and not current.strip():
                    current = current.next_sibling
                    continue
                if isinstance(current, Tag) and current.name == "h2":
                    adjacent_h2s.append(current)
                    current = current.next_sibling
                else:
                    break

            # 2. Process and merge if a sequence is found
            if len(adjacent_h2s) > 1:
                new_div: Tag = soup.new_tag("div")

                div_id: Optional[str] = None
                div_classes: List[str] = []
                div_styles: List[str] = []
                other_attrs: Dict[str, str] = {}

                for tag in adjacent_h2s:
                    attr_name: str
                    attr_value: Union[str, List[str]]
                    for attr_name, attr_value in tag.attrs.items():

                        if attr_name == "id":
                            if not div_id and isinstance(attr_value, str):
                                div_id = attr_value

                        elif attr_name == "class":
                            cls_list: List[str] = attr_value if isinstance(attr_value, list) else [attr_value]
                            for cls in cls_list:
                                if cls not in div_classes:
                                    div_classes.append(cls)

                        elif attr_name == "style" and isinstance(attr_value, str):
                            stripped_style: str = attr_value.strip()
                            if stripped_style:
                                if not stripped_style.endswith(";"):
                                    stripped_style += ";"
                                div_styles.append(stripped_style)

                        else:
                            val_str: str = " ".join(attr_value) if isinstance(attr_value, list) else str(attr_value)
                            if attr_name not in other_attrs:
                                other_attrs[attr_name] = val_str
                            else:
                                if val_str not in other_attrs[attr_name].split():
                                    other_attrs[attr_name] += f" {val_str}"

                if div_id:
                    new_div["id"] = div_id
                if div_classes:
                    new_div["class"] = div_classes
                if div_styles:
                    new_div["style"] = " ".join(div_styles)

                attr_key: str
                attr_val: str
                for attr_key, attr_val in other_attrs.items():
                    new_div[attr_key] = attr_val

                # 3. Modify the DOM layout
                h2.insert_before(new_div)

                i: int
                tag: Tag
                for i, tag in enumerate(adjacent_h2s):
                    # Explicitly extract individual nodes one by one by index 0
                    while tag.contents:
                        new_div.append(tag.contents[0])
                    if i < len(adjacent_h2s) - 1:
                        new_div.append(soup.new_tag("br"))

                    processed.append(tag)
                    tag.decompose()

    except Exception as errrr:
        print(f"        ... error cleaning <h2> elements: {errrr}")
        raise errrr

    return soup


def repair_and_section_html(html_path: Path) -> None:
    """Parses the intermediate HTML file, repairs LibreOffice's malformed nested list syntax,
    purges unnecessary page-break inline styles, and programmatically groups
    elements into semantic <section> tags. All of this is intended to help ensure
    the intermediate HTML file to be processed by Pandoc is valid and correctly
    encodes the slide data semantically.
    """
    assert isinstance(html_path, Path)
    assert html_path.is_file()

    content: str = html_path.read_text(encoding='utf-8')
    soup: BeautifulSoup = BeautifulSoup(content, 'html.parser')

    body: Optional[Tag] = soup.body
    if not body:
        raise RuntimeError("Unable to parse intermediate HTML generated by LibreOffice! (No <body> tag found.)")

    # Phase 1: Structural Repair of Malformed Nested Lists
    soup = repair_lists(soup)

    # Phase 2: Purge redundant LibreOffice page-break style elements
    soup = purge_page_breaks(soup)

    # Phase 3: Structural partitioning into semantic slide sections
    soup = partition_into_slides(soup)

    # Phase 4: any other repairs needed?
    soup = collapse_adjacent_h2s(soup)

    html_path.write_text(str(soup), encoding='utf-8')


def process_single_presentation(source_doc: Path, local_dir: Path) -> None:
    """
    Executes the sequential compilation chain strictly within the local directory context,
    ensuring non-overlapping names protect production documents from automated unlinking.
    """
    raw_base_name: str = source_doc.stem
    clean_base_name: str = sanitize_filename_string(raw_base_name)

    # Isolate intermediate stages cleanly using a distinct temporary extension suffix
    libreoffice_output_html: Path = local_dir / f"{raw_base_name}.html"
    intermediate_html: Path = local_dir / f"{clean_base_name}_intermediate_temp.html"
    raw_slideshow: Path = local_dir / f"{clean_base_name}_raw_temp.html"
    production_slideshow: Path = local_dir / f"{clean_base_name}.html"

    print(f"[*] Starting processing for target file: {source_doc.name}")

    # Step 1: ODP image asset extraction        # FIXME: we're going to have to handle non-ODP formats differently
    extract_odp_images(source_doc, clean_base_name, local_dir)

    # Step 2: headless LibreOffice conversion
    libreoffice_cmd: list[str] = [
        str(SOFFICE_PATH),
        "--headless",
        "--convert-to", "html:impress_html_Export",
        str(source_doc),
        "--outdir", str(local_dir)
    ]
    print("    [2/5] Running isolated LibreOffice 24 compiler export...")
    subprocess.run(libreoffice_cmd, check=True)

    # Rename LibreOffice's direct file creation to our protected intermediate tracking name
    if libreoffice_output_html.exists():
        libreoffice_output_html.rename(intermediate_html)

    # Step 3: Programmatic DOM Structural Cleanup Pass
    print("    [3/5] Executing BeautifulSoup4 structural DOM validation pass...")
    if intermediate_html.exists():
        repair_and_section_html(intermediate_html)
    else:
        print(f"    [!] Error: Expected intermediate file '{intermediate_html.name}' was not found.")
        return

    # Step 4: Local Pandoc Presentation Compilation with Explicit Light Theme Injection
    pandoc_cmd: list[str] = [
        str(PANDOC_PATH),
        "-f", "html",
        "-t", "revealjs",
        str(intermediate_html),
        "-o", str(raw_slideshow),
        "-s",
        "--slide-level=1",
        "-V", "theme=light",        # Explicitly force light theme
        "-V", "revealjs-url=/~patrick/res/revealjs/",
        "-V", "css=/~patrick/css/reveal-custom.css",
        "-V", "width=1050",
        "-V", "height=590"
    ]
    print("    [4/5] Compiling responsive Reveal.js slideshow via Pandoc...")
    subprocess.run(pandoc_cmd, check=True)

    # FIXME! We need another HTML-massaging pass in here, to consist of:
    #  * getting the correct title in the <title> element of the slideshow
    #  * putting lang="en" on the <HTML> tag
    #  * eliminating duplicate <meta name="generator"> tags
    #  * eliminate <h1> and <h2> tags containing the same text content as the first non-heading tab?
    #  * what else?

    # Step 5: Local HTML Tidy Code Unwrapping and Cleanup (Altered layout indentation spacing to 2)
    tidy_cmd: list[str] = [
        str(TIDY_PATH),
        "-indent",
        "-wrap", "0",
        "--indent-spaces", "2",
        str(raw_slideshow)
    ]
    print("    [5/5] Beautifying and unwrapping final source lines with HTML Tidy...")

    with open(production_slideshow, 'w', encoding='utf-8') as out_f:
        subprocess.run(tidy_cmd, stdout=out_f, stderr=subprocess.DEVNULL)

    # Clean up temporary storage files safely without unlinking production_slideshow
    if intermediate_html.exists():
        intermediate_html.unlink()
    if raw_slideshow.exists():
        raw_slideshow.unlink()

    print(f"[+] Successfully generated sanitized file locally: {production_slideshow.name}\n")


def main() -> None:
    local_dir: Path = Path(".")
    odp_files: list[Path] = list(local_dir.glob("*.odp"))

    if not odp_files:
        print(f"[-] No presentation files (*.odp) located in the active directory context.")
        sys.exit(0)

    print(f"[+] Found {len(odp_files)} presentation files to convert inside the active directory context.\n")

    odp: Path
    for odp in sorted(odp_files):
        try:
            process_single_presentation(odp, local_dir)
        except subprocess.CalledProcessError as err:
            print(f"[!] Compilation failed on '{odp.name}': {err}")
        except Exception as err:
            print(f"[!] Unexpected processing error occurred on '{odp.name}': {err}")


if __name__ == "__main__":
    main()
