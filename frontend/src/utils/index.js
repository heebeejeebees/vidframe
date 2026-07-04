export function customErrorMessage(title, message) {
  utilArea.style.display = "flex";
  utilTitle.textContent = title;
  utilMsg.textContent = message;
  utilBtn.style.display = "none";
}

/**
 * convert microsecond timestamp of VideoFrame to timestamp string
 */
export function transformMicrosecondsToTimestamp(microseconds) {
  if (microseconds <= 0) {
    return "00:00.000000";
  }

  const totalSeconds = Math.floor(microseconds / 1000000);
  const remainingMicroseconds = microseconds % 1000000;

  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;

  // Format with leading zeros
  const formattedMinutes = String(minutes).padStart(2, "0");
  const formattedSeconds = String(seconds).padStart(2, "0");
  const formattedMicroseconds = String(remainingMicroseconds).padStart(6, "0");

  return `${formattedMinutes}:${formattedSeconds}.${formattedMicroseconds}`;
}

/**
 * draw bitmap to canvas
 * @param {HTMLCanvasElement | OffscreenCanvas} canvas to be drawn on
 * @param {OffscreenCanvasRenderingContext2D} ctx to be drawn on
 * @param {ImageBitmap} bitmap of image
 */
export function canvasDrawImage(canvas, ctx, bitmap) {
  canvas.width = bitmap.width;
  canvas.height = bitmap.height;
  ctx.drawImage(bitmap, 0, 0);
}

/**
 * to calculate laplacian variance per video frame from OffscreenCanvas
 * https://stackoverflow.com/a/72288032
 * @returns laplacian variance float, higher = clearer
 */
export function getLaplacianVar(offscreenCanvas) {
  /* opencv starts */
  try {
    // get image
    const cvImage = cv.imread(offscreenCanvas);

    // convert to gray scale
    const grayImage = new cv.Mat();
    cv.cvtColor(cvImage, grayImage, cv.COLOR_RGBA2GRAY);
    cvImage.delete();

    // TODO let user choose accuracy on RAM expense
    // CV_8S  : low
    // CV_16S : mid
    // CV_32F : high
    // CV_64F : extra high
    const CV_TYPE = cv.CV_64F;

    // calculate laplacian
    const laplacianMat = new cv.Mat();
    cv.Laplacian(grayImage, laplacianMat, CV_TYPE);
    grayImage.delete();

    // calculate standard deviation
    const standardDeviationMat = new cv.Mat(1, 4, CV_TYPE);
    cv.meanStdDev(
      laplacianMat,
      standardDeviationMat.clone(),
      standardDeviationMat
    );
    laplacianMat.delete();

    // calculate variance
    const standardDeviation = standardDeviationMat.doubleAt(0, 0);
    standardDeviationMat.delete();
    return standardDeviation * standardDeviation;
  } catch (e) {
    if (typeof e === "number") {
      throw new Error(
        "Video processing failed, try trimming, converting, or resize your video"
      );
    }
  }
}
