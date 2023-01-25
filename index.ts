// We are including photo-sphere-viewer.js from index.html.  Declare the global it defines
import { Viewer } from "dist/photo-sphere-viewer-4.8.0/photo-sphere-viewer.d";
declare global {
    var PhotoSphereViewer: { Viewer: typeof Viewer};
}

type UserExport = {
    id: string,
    name: string,
    email: string
};

type PanoramaExport = {
    id: number,
    name: string,
    viewport_lat: number,
    viewport_long: number,
    viewport_name: number,
    image_full_width: number,
    image_full_height: number,
    image_cropped_width: number,
    image_cropped_height: number,
    image_cropped_x: number,
    image_cropped_y: number,
    user: UserExport,
    url: string,
    image_url: string
};

function requireElementIdType<EltType extends HTMLElement>(id: string, constructor:{new():EltType}): EltType {
    var elt = document.getElementById(id);
    if (!elt) {
        throw Error(`Required dom element id=${id} not found`);
    }
    if (!(elt instanceof constructor)) {
        throw Error(`Dom element id=${id} required to be of type ${constructor.name} but is ${elt.constructor.name}`);
    }
    return elt;
}

// Wait for button to be clicked, and return the MouseEvent
function awaitButtonClick(button: HTMLButtonElement): Promise<MouseEvent> {
    return new Promise(function (resolve, reject) {
        var listener = (event: MouseEvent) => {
            button.removeEventListener("click", listener);
            resolve(event);
        };
        button.addEventListener("click", listener);
    });
}

// Wait for first button of buttons to be clicked, and return that button
async function awaitFirstButtonClick(buttons: HTMLButtonElement[]): Promise<HTMLButtonElement> {
   return (await Promise.race(buttons.map(awaitButtonClick))).target as HTMLButtonElement;
}

function readFileAsDataUrlAsync(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      let reader = new FileReader();
  
      reader.onload = () => {
        resolve(reader.result as string);
      };
  
      reader.onerror = reject;
  
      reader.readAsDataURL(file);
    })
  }

  var barf2;

  async function upload() {
    var uploadDialog = requireElementIdType("uploadDialog", HTMLDivElement);

    // Abort if the dialog is already up
    if (uploadDialog.style.visibility == "visible") return;

    uploadDialog.style.visibility = "visible";
    var fileInput = requireElementIdType("panoramaFile", HTMLInputElement);
    var nameInput = requireElementIdType("uploadPanoramaName", HTMLInputElement);
    var cancelButton = requireElementIdType("uploadCancelButton", HTMLButtonElement);
    var uploadButton = requireElementIdType("uploadUploadButton", HTMLButtonElement);
    fileInput.value = "";
    nameInput.value = "";

    try {
        while (1) {
            var clickedButton = await awaitFirstButtonClick([cancelButton, uploadButton]);
            if (clickedButton == cancelButton) break;
            var minNameLen = 4;
            var name = nameInput.value.trim();
            if (!name || name.length < minNameLen) {
                alert(`Name must be at least ${minNameLen} characters long`);
            }

            console.log(fileInput);
            var file = fileInput.files[0];
            if (!file) {
                alert("Please select a panorama file to upload");
                continue;
            }
            var uri = await readFileAsDataUrlAsync(file);
            var base64content = uri.split(",")[1];
            var mimeType = uri.split(",")[0].split(":")[1].split(";")[0]
            console.log(`mimeType ${mimeType}`)

            if (!base64content || !mimeType) {
                alert("Could not read your panorama file");
                continue;
            }
            var upload = {
                name: name,
                image: base64content,
                mimeType: mimeType
            };
            console.log(upload);
            var response = await (await fetch("/upload", {
                method: "POST",
                body: JSON.stringify(upload),
                headers: {
                "Content-Type": "application/json"
                }
            })).json();

            console.log(response);
            if (response && response["success"] == true) {
                alert(`Panorama uploaded successfully ${response} ${JSON.stringify(response)}`);
                console.log("after alert!");
                window.location.replace(response.panorama.url);
                return;
            } else {
                alert(`Panorama not uploaded: ${JSON.stringify(response)}`);
            }
        } 
    } finally {
        uploadDialog.style.visibility = "hidden";
    }
}

class FovDef {
    Name: string;
    Cam: string;
    fl_mm: number;
    overlap_px: number;
    Cols: number;
    Rows: number;
    eff_x_px: number;
    eff_y_px: number;
    hfov_deg: number;
    vfov_deg: number;
    Notes: string;
    info: string;
};

var mPanorama : PanoramaExport | null;

async function deletePanorama(): Promise<null> {
    let ret = confirm("Deleting panorama cannot be undone.  Are you sure you want to delete this panorama?");
    if (!ret) return;
    var payload = {
        pano_id: mPanorama.id
    };
    console.log("deletePanorama", payload);
    var response = await (await fetch("/delete", {
        method: "POST",
        body: JSON.stringify(payload),
        headers: {
            "Content-Type": "application/json"
        }
    })).json();

    console.log(response);
    if (response && response["success"] == true) {
        window.location.replace("/");
        return;
    } else {
        alert(`Panorama not uploaded: ${JSON.stringify(response)}`);
    }

    return null;
}

export function init(panorama : PanoramaExport | null, fovs: FovDef[]) {
    mPanorama = panorama;
    console.log(fovs);
    requireElementIdType("upload", HTMLButtonElement).addEventListener("click", upload);
    console.log("panorama:", panorama);
    let panoData = {
        fullWidth: panorama.image_full_width,
        fullHeight: panorama.image_full_height,
        croppedWidth: panorama.image_cropped_width,
        croppedHeight: panorama.image_cropped_height,
        croppedX: panorama.image_cropped_x,
        croppedY: panorama.image_cropped_y
    };
    console.log("panoData:", panoData);

    if (panorama) {
        const viewer = new PhotoSphereViewer.Viewer({
            container: 'panoviewer',
            panorama: panorama.image_url,
            panoData: panoData
        });
        requireElementIdType("panoname", HTMLSpanElement).innerText = `${panorama.name} (id ${panorama.id})`;
        let deleteButton = requireElementIdType("delete", HTMLButtonElement);
        deleteButton.addEventListener("click", deletePanorama);
        deleteButton.style.display = "inline";
    }
}



