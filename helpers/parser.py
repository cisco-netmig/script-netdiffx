import logging
logger = logging.getLogger(__name__)

import re

class ConfigParser:
    """
    Parses hierarchical configuration data from raw text input.

    Attributes:
        raw (str): Raw input configuration text.
        config (list): Parsed configuration in a hierarchical structure.
    """

    def __init__(self, raw):
        """
        Initializes the ConfigParser instance.

        Args:
            raw (str): Raw configuration data to be parsed.
        """
        logger.info("Initializing ConfigParser...")
        self.raw = raw
        self.config = self.parse(raw)

    def parse(self, raw):
        """
        Parses the raw input configuration into a hierarchical structure.

        Args:
            raw (str): The raw configuration text.

        Returns:
            list: A list representing the parsed configuration.
        """
        logger.info("Parsing configuration data...")
        lines = raw.splitlines()
        config = []
        line_idx = 0

        while line_idx < len(lines):
            if line_idx > len(lines) - 1:
                break
            if line_idx == len(lines) - 1:
                config.append(lines[line_idx])
                break

            curr_indent = self.get_indent(line_idx, lines)
            next_indent = self.get_indent(line_idx + 1, lines)

            if next_indent > curr_indent:
                key = lines[line_idx]
                line_idx += 1
                body = self.get_body(line_idx, lines)
                config.append({key: self.parse('\n'.join(body))})
                line_idx += len(body) - 1
            else:
                config.append(lines[line_idx])

            line_idx += 1

        logger.info("Configuration parsing completed.")
        return config

    def get_indent(self, posx, lines):
        """
        Returns the indentation level of a given line.

        Args:
            posx (int): The index of the line.
            lines (list): The list of lines in the raw configuration.

        Returns:
            int: The number of spaces before the line content.
        """
        indent = len(re.search(r'^\s*', lines[posx]).group())
        logger.debug(f"Indentation for line {posx}: {indent}")
        return indent

    def get_body(self, posx, lines):
        """
        Returns the body of a block of lines with the same indentation level.

        Args:
            posx (int): The starting index of the block.
            lines (list): The list of lines in the raw configuration.

        Returns:
            list: A list of lines representing the body of the block.
        """
        indent = self.get_indent(posx, lines)
        body = []
        for line_idx in range(posx, len(lines)):
            curr_indent = self.get_indent(line_idx, lines)
            if curr_indent < indent:
                break
            body.append(lines[line_idx])
        logger.debug(f"Body starting from line {posx}: {body}")
        return body

    def query(self, regex, lines=None):
        """
        Queries the parsed configuration for lines or blocks matching the regex.

        Args:
            regex (str): The regex pattern to search for.
            lines (list, optional): The lines to search through. If None, searches the entire config.

        Returns:
            list: A list of matching items.
        """
        lines = lines if lines else self.config
        result = []

        for item in lines:
            if isinstance(item, dict):
                key = next(iter(item))
                if re.search(regex, key):
                    result.append(item)
                _result = self.query(regex, item[key])
                if _result:
                    result.append({key: _result})
            else:
                if re.search(regex, item):
                    result.append(item)

        logger.info(f"Query results for regex '{regex}': {result}")
        return result
