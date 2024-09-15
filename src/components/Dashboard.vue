<template>
  <div id="container">
    <img id="banner" src="../../public/vidfra.me.jpg" />
    <h3>What does it do?</h3>
    -
    <!-- to be moved-->
    <label for="metric">Choose an image metric to calculate per video frame:</label>
    <select name="metric" id="metric">
      <option value="laplacian_variance">Laplacian Variance</option>
    </select>
    <h3>Browser Compatibility</h3>
    <p>Only "Chromium" browsers are <a href="https://caniuse.com/webcodecs">compatible</a>
      for encoding and decoding of audio, video, and images.</p>
    <h3>Future Enhancements</h3>
    <h3>Feedback?</h3>
    <h3>Advertisements</h3>
    <h3>Ko-fi</h3>
  </div>
</template>

<script>
export default {
  name: 'Dashboard'
}
</script>

<style scoped>
#container {
  flex: 1;
  display: flex;
  justify-content: top;
  align-items: center;
  background: var(--background-color);
  flex-direction: column;
}

#banner {
  margin: 5%;
  height: 200px;
  max-width: 100%;
  object-fit: cover;
}
</style>