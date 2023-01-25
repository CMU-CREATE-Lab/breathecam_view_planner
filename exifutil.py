import glob, json, math, subprocess

def read_exif(filename: str):
    js = subprocess.check_output(["exiftool", "-G", "-s", "-b", "-j", "-a", "-T", filename], encoding="utf-8")
    return json.loads(js)[0]

def get_first_key(dct, *keys):
    for key in keys:
        if key in dct:
            return dct[key]
    raise f"Could not find any of keys {keys}"

class FovInfo:
    def __init__(self, filename: str):
        try:
            exif = read_exif(filename)

            self.fl_35mm_mm: float = float(exif["EXIF:FocalLengthIn35mmFormat"]["val"].split()[0])
            self.image_width_px: int = exif["File:ImageWidth"]["val"]
            self.image_height_px: int = exif["File:ImageHeight"]["val"]

            self.camera_model = get_first_key(exif, "EXIF:UniqueCameraModel", "EXIF:Model")["val"]

            print(f"Camera model {self.camera_model}")
            print(f"Image size {self.image_width_px}x{self.image_height_px}")
            pano_models = ["Insta360 ONE X2"]

            if "XMP:ProjectionType" in exif:
                print("Using Gpano metadata")
                assert(exif["XMP:ProjectionType"]["val"] == "equirectangular")
                self.image_full_width = exif["XMP:FullPanoWidthPixels"]["val"]
                self.image_full_height = exif["XMP:FullPanoHeightPixels"]["val"]
                assert(self.image_width_px == exif["XMP:CroppedAreaImageWidthPixels"]["val"])
                assert(self.image_height_px == exif["XMP:CroppedAreaImageHeightPixels"]["val"])
                self.hfov_deg = 360 * self.image_width_px / self.image_full_width
                self.vfov_deg = 180 * self.image_height_px / self.image_full_height
            elif self.camera_model in pano_models and self.image_width_px == self.image_height_px * 2:
                print(f"No Gpano, but camera model {self.camera_model} in pano_models and width == 2*height; assuming 360x180")
                self.hfov_deg = 360
                self.vfov_deg = 180
                self.image_full_width = self.image_width_px
                self.image_full_height = self.image_height_px
            else:
                print("Looks like a standard non-panoramic image")
                if self.image_width_px == self.image_height_px * 2:
                    print(f"WARNING: width = 2*height;  do we need to add camera model to pano_models in exifutil.py?")
                sensor_diag_35mm_mm = math.hypot(36,24)
                self.diag_fov_35mm_deg: float = self._fov_deg(focal_length = self.fl_35mm_mm, sensor_length = sensor_diag_35mm_mm)
                print(f"Computed diagonal fov: {self.diag_fov_35mm_deg:.3f} deg")

                focal_length = float(exif["EXIF:FocalLength"]["val"].split()[0])

                image_diag_px = math.hypot(self.image_width_px, self.image_height_px)
                px_size_35mm_um = sensor_diag_35mm_mm / image_diag_px * 1000
                self.px_size_ccd_um: float = px_size_35mm_um * focal_length / self.fl_35mm_mm
                image_width_35mm_mm = px_size_35mm_um * self.image_width_px / 1000
                image_height_35mm_mm = px_size_35mm_um * self.image_height_px / 1000
                self.image_width_ccd_mm: float = self.px_size_ccd_um * self.image_width_px / 1000
                self.image_height_ccd_mm: float = self.px_size_ccd_um * self.image_height_px / 1000

                print(f"Computed CCD size {self.image_width_ccd_mm:.3f} mm x {self.image_height_ccd_mm:.3f} mm, with pixel size {self.px_size_ccd_um:.3f} um")

                self.hfov_deg: float = self._fov_deg(focal_length = self.fl_35mm_mm, sensor_length = image_width_35mm_mm)
                self.vfov_deg: float = self._fov_deg(focal_length = self.fl_35mm_mm, sensor_length = image_height_35mm_mm)
                print(f"Computed fields of view: HFOV = {self.hfov_deg:.3f} deg, VFOV = {self.vfov_deg:.3f}")
        except KeyError:
            print(exif)
            raise

    @staticmethod
    def _fov_deg(focal_length: float, sensor_length: float) -> float:
        return 2 * math.degrees(math.atan2(sensor_length / 2, focal_length))
    
    def __repr__(self) -> str:
        return str(self.__dict__)

# def exif_summary(image: exif.Image):
#     fov_info = FovInfo(image)
#     return f"{image.make} {image.model} {fov_info.hfov_deg:.2f}°x{fov_info.vfov_deg:.2f}° {fov_info.image_width_px*fov_info.image_height_px/1e6:.1f}Mpix"
        