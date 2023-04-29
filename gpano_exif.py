import glob, json, math, subprocess

def read_exif(filename: str):
    js = subprocess.check_output(["exiftool", "-G", "-s", "-b", "-j", "-a", "-T", filename], encoding="utf-8")
    return json.loads(js)[0]

def get_first_key(dct, *keys):
    for key in keys:
        if key in dct:
            return dct[key]
    raise Exception(f"Could not find any of keys {keys}")

class GPanoInfo:
    def __init__(self, filename: str):
        exif = read_exif(filename)
        try:
            self.image_cropped_width: int = exif["File:ImageWidth"]["val"]
            self.image_cropped_height: int = exif["File:ImageHeight"]["val"]

            camera_model = get_first_key(exif, "EXIF:UniqueCameraModel", "EXIF:Model")["val"]

            print(f"Camera model {camera_model}")
            print(f"Image size {self.image_cropped_width}x{self.image_cropped_height}")
            pano_models = ["Insta360 ONE X2"]

            if "XMP:ProjectionType" in exif:
                print("Using Gpano metadata")
                assert(exif["XMP:ProjectionType"]["val"] == "equirectangular")
                self.image_full_width: float = exif["XMP:FullPanoWidthPixels"]["val"]
                self.image_full_height: float = exif["XMP:FullPanoHeightPixels"]["val"]
                assert(self.image_cropped_width == exif["XMP:CroppedAreaImageWidthPixels"]["val"])
                assert(self.image_cropped_height == exif["XMP:CroppedAreaImageHeightPixels"]["val"])
                self.image_cropped_x: float = exif["XMP:CroppedAreaLeftPixels"]["val"]
                self.image_cropped_y: float = exif["XMP:CroppedAreaTopPixels"]["val"]
            elif camera_model in pano_models and self.image_cropped_width == self.image_cropped_height * 2:
                print(f"No Gpano, but camera model {camera_model} in pano_models and width == 2*height; assuming 360x180")
                self.image_full_width = self.image_cropped_width
                self.image_full_height = self.image_cropped_height
                self.image_cropped_x = 0.0
                self.image_cropped_y = 0.0
            else:
                fl_35mm_mm: float = float(exif["EXIF:FocalLengthIn35mmFormat"]["val"].split()[0])
                print("Looks like a non-panoramic image")
                # THIS IS AN APPROXIMATION, USING IMAGE AS IF IT'S PROJECTED EQUIRECTANGULAR
                # The approximation works better for narrow FOV images and less well for wide-angle
                if self.image_cropped_width == self.image_cropped_height * 2:
                    print(f"WARNING: width = 2*height;  do we need to add camera model to pano_models in exifutil.py?")
                sensor_diag_35mm_mm = math.hypot(36,24)
                self.diag_fov_35mm_deg: float = self._fov_deg(focal_length = fl_35mm_mm, sensor_length = sensor_diag_35mm_mm)
                print(f"Computed diagonal fov: {self.diag_fov_35mm_deg:.3f} deg")

                focal_length = float(exif["EXIF:FocalLength"]["val"].split()[0])

                image_diag_px = math.hypot(self.image_cropped_width, self.image_cropped_height)
                px_size_35mm_um = sensor_diag_35mm_mm / image_diag_px * 1000
                px_size_ccd_um = px_size_35mm_um * focal_length / fl_35mm_mm
                image_width_35mm_mm = px_size_35mm_um * self.image_cropped_width / 1000
                image_height_35mm_mm = px_size_35mm_um * self.image_cropped_height / 1000
                image_width_ccd_mm = px_size_ccd_um * self.image_cropped_width / 1000
                image_height_ccd_mm = px_size_ccd_um * self.image_cropped_height / 1000

                print(f"Computed CCD size {image_width_ccd_mm:.3f} mm x {image_height_ccd_mm:.3f} mm, with pixel size {px_size_ccd_um:.3f} um")

                hfov_deg = self._fov_deg(focal_length = fl_35mm_mm, sensor_length = image_width_35mm_mm)
                vfov_deg = self._fov_deg(focal_length = fl_35mm_mm, sensor_length = image_height_35mm_mm)
                print(f"Computed fields of view: HFOV = {hfov_deg:.3f} deg, VFOV = {vfov_deg:.3f}")

                self.image_full_width: float = self.image_cropped_width * 360 / hfov_deg
                self.image_full_height: float = self.image_cropped_height * 180 / vfov_deg

                self.image_cropped_x: float = (self.image_full_width - self.image_cropped_width) / 2 # center horizontally
                self.image_cropped_y: float = (self.image_full_height - self.image_cropped_height) / 2 # center vertically

        except KeyError:
            print(exif)
            raise

    @staticmethod
    def _fov_deg(focal_length: float, sensor_length: float) -> float:
        return 2 * math.degrees(math.atan2(sensor_length / 2, focal_length))
    
    def __repr__(self) -> str:
        return str(self.__dict__)
    
    def as_dict(self):
        return self.__dict__

# def exif_summary(image: exif.Image):
#     fov_info = FovInfo(image)
#     return f"{image.make} {image.model} {fov_info.hfov_deg:.2f}°x{fov_info.vfov_deg:.2f}° {fov_info.image_width_px*fov_info.image_height_px/1e6:.1f}Mpix"
        