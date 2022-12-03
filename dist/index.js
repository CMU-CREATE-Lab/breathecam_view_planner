//import { Viewer } from 'photo-sphere-viewer';
//import * as foo from "../dist/photo-sphere-viewer-4.8.0/photo-sphere-viewer.js"
//console.log(foo)
//import { Viewer } from "photo-sphere-viewer"
function requireElementIdType(id, constructor) {
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
function awaitButtonClick(button) {
    return new Promise(function (resolve, reject) {
        var listener = (event) => {
            button.removeEventListener("click", listener);
            resolve(event);
        };
        button.addEventListener("click", listener);
    });
}
// Wait for first button of buttons to be clicked, and return that button
async function awaitFirstButtonClick(buttons) {
    return (await Promise.race(buttons.map(awaitButtonClick))).target;
}
function readFileAsDataUrlAsync(file) {
    return new Promise((resolve, reject) => {
        let reader = new FileReader();
        reader.onload = () => {
            resolve(reader.result);
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}
var barf2;
async function upload() {
    var uploadDialog = requireElementIdType("uploadDialog", HTMLDivElement);
    // Abort if the dialog is already up
    if (uploadDialog.style.visibility == "visible")
        return;
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
            if (clickedButton == cancelButton)
                break;
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
            var mimeType = uri.split(",")[0].split(":")[1].split(";")[0];
            console.log(`mimeType ${mimeType}`);
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
                alert("Panorama uploaded successfully");
                return;
            }
            else {
                alert(`Panorama not uploaded: ${JSON.stringify(response)}`);
            }
        }
    }
    finally {
        uploadDialog.style.visibility = "hidden";
    }
}
export function init(panorama) {
    requireElementIdType("upload", HTMLButtonElement).addEventListener("click", upload);
    console.log("the pano is", panorama);
    if (panorama) {
        // @ts-ignore
        const viewer = new PhotoSphereViewer.Viewer({
            container: 'panoviewer',
            panorama: panorama.image_url
        });
        // var viewer = new Viewer({
        //     container: requireElementIdType("panoviewer", HTMLDivElement),
        //     panorama: panorama.image_url
        // })
        // // @ts-ignore
        // globalThis.viewer = viewer;
        //     panorama: 'path/to/panorama.jpg',
        //   });
    }
}
// @ts-ignore
globalThis.index_ts_init = init;
//# sourceMappingURL=index.js.map