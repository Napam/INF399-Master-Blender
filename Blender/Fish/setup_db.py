import pathlib
import blender_config as cng
import sqlite3 as db

GEN_DIR = pathlib.Path(cng.GENERATED_DATA_DIR)

class DatabaseMaker:
    """
    Used for setting up sqlite3 database
    """

    def __init__(self):
        # This makes the .db file if not existing
        self.con = db.connect(GEN_DIR / cng.BBOX_DB_FILE)
        self.cursor = self.con.cursor()

    def __del__(self):
        self.close()

    def close(self) -> None:
        print("Closed database connection")
        self.con.close()

    def create_bboxes_cps_table(self) -> None:
        """
        Creating tables does not require commiting.
        sqlite3 will raise error if table already exists
        """
        self.cursor.execute(
            f"""
            CREATE TABLE {cng.BBOX_DB_TABLE_CPS} (
                imgnr INTEGER NOT NULL,
                class_ INTEGER NOT NULL,
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
                imgnr INTEGER NOT NULL,
                class_ INTEGER NOT NULL,
                x FLOAT(4) NOT NULL,
                y FLOAT(4) NOT NULL,
                z FLOAT(4) NOT NULL
            )
        """
        )


if __name__ == "__main__":
    db_ = DatabaseMaker()
    db_.create_bboxes_cps_table()
    db_.create_bboxes_xyz_table()
