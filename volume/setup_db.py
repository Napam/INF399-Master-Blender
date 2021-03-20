import pathlib
from typing import Callable, Optional, Tuple
import config as cng
import sqlite3 as db
import os

GEN_DIR = pathlib.Path(cng.GENERATED_DATA_DIR)
LABELCHECK_DIR = pathlib.Path(cng.LABELCHECK_DATA_DIR)

class DatabaseMaker:
    """
    Used for setting up sqlite3 database for generated data
    """

    def __init__(self, file: str):
        """
        Connects to .db file on initialization, creates one if not existing
        """
        # This makes the .db file if not existing
        self.con: db.Connection = db.connect(file)
        self.cursor: db.Cursor = self.con.cursor()
        self.table_create_funcs: Tuple[Callable] = (
            self.create_bboxes_cps_table,
            self.create_bboxes_xyz_table,
            self.create_bboxes_std_table,
            self.create_bboxes_full_table,
        )

    def __del__(self):
        self.close()

    def close(self) -> None:
        print("Closing database connection for DatabaseMaker")
        self.con.close()

    def create_bboxes_cps_table(self) -> None:
        """
        Creating tables does not require commiting.
        sqlite3 will raise error if table already exists
        """
        self.cursor.execute(
            f"""
            CREATE TABLE {cng.BBOX_DB_TABLE_CPS} (
                {cng.BBOX_DB_IMGRNR} INTEGER NOT NULL,
                {cng.BBOX_DB_CLASS} INTEGER NOT NULL,
                p1_x REAL NOT NULL,
                p1_y REAL NOT NULL,
                p1_z REAL NOT NULL,
                p2_x REAL NOT NULL,
                p2_y REAL NOT NULL,
                p2_z REAL NOT NULL,
                p3_x REAL NOT NULL,
                p3_y REAL NOT NULL,
                p3_z REAL NOT NULL,
                p4_x REAL NOT NULL,
                p4_y REAL NOT NULL,
                p4_z REAL NOT NULL,
                p5_x REAL NOT NULL,
                p5_y REAL NOT NULL,
                p5_z REAL NOT NULL,
                p6_x REAL NOT NULL,
                p6_y REAL NOT NULL,
                p6_z REAL NOT NULL,
                p7_x REAL NOT NULL,
                p7_y REAL NOT NULL,
                p7_z REAL NOT NULL,
                p8_x REAL NOT NULL,
                p8_y REAL NOT NULL,
                p8_z REAL NOT NULL
            )
        """
        )

    def create_bboxes_xyz_table(self) -> None:
        """
        Creating tables does not require commiting.
        sqlite3 will raise error if table already exists
        """
        self.cursor.execute(
            f"""
            CREATE TABLE {cng.BBOX_DB_TABLE_XYZ} (
                {cng.BBOX_DB_IMGRNR} INTEGER NOT NULL,
                {cng.BBOX_DB_CLASS} INTEGER NOT NULL,
                x REAL NOT NULL,
                y REAL NOT NULL,
                z REAL NOT NULL
            )
        """
        )

    def create_bboxes_std_table(self) -> None:
        """
        Creating tables does not require commiting.
        sqlite3 will raise error if table already exists
        """
        self.cursor.execute(
            f"""
            CREATE TABLE {cng.BBOX_DB_TABLE_STD} (
                {cng.BBOX_DB_IMGRNR} INTEGER NOT NULL,
                {cng.BBOX_DB_CLASS} INTEGER NOT NULL,
                x REAL NOT NULL,
                y REAL NOT NULL,
                w REAL NOT NULL,
                h REAL NOT NULL
            )
        """
        )

    def create_bboxes_full_table(self) -> None:
        """
        Creating tables does not require commiting.
        sqlite3 will raise error if table already exists
        """
        self.cursor.execute(
            f"""
            CREATE TABLE {cng.BBOX_DB_TABLE_FULL} (
                {cng.BBOX_DB_IMGRNR} INTEGER NOT NULL,
                {cng.BBOX_DB_CLASS} INTEGER NOT NULL,
                x REAL NOT NULL,
                y REAL NOT NULL,
                z REAL NOT NULL,
                w REAL NOT NULL,
                l REAL NOT NULL,
                h REAL NOT NULL,
                rx REAL NOT NULL,
                ry REAL NOT NULL,
                rz REAL NOT NULL
            )
        """
        )
    
    def create_labelcheck_table(self) -> None:
        """
        Creating tables does not require commiting.
        sqlite3 will raise error if table already exists

        This is not supposed to be included in self.table_create_funcs
        """
        self.cursor.execute(
            f"""
            CREATE TABLE {cng.LABELCHECK_DB_TABLE} (
                {cng.LABELCHECK_DB_IMGNR} INTEGER NOT NULL PRIMARY KEY
            )
        """
        )



if __name__ == "__main__":
    # Create folder if not exist
    # pathlib.Path(dirpath / cng.GENERATED_DATA_DIR).mkdir(parents=True, exist_ok=True)
    db_ = DatabaseMaker()
    # db_.create_bboxes_cps_table()
    # db_.create_bboxes_xyz_table()
    # db_.create_bboxes_std_table()
    pass
