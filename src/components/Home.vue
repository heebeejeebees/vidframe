<template>
  <div id="wrapper">
    <Dashboard />
    <UploadFile />
  </div>
</template>

<script>
import Dashboard from './Dashboard.vue';
import UploadFile from './UploadFile.vue';
export default {

  components: {
    Dashboard,
    UploadFile
  },
}
</script>

<style scoped>
#wrapper {
  display: flex;
  flex: 1;
}

/* Landscape mode: children are side by side if width is greater than height */
@media (min-aspect-ratio: 1/1) {
  #wrapper {
    flex-direction: row;
  }
}

/* Portrait mode: children are one atop another if height is greater than width */
@media (max-aspect-ratio: 1/1) {
  #wrapper {
    flex-direction: column;
  }
}
</style>