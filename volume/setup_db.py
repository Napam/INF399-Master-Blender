import pathlib
import blender_config as cng
import sqlite3 as db
import os

# import bpy

GEN_DIR = pathlib.Path(cng.GENERATED_DATA_DIR)
# dir_ = os.path.dirname(bpy.data.filepath)
# dirpath = pathlib.Path(dir_)


class DatabaseMaker:
    """
    Used for setting up sqlite3 database
    """

    def __init__(self):
        """
        Connects to .db file on initialization, creates one if not existing
        """
        # This makes the .db file if not existing
        self.con = db.connect(os.path.join(cng.GENERATED_DATA_DIR, cng.BBOX_DB_FILE))
        self.cursor = self.con.cursor()
        self.table_create_funcs = (
            self.create_bboxes_cps_table,
            self.create_bboxes_xyz_table,
            self.create_bboxes_std_table
        )

    def __del__(self):
        self.close()

    def close(self) -> None:
        print("Closing database connection")
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
                p1_x FLOAT(3) NOT NULL,
                p1_y FLOAT(3) NOT NULL,
                p1_z FLOAT(3) NOT NULL,
                p2_x FLOAT(3) NOT NULL,
                p2_y FLOAT(3) NOT NULL,
                p2_z FLOAT(3) NOT NULL,
                p3_x FLOAT(3) NOT NULL,
                p3_y FLOAT(3) NOT NULL,
                p3_z FLOAT(3) NOT NULL,
                p4_x FLOAT(3) NOT NULL,
                p4_y FLOAT(3) NOT NULL,
                p4_z FLOAT(3) NOT NULL,
                p5_x FLOAT(3) NOT NULL,
                p5_y FLOAT(3) NOT NULL,
                p5_z FLOAT(3) NOT NULL,
                p6_x FLOAT(3) NOT NULL,
                p6_y FLOAT(3) NOT NULL,
                p6_z FLOAT(3) NOT NULL,
                p7_x FLOAT(3) NOT NULL,
                p7_y FLOAT(3) NOT NULL,
                p7_z FLOAT(3) NOT NULL,
                p8_x FLOAT(3) NOT NULL,
                p8_y FLOAT(3) NOT NULL,
                p8_z FLOAT(3) NOT NULL
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
                x FLOAT(4) NOT NULL,
                y FLOAT(4) NOT NULL,
                z FLOAT(4) NOT NULL
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
                x FLOAT(4) NOT NULL,
                y FLOAT(4) NOT NULL,
                w FLOAT(4) NOT NULL,
                h FLOAT(4) NOT NULL
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
