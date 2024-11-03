
document.addEventListener("DOMContentLoaded", function() {
    var osmdContainer = document.getElementById("osmd-container");
    var osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay(osmdContainer, {
        backend: "svg",
        drawTitle: true,
        pageFormat: "A4 P",
        newSystemFromXML: true,
        newPageFromXML: true,
        drawingParameters: "all",
        autoResize: false,
    });
    

    osmd.load(scoreFileUrl).then(function() {
        osmd.render();
        
        const numberOfPages = osmd.GraphicSheet.MusicPages.length;

        for (let i = 0; i < numberOfPages; i++) {
            let pageDiv = document.createElement("div");
            pageDiv.className = "osmd-page"; // Применяем класс для страницы
            pageDiv.id = "osmd-page-" + (i + 1);
            osmdContainer.appendChild(pageDiv);

            let svgElement = document.getElementById("osmdCanvasPage" + (i + 1));
            if (svgElement) {
                pageDiv.appendChild(svgElement);
            }
        }
    }).catch(function(error) {
        console.error("Ошибка при загрузке файла партитуры: ", error);
    });
});