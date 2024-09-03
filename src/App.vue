<template>
  <div id="app" :style="cssProps">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css" />
    <RouterView />
  </div>
</template>

<script>
import UploadFile from './components/UploadFile.vue'

export default {
  name: 'App',
  components: {
    UploadFile
  },
  mounted() {
    const openCvScript = document.createElement('script')
    openCvScript.src = "./scripts/opencv.js"
    openCvScript.type = "text/javascript"
    document.head.appendChild(openCvScript)
  },
  computed: {
    cssProps() {
      return {
        '--background-color': '#121212',
        '--primary-color': '#BB86FC',
        '--secondary-color': '#1F1B24',
        '--tertiary-color': '#03DAC5'
      }
    }
  }
}
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@200;300;400;500;600;700&display=swap');

* {
  margin: 0;
  padding: 0;
  font-family: "Poppins", sans-serif;
}

#app {
  position: relative;
  min-height: 100vh;
  min-width: 100%;
  margin: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--background-color);
}

.btn {
  padding: 0 5px 0 5px;
}
</style>
