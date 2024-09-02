<template>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css" />
  <RouterView :fileBlob="fileBlob" />
</template>

<script>
import UploadFile from './components/UploadFile.vue'

export default {
  name: 'App',
  components: {
    UploadFile
  },
  data() {
    return { fileBlob: null }
  },
  mounted() {
    const openCvScript = document.createElement('script')
    openCvScript.src = "./scripts/opencv.js"
    openCvScript.type = "text/javascript"
    document.head.appendChild(openCvScript)
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
  background: #111;
}

.btn {
  padding: 0 5px 0 5px;
}
</style>
