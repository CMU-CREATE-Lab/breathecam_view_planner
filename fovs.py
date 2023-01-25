from gsheet import GSheet
import pandas as pd

breathecam_field_of_views_google_sheet = "https://docs.google.com/spreadsheets/d/1qMLQ5kxYl8Y-hC1WeiLEzfPdcKy6rdpjBc-hGy55MuI/edit#gid=0"

def read_fovs():
    fovs_sheet = GSheet.from_url(breathecam_field_of_views_google_sheet)

    fovs_df = pd.read_csv(
                    fovs_sheet.get_csv_export_url(),
                    keep_default_na=False,
                    skip_blank_lines=False
                    #dtype={'Enabled':str,'Share link identifier':str, 'Start date':str, 'End date': str}
    )
    fovs_df = fovs_df[fovs_df.Name != ""]
    records = fovs_df.to_dict(orient="records")
    for record in records:
        info = (
            f"{record['hfov_deg']:.0f}°x{record['vfov_deg']:.0f}° "
            f"{record['Cam']} {record['fl_mm']} {record['Cols']}x{record['Rows']}")
        if record["Notes"]:
            info += f" ({record['Notes']})"
        record["info"] = info

    return records