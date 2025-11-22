from pyxlsb import open_workbook
import pandas as pd

xlsb_path = "dvd_2025_01.xlsb"

with open_workbook(xlsb_path) as wb:
    with wb.get_sheet(1) as sheet:  # 你也可以用 sheet 名称
        data = [[item.v for item in row] for row in sheet.rows()]
        df = pd.DataFrame(data[1:], columns=data[0])  # 第一行作为表头

df.to_excel("converted.xlsx", index=False)
