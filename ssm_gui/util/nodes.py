import os

import numpy as np
import pandas as pd


class NodeListUtl:
    @staticmethod
    def load_node_ids(filepath):
        """
        Load a list of VTK point/node ids from a .txt or .csv file.
        Accepts one id per line, or ids separated by commas/whitespace across lines,
        with or without a header row - non-numeric tokens are ignored.
        :param filepath: path to the .txt or .csv file
        :return: sorted list of unique non-negative integer node ids
        """
        ext = os.path.splitext(filepath)[1].lower()
        raw_values = []
        if ext == '.csv':
            df = pd.read_csv(filepath, header=None)
            raw_values = df.to_numpy().flatten().tolist()
        else:
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.split('#')[0].strip()
                    if not line:
                        continue
                    raw_values.extend(line.replace(',', ' ').split())

        ids = set()
        for v in raw_values:
            if v is None:
                continue
            try:
                if isinstance(v, float) and np.isnan(v):
                    continue
                iv = int(float(v))
            except (ValueError, TypeError):
                continue
            if iv >= 0:
                ids.add(iv)
        return sorted(ids)

    @staticmethod
    def save_node_coordinates(filepath, node_ids, points):
        """
        Write node ids and their x, y, z coordinates to a .csv or .txt file.
        :param filepath: destination path
        :param node_ids: sequence of node ids, aligned with rows in points
        :param points: Nx3 array of coordinates
        """
        df = pd.DataFrame({'node_id': node_ids, 'x': points[:, 0], 'y': points[:, 1], 'z': points[:, 2]})
        sep = ' ' if os.path.splitext(filepath)[1].lower() == '.txt' else ','
        df.to_csv(filepath, index=False, sep=sep)
