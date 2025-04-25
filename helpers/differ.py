import logging
import textdistance
from .parser import ConfigParser

class ConfigDiffer:
    """
    Compares two configuration datasets and highlights differences using fuzzy matching.

    Attributes:
        src (list): Source configuration data.
        dest (list): Destination configuration data.
        diff (dict): Dictionary containing the diff results.
    """

    def __init__(self, src, dest, diff_only=False):
        """
        Initialize the ConfigDiffer with source and destination data.

        Args:
            src (list): Source configuration data.
            dest (list): Destination configuration data.
            diff_only (bool): If True, perform diff-only comparison.
        """
        logging.info("Initializing ConfigDiffer...")
        self.src = src
        self.dest = dest
        self.src_parser = ConfigParser(self.src)
        self.dest_parser = ConfigParser(self.dest)
        self.diff = {}
        self.find_diff_only() if diff_only else self.find_diff()

    def sort_config(self, config_list):
        """
        Separates strings and dictionaries from the config list.

        Args:
            config_list (list): List of config lines or sections.

        Returns:
            tuple: (list of strings, dict of dicts)
        """
        strings = []
        dicts = {}
        for item in config_list:
            if isinstance(item, str):
                strings.append(item)
            elif isinstance(item, dict):
                dicts[next(iter(item))] = item[next(iter(item))]
        return strings, dicts

    def get_best_match(self, query, lines):
        """
        Finds the best fuzzy match for the given query in a list of lines.

        Args:
            query (str): The string to match.
            lines (list): List of candidate strings.

        Returns:
            tuple: (similarity score, best match, longest common subsequence)
        """
        best_match = max(lines, key=lambda line: textdistance.ratcliff_obershelp(query, line), default='')
        best_score = textdistance.ratcliff_obershelp(query, best_match)
        lcs_match = textdistance.lcsseq(query, best_match)
        return best_score, best_match, lcs_match

    def format_string_match(self, string, lcs_match):
        """
        Formats a string to highlight matched characters using tags.

        Args:
            string (str): The string to format.
            lcs_match (str): Longest common subsequence for comparison.

        Returns:
            list: A list containing tags and characters.
        """
        formatted = []
        lcs_index = 0
        for char in string:
            if lcs_index < len(lcs_match) and char == lcs_match[lcs_index]:
                formatted.extend(['ftmatch', char])
                lcs_index += 1
            else:
                formatted.extend(['ftdiff', char])
        return formatted

    def write(self, worksheet, header, ft_header, ft_body, ft_bad, ft_badb,
              format_strings=None, row_idx=0, col_idx=0, col_width=60):
        """
        Writes the formatted differences to an Excel worksheet.

        Args:
            worksheet (xlsxwriter.Workbook): The worksheet to write to.
            header (str): Header text.
            ft_header: Header formatting.
            ft_body: Match formatting.
            ft_bad: Diff formatting.
            ft_badb: Highlight formatting.
            format_strings (dict): Formatted diff dictionary.
            row_idx (int): Starting row.
            col_idx (int): Starting column.
            col_width (int): Column width.
        """
        format_strings = format_strings or self.diff
        worksheet.set_column(col_idx, col_idx, col_width)
        worksheet.write_string(row_idx, col_idx, header, ft_header)
        row_idx += 1
        for idx, segment in format_strings.items():
            segment = [ft_body if item == 'ftmatch' else item for item in segment]
            segment = [ft_bad if item == 'ftdiff' else item for item in segment]
            segment = [ft_badb if item == 'ftdiffb' else item for item in segment]
            if ft_bad in segment and ft_badb in segment:
                worksheet.write_rich_string(row_idx, col_idx, *segment)
            else:
                worksheet.write_string(row_idx, col_idx, *segment)
            row_idx += 1

    def find_diff(self):
        """
        Performs a full diff including unchanged, partially matched, and unmatched entries.
        """
        logging.info("Performing full diff...")
        self.diff, _ = self._find_diff(self.src_parser.config, self.dest_parser.config)

    def _find_diff(self, src_list, dest_list, diff=None, idx=0):
        src_strings, src_dicts = self.sort_config(src_list)
        diff = diff or {}
        for obj in dest_list:
            idx += 1
            diff[idx] = {}
            if isinstance(obj, str):
                score, match, lcs = self.get_best_match(obj, src_strings)
                if score == 1 or obj.strip() == lcs.strip():
                    diff[idx] = [obj, 'ftmatch']
                elif lcs and score > 0.5:
                    diff[idx] = self.format_string_match(obj, lcs) + ['ftdiffb']
                else:
                    diff[idx] = [obj, 'ftdiff']
            elif isinstance(obj, dict):
                key = next(iter(obj))
                value = obj[key]
                score, match, lcs = self.get_best_match(key, src_dicts.keys())
                src_sublist = src_dicts[match]
                if score == 1 or key.strip() == lcs.strip():
                    diff[idx] = [key, 'ftmatch']
                elif lcs and score > 0.99:
                    diff[idx] = self.format_string_match(key, lcs) + ['ftdiffb']
                else:
                    diff[idx] = [key, 'ftdiff']
                    src_sublist = []
                diff, idx = self._find_diff(src_sublist, value, diff, idx)
        return diff, idx

    def find_diff_only(self):
        """
        Performs a diff that includes only differing entries.
        """
        logging.info("Performing diff-only comparison...")
        self.diff, *_ = self._find_diff_only(self.src_parser.config, self.dest_parser.config)

    def _find_diff_only(self, src_list, dest_list, scores=None, keys=None, diff=None,
                        idx=0, exclam_flag=False):
        src_strings, src_dicts = self.sort_config(src_list)
        scores = scores or []
        keys = keys or []
        diff = diff or {}
        values = []
        for obj in dest_list:
            idx += 1
            if isinstance(obj, str):
                if not obj or obj == '!':
                    if not exclam_flag:
                        diff[idx] = ['!', 'ftmatch']
                        exclam_flag = True
                        continue
                score, match, lcs = self.get_best_match(obj, src_strings)
                scores.append(score)
                if score == 1 or obj.strip() == lcs.strip():
                    continue
                format_type = 'ftdiffb' if lcs and score > 0.5 else 'ftdiff'
                formatted = self.format_string_match(obj, lcs) + [format_type] if format_type == 'ftdiffb' else [obj, format_type]
                exclam_flag = False
                if keys:
                    values.append(formatted)
                else:
                    diff[idx] = formatted
            else:
                key = next(iter(obj))
                value = obj[key]
                score, match, lcs = self.get_best_match(key, src_dicts.keys())
                scores.append(score)
                src_sublist = src_dicts[match]
                if score == 1 or key.strip() == lcs.strip():
                    keys.append([key, 'ftmatch'])
                elif lcs and score > 0.99:
                    keys.append(self.format_string_match(key, lcs) + ['ftdiffb'])
                else:
                    keys.append([key, 'ftdiff'])
                    src_sublist = []
                diff, idx, keys, scores, exclam_flag = self._find_diff_only(
                    src_sublist, value, scores, keys, diff, idx, exclam_flag
                )
        if values:
            for item in keys + values:
                idx += 1
                diff[idx] = item
        return diff, idx, [], scores, exclam_flag
